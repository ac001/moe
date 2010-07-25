# -*- coding: utf-8 -*-
"""
    moe.wiki.model
    ~~~~~~~~~~~~~~

    Models for wiki pages and revisions.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import datetime

from google.appengine.ext import db

from tipfy.ext.wtforms import Form, fields, validators

from tipfy import cached_property
from tipfy.ext.db import PickleProperty, get_property_dict, populate_entity
from tipfy.ext.i18n import lazy_gettext, _
from tipfy.ext.auth.model import User


class WikiRevision(db.Model):
    """Stores content for wiki pages. The latest version is always a root
    entity and past versions have the latest version as ancestor.
    """
    # Creation date.
    created = db.DateTimeProperty()
    # Modification date.
    updated = db.DateTimeProperty()
    # Creator of this page: a reference identifier to an authenticated user.
    author_key = db.StringProperty()
    # Editor of this version: a reference identifier to an authenticated user.
    editor_key = db.StringProperty()
    # IP address of the editor or author.
    editor_ip = db.StringProperty()
    # Page title.
    title = db.StringProperty()
    # Body formatted message.
    body = db.TextProperty()
    # Body raw message, as posted by the user. Only displayed when editing.
    body_raw = db.TextProperty()
    # Format name: defines a markup processor such as Creole or Markdown.
    format = db.StringProperty(required=True, default='creole')
    # Generated HTML with table of contents: lists all headings in the page.
    toc = db.TextProperty()
    # Change notes, set when the node is updated.
    notes = db.StringProperty()

    @cached_property
    def id(self):
        return self.version.lower()

    @cached_property
    def author(self):
        if self.author_key:
            return User.get(db.Key(self.author_key))

    @cached_property
    def editor(self):
        if self.editor_key:
            return User.get(db.Key(self.editor_key))

    @cached_property
    def version(self):
        """Returns the current version id. Latest versions always have a key
        name, while older versions have a key id.
        """
        id = self.key().id()
        if id is None:
            return _('Latest')
        else:
            return str(id)

    def populate(self, **kwargs):
        """Sets a batch of property values for this entity."""
        populate_entity(self, **kwargs)

    @classmethod
    def update(cls, area, path, **kwargs):
        """Creates or updates a revision transactionally. By default, stores
        the existing entity as a new entity with the current entity as parent.
        """
        key_name = cls.get_key_name(area, path)
        entities = []

        now = datetime.datetime.now()
        kwargs['created'] = now
        kwargs['updated'] = now

        def txn():
            entity = cls.get_by_key_name(key_name)

            if entity:
                # Create a new entity for the revision history.
                old = cls(parent=entity, **get_property_dict(entity))
                # Populate old entity with new values.
                entity.populate(**kwargs)
                # Save both entities.
                db.put([entity, old])
            else:
                # This is a new page, so author and editor are the same.
                kwargs.setdefault('author_key', kwargs.get('editor_key'))
                entity = cls(key_name=key_name, **kwargs)
                entity.put()

            return entity

        return db.run_in_transaction(txn)

    @classmethod
    def get_key(cls, area, path, version=None):
        path = (cls.kind(), cls.get_key_name(area, path))
        if version is not None:
            # This is not the latest revision.
            path += (cls.kind(), version)

        return db.Key.from_path(*path)

    @classmethod
    def get_key_name(cls, area, path):
        return WikiPage.get_key_name(area, path)

    @classmethod
    def get_revision(cls, area, path, version=None):
        return cls.get(cls.get_key(area, path, version))

    @classmethod
    def get_latest_revisions(cls, area, path, limit=2):
        # Latest 2 revisions.
        res = cls.all().ancestor(cls.get_key(area, path)) \
                       .order('-updated') \
                       .fetch(limit)

        return res or []


class WikiPage(db.Model):
    # Creation date.
    created = db.DateTimeProperty(auto_now_add=True)
    # Modification date.
    updated = db.DateTimeProperty(auto_now=True)
    # Key to the area where this page is published.
    area_key = db.StringProperty()
    # The URL path to the page.
    path = db.StringProperty()
    # Direct parent path.
    parent_path = db.StringProperty()
    # Paths to all parents of this page.
    parent_paths = db.StringListProperty()
    # Tags.
    tags = db.StringListProperty()
    # Dependencies.
    deps = PickleProperty()

    @classmethod
    def update(cls, area, path, **kwargs):
        """Creates or updates a page."""
        kwargs['area_key'] = str(area.key())
        kwargs['path'] = path
        page = cls(key_name=cls.get_key_name(area, path), **kwargs)
        page.put()
        return page

    @classmethod
    def get_key_name(cls, area, path):
        return '%s:%s' % (str(area.key()), path)

    @classmethod
    def get_page(cls, area, path):
        return cls.get_by_key_name(cls.get_key_name(area, path))

    @classmethod
    def get_revision(cls, area, path, version=None):
        """Returns a revision for a given area, page and version.

        This is mostly a proxy for WikiRevision for now, but this may change.
        """
        return WikiRevision.get_revision(area, path, version)

    @cached_property
    def latest_revision(self):
        # Latest revision entity.
        return WikiRevision.get_by_key_name(self.key().name())

    @cached_property
    def latest_revision_key(self):
        # Latest revision key.
        return db.Key.from_path('WikiRevision', self.key().name())

    def populate(self, **kwargs):
        """Sets a batch of property values for this entity."""
        populate_entity(self, **kwargs)


class WikiToc(db.Model):
    # Creation date.
    created = db.DateTimeProperty(auto_now_add=True)
    # Modification date.
    updated = db.DateTimeProperty(auto_now=True)
    # Key to the area where this page is published.
    area_key = db.StringProperty()
    # The URL path to the page.
    path = db.StringProperty()
    # Formatted toc contents.
    body = db.TextProperty()
    # Original toc contents.
    body_raw = db.TextProperty()


class WikiRevisionForm(Form):
    title = fields.TextField(lazy_gettext('Title'),
        validators=[validators.required()])
    body = fields.TextAreaField(lazy_gettext('Content'))
    note = fields.TextField(lazy_gettext('Change note'))


def wiki_revisions_pager(revision, cursor=None, limit=20):
    def get_query(keys_only=False, cursor=None):
        return WikiRevision.all(keys_only=keys_only, cursor=cursor) \
                           .ancestor(revision) \
                           .order('-updated')

    query = get_query(cursor=cursor)
    entities = query.fetch(limit)
    query_cursor = None

    if entities:
        query_cursor = query.cursor()

        # Check if we have "next" results.
        res = get_query(keys_only=True, cursor=query_cursor).get()
        if res is None:
            query_cursor = None

    return entities, query_cursor


def wiki_changes_pager(area, cursor=None, limit=20):
    def get_query(keys_only=False, cursor=None):
        return WikiPage.all(keys_only=keys_only, cursor=cursor) \
                       .filter('area_key', str(area.key())) \
                       .order('-updated')

    query = get_query(cursor=cursor)
    entities = query.fetch(limit)

    if not entities:
        query_cursor = None
    else:
        query_cursor = query.cursor()

        # Check if we have "next" results.
        res = get_query(keys_only=True, cursor=query_cursor).get()
        if res is None:
            query_cursor = None

    return entities, query_cursor


def wiki_list_pager(area, parent_path=None, cursor=None, limit=20):
    def get_query(keys_only=False, cursor=None):
        query = WikiPage.all(keys_only=keys_only) \
                        .filter('area_key', str(area.key())) \
                        .filter('parent_path', parent_path) \
                        .order('path')

        if cursor is not None:
            query.with_cursor(cursor)

        return query

    query = get_query(cursor=cursor)
    entities = query.fetch(limit)

    if not entities:
        query_cursor = None
    else:
        query_cursor = query.cursor()

        # Check if we have "next" results.
        res = get_query(keys_only=True, cursor=query_cursor).get()
        if res is None:
            query_cursor = None

    return entities, query_cursor
