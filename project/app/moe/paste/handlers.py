# -*- coding: utf-8 -*-
"""
    moe.paste.handlers
    ~~~~~~~~~~~~~~~~~~

    Handlers for a really simple pastebin.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from tipfy import NotFound, request, Response, url_for, redirect_to
from tipfy.ext.i18n import _

from moe.base.handlers import AreaRequestHandler

from moe.paste.models import Paste, PasteForm
from moe.paste.highlighting import highlight


class PasteBaseHandler(AreaRequestHandler):
    """Base class for the pastebin."""
    def __init__(self, app, request):
        AreaRequestHandler.__init__(self, app, request)

        # Set a flag in context for menus.
        self.request.context['current_app'] = 'paste'

        # Initialize list of breadcrumbs.
        self.breadcrumbs = []

    def get_breadcrumb(self, endpoint, text, **kwargs):
        return (url_for(endpoint, area_name=self.area.name, **kwargs),
            text)

    def add_breadcrumb(self, endpoint, text, **kwargs):
        self.breadcrumbs.append(self.get_breadcrumb(endpoint, text, **kwargs))

    def render_response(self, filename, **values):
        self.request.context['breadcrumbs'] = [
            self.get_breadcrumb('home/index', _('Home')),
            self.get_breadcrumb('paste/index', _('Paste'))] + self.breadcrumbs

        return super(PasteBaseHandler, self).render_response(filename, **values)


class PasteNewHandler(PasteBaseHandler):
    """Displays a paste form and saves a new paste."""
    form = None

    def get(self, **kwargs):
        context = {
            'form': self.form or PasteForm(language=kwargs.pop('language',
                'python')),
        }
        return self.render_response('paste/new.html', **context)

    def post(self, **kwargs):
        self.form = PasteForm(request.form)

        if self.form.validate():
            if self.current_user:
                user_key = str(self.current_user.key())
            else:
                user_key = None

            language_code = request.form.get('language')
            code_raw = request.form.get('code', u'')
            code = highlight(code_raw, language_code)

            values = {
                'area_key': str(self.area.key()),
                'user_key': user_key,
                'code_raw': code_raw,
                'code':     code,
                'language': language_code,
            }
            paste = Paste(**values)
            paste.put()
            self.set_message('success', _('The paste was saved.'), flash=True)

            return redirect_to('paste/view', paste_id=paste.id,
                area_name=self.area.name)
        else:
            self.set_form_error(_('Ooops, code is empty! Please post '
                'some lines.'))
            return self.get()


class PasteViewHandler(PasteBaseHandler):
    """Displays a paste."""
    def get(self, **kwargs):
        paste_id = kwargs.pop('paste_id', None)
        if not paste_id:
            raise NotFound()

        paste = Paste.get_by_id(paste_id)
        if not paste:
            raise NotFound()

        self.add_breadcrumb('paste/view',
            _('Paste #%(paste_id)s', paste_id=paste.id),
            paste_id=paste.id)
        form = PasteForm(code=paste.code_raw, language=paste.language)

        context = {
            'paste': paste,
            'form': form,
        }
        return self.render_response('paste/view.html', **context)



class PasteViewRawHandler(PasteBaseHandler):
    """Displays a paste in raw mode, as text."""
    def get(self, **kwargs):
        paste_id = kwargs.pop('paste_id', None)
        if not paste_id:
            raise NotFound()

        paste = Paste.get_by_id(paste_id)
        if not paste:
            raise NotFound()

        return Response(paste.code_raw)


class PasteListHandler(PasteBaseHandler):
    """Not implemented."""
    def get(self, **kwargs):
        context = {
        }
        return self.render_response('paste/new.html', **context)
