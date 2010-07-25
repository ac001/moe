# -*- coding: utf-8 -*-
"""
    moe.paste.models
    ~~~~~~~~~~~~~~~~

    Pastebin models.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from google.appengine.ext import db

from tipfy.ext.wtforms import Form, fields, validators

from tipfy import cached_property
from tipfy.ext.i18n import lazy_gettext, _

from moe.paste.highlighting import list_languages, get_language_name


class Paste(db.Model):
    # Creation date.
    created = db.DateTimeProperty(auto_now_add=True)
    # Modification date.
    updated = db.DateTimeProperty(auto_now=True)
    # Key to the area where this page is published.
    area_key = db.StringProperty()
    # Reference identifier to an authenticated user.
    user_key = db.StringProperty()
    # Original code.
    code_raw = db.TextProperty()
    # Highlighted code.
    code = db.TextProperty()
    # Language code.
    language = db.StringProperty()

    @cached_property
    def id(self):
        return self.key().id()

    @cached_property
    def lines(self):
        """Number of lines."""
        return len(self.code_raw.splitlines())

    @cached_property
    def language_name(self):
        return get_language_name(self.language)


class PasteForm(Form):
    code = fields.TextAreaField(lazy_gettext('Code'), validators=[
        validators.required()])
    language = fields.SelectField(lazy_gettext('Language'),
        choices=list_languages())
    insert_tab = fields.BooleanField(lazy_gettext('Activate tab key'))
