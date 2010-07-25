# -*- coding: utf-8 -*-
"""
    moe.wiki.urls
    ~~~~~~~~~~~~~

    URL definitions. All URLs:

        /wiki/
        /wiki/<path:page_path>

        /wiki/pages/

        /wiki/pages/changes/
        /wiki/pages/changes/<path:page_path>
        /wiki/pages/changes-feed/
        /wiki/pages/changes-feed/<path:page_path>

        /wiki/pages/diff/
        /wiki/pages/diff/<path:page_path>

        /wiki/pages/edit/
        /wiki/pages/edit/<path:page_path>

        /wiki/pages/list/
        /wiki/pages/list/<path:page_path>
        /wiki/pages/list-feed/
        /wiki/pages/list-feed/<path:page_path>

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from tipfy import Rule, Submount, get_config


def get_rules():
    # A protected path (by default '/pages') is used by everything related to
    # the wiki operation. Everything else is considered a wiki content page.
    protected_path = '/' + get_config('moe.wiki', 'protected_path')

    # Take the area name from the subdomain if they are in use. Otherwise
    # assume that this will be used in a single domain.
    if get_config('moe', 'use_subdomain', False):
        kwargs = {'subdomain': '<area_name>'}
    else:
        kwargs = {'defaults': {'area_name': 'www'}}

    rules = [
        # Initial page.
        Rule('/', endpoint='wiki/index', handler='moe.wiki.handlers.WikiViewHandler', **kwargs),
        Submount(protected_path, [
            # Base for the internal pages.
            Rule('/', endpoint='wiki/pages', handler='moe.wiki.handlers.WikiOverviewHandler', **kwargs),
            # Lists all pages.
            Rule('/list', endpoint='wiki/list', handler='moe.wiki.handlers.WikiPageListHandler', **kwargs),
            # Lists all child pages for a given page.
            Rule('/list/<path:page_path>', endpoint='wiki/list', handler='moe.wiki.handlers.WikiPageListHandler', **kwargs),
            # Lists all pages (Atom format).
            Rule('/list-atom', endpoint='wiki/list-atom', handler='moe.wiki.handlers.WikiPageListFeedHandler', **kwargs),
            # Lists all child pages for a given page (Atom format).
            Rule('/list-atom/<path:page_path>', endpoint='wiki/list-atom', handler='moe.wiki.handlers.WikiPageListFeedHandler', **kwargs),
            # Lists all changes.
            Rule('/changes', endpoint='wiki/changes', handler='moe.wiki.handlers.WikiChangesHandler', **kwargs),
            # Lists all changes for a given page.
            Rule('/changes/<path:page_path>', endpoint='wiki/changes', handler='moe.wiki.handlers.WikiPageChangesHandler', **kwargs),
            # Lists all changes (Atom format).
            Rule('/changes-atom', endpoint='wiki/changes-atom', handler='moe.wiki.handlers.WikiChangesFeedHandler', **kwargs),
            # Lists all changes for a given page (Atom format).
            Rule('/changes-atom/<path:page_path>', endpoint='wiki/changes-atom', handler='moe.wiki.handlers.WikiPageChangesFeedHandler', **kwargs),
            # Edition overview.
            Rule('/edit/', endpoint='wiki/edit', handler='moe.wiki.handlers.WikiEditOverviewHandler', **kwargs),
            # Edits a page.
            Rule('/edit/<path:page_path>', endpoint='wiki/edit', handler='moe.wiki.handlers.WikiEditHandler', **kwargs),
            # Diffs overview.
            Rule('/diff/', endpoint='wiki/diff', handler='moe.wiki.handlers.WikiDiffOverviewHandler', **kwargs),
            # Show diffs for a page revision.
            Rule('/diff/<path:page_path>', endpoint='wiki/diff', handler='moe.wiki.handlers.WikiDiffHandler', **kwargs),
            # Reparse all pages.
            # Rule('/reparse/', endpoint='wiki/reparse', handler='moe.wiki.handlers.WikiReparseHandler', **kwargs),
        ]),
        # A wiki page.
        Rule('/<path:page_path>', endpoint='wiki/index', handler='moe.wiki.handlers.WikiViewHandler', **kwargs),
    ]

    return rules
