# -*- coding: utf-8 -*-
"""
    moe.paste.urls
    ~~~~~~~~~~~~~~

    URL definitions.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from tipfy import get_config, Rule


def get_rules():
    # Take the area name from the subdomain if they are in use. Otherwise
    # assume that this will be used in a single domain.
    if get_config('moe', 'use_subdomain', False):
        kwargs = {'subdomain': '<area_name>'}
    else:
        kwargs = {'defaults': {'area_name': 'www'}}

    rules = [
        Rule('/', endpoint='paste/index', handler='moe.paste.handlers.PasteNewHandler', **kwargs),
        Rule('/+<language>', endpoint='paste/index', handler='moe.paste.handlers.PasteNewHandler', **kwargs),
        Rule('/view/<int:paste_id>', endpoint='paste/view', handler='moe.paste.handlers.PasteViewHandler', **kwargs),
        Rule('/view-raw/<int:paste_id>', endpoint='paste/view-raw', handler='moe.paste.handlers.PasteViewRawHandler', **kwargs),
    ]

    return rules
