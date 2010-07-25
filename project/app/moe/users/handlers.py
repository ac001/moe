from google.appengine.api import users

from tipfy import RequestHandler, local, app, request, url_for, \
    get_config, redirect, redirect_to
from tipfy.ext.i18n import _, lazy_gettext, I18nMiddleware

from tipfy.ext.auth import get_auth_system, create_signup_url, \
    create_login_url, create_logout_url, get_current_user

from tipfy.ext.wtforms import Form, fields, validators

from moe.base.handlers import AreaRequestHandler


def get_signup_form(*args, **kwargs):
    form = SignupForm(request.form, **kwargs)
    return form, False


class SignupForm(Form):
    """Base signup form."""
    username = fields.TextField(lazy_gettext('Nickname'))
    email = fields.TextField(lazy_gettext('Email'))


class SignupHandler(AreaRequestHandler):
    """Performs signup after first login or creates a new account. The
    difference is that new accounts require a password and extenal auth not.
    """
    def get(self, **kwargs):
        if self.current_user is not None:
            # Don't allow existing users to access this page.
            return redirect(request.args.get('redirect', '/'))

        current_user = users.get_current_user()
        values = {}
        if current_user is not None:
            values['username'] = current_user.email().split('@')[0]
            values['email'] = current_user.email()

        form, use_password = get_signup_form(**values)

        context = {
            'form': form,
        }
        return self.render_response('users/signup.html', **context)

    def post(self, **kwargs):
        if self.current_user is not None:
            # Don't allow existing users to access this page.
            return redirect(request.args.get('redirect', '/'))

        user = None
        error = None

        form, use_password = get_signup_form()
        username = form.data['username']
        email = form.data['email']

        kwargs = {'email': email}

        if use_password:
            kwargs['password'] = request.form.get('password')
            if kwargs['password'] != request.form.get('confirm_password'):
                error = True
                self.messages.add_form_error(_("Passwords didn't match."))

        if error is None:
            kwargs['is_admin'] = False
            if use_password:
                # Own authentication.
                auth_id = 'own|%s' % username
            else:
                current_user = users.get_current_user()
                if current_user is not None:
                    # App Engine authentication.
                    auth_id = 'gae|%s' % current_user.user_id()
                    kwargs['is_admin'] = users.is_current_user_admin()
                else:
                    # OpenId, Oauth, Facebook, Twitter or FriendFeed.
                    raise NotImplementedError()

            user = get_auth_system().create_user(username, auth_id, **kwargs)

            if user is None:
                self.messages.add_form_error(_('Username already exists. '
                    'Please try a different one.'))

        if user is not None:
            redirect_url = request.args.get('redirect', '/')
            if use_password:
                return redirect(create_login_url(redirect_url))
            else:
                return redirect(redirect_url)
        else:
            context = {
                'form': form,
                'messages': self.messages,
            }

            return self.render_response('users/signup.html', **context)
