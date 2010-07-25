# -*- coding: utf-8 -*-
import logging

from tipfy import (abort, app, get_config, HTTPException, import_string, local,
    request, RequestHandler, Response, Tipfy, url_for)
from tipfy.ext import i18n
from tipfy.ext import jinja2
from tipfy.ext import session
from tipfy.ext import auth
from tipfy.ext.auth import acl

from moe.base.models import Area


class UserMiddleware(object):
    """Middleware to load an area."""
    def pre_dispatch(self, handler):
        """Loads the current user and sets it as a handler property."""
        current_user = auth.get_current_user()

        handler.request.context.update({
            'current_user':     current_user,
            'login_url':        auth.create_login_url(request.url),
            'logout_url':       auth.create_logout_url('/'),
            'is_authenticated': auth.is_authenticated(),
        })

        setattr(handler, 'current_user', current_user)


class AreaRequestHandler(RequestHandler, jinja2.Jinja2Mixin, acl.AclMixin,
    session.MessagesMixin):
    """Base for all handlers."""

    middleware = [session.SessionMiddleware, i18n.I18nMiddleware,
        auth.AuthMiddleware, UserMiddleware]

    def __init__(self, app, request):
        self.app = app
        self.request = request

        area_name = self.get_area_name()
        if area_name not in ('docs', 'www'):
            # TODO instead of 404, redirect to a page to create the area,
            # if the are doesn't exist.
            # For now, only 404 is allowed.
            abort(404)

        self.area = Area.get_by_key_name(area_name)
        if self.area is None:
            self.area = Area.get_or_insert(key_name=area_name, name=area_name)

        # Get sitename from config or use host minus port as default
        # sitename.
        sitename = self.request.host.rsplit(':', 1)[0]

        # Add some common stuff to context.
        self.context = self.request.context = {
            'area':           self.area,
            'current_url':    self.request.url,
            'sitename':       get_config('moe', 'sitename', sitename),
            'analytics_code': get_config('moe', 'analytics_code', None),
            'dev':            get_config('tipfy', 'dev'),
            'apps_installed': get_config('tipfy', 'apps_installed'),
        }

    def render_response(self, filename, **values):
        # System messages.
        self.request.context['messages'] = self.messages

        return super(AreaRequestHandler, self).render_response(filename,
            **values)

    def set_form_error(self, body=None, title=None):
        """Adds a form error message.

        :param body:
            Message contents.
        :param title:
            Optional message title.
        :return:
            ``None``.
        """
        if body is None:
            body = i18n._('A problem occurred. Please correct the errors '
                'listed in the form.')

        if title is None:
            title = i18n._('Error')

        self.set_message('error', body, title=title, life=None)

    def get_area_name(self):
        if self.request.rule_args:
            name = self.request.rule_args.get('area_name', 'www')
        else:
            # For when no rule is set.
            #host = request.host.split(':', 1)[0]
            #domain = get_config('tipfy', 'server_name', '').split(':', 1)[0]
            #name = host[:-len(domain) - 1]
            name = 'www'

        return name

class ExceptionHandler(AreaRequestHandler):
    def get(self, exception=None, handler=None):
        logging.exception(exception)
        # Initial breadcrumbs for this app.
        self.request.context['breadcrumbs'] = [
            (url_for('home/index', area_name=self.area.name),
                i18n._('Home'))
        ]
        kwargs = {}
        code = 500
        template = 'base/error_500.html'

        if isinstance(exception, HTTPException):
            kwargs = {}
            code = exception.code
            if code in (404, 500):
                if exception.description != exception.__class__.description:
                    kwargs['message'] = exception.description

                template = 'base/error_%d.html' % code
            else:
                kwargs['message'] = exception.description

        response = self.render_response(template, **kwargs)
        response.status_code = code
        return response


class ExceptionMiddleware(object):
    def handle_exception(self, e, handler=None):
        if get_config('tipfy', 'dev'):
            # Always raise the exception in dev, so we can debug it.
            raise

        return ExceptionHandler(Tipfy.app, Tipfy.request).dispatch('get',
            exception=e)
