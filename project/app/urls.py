# -*- coding: utf-8 -*-
"""
    urls
    ~~~~

    URL definitions.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from tipfy import Rule, Submount, get_config, import_string


def get_rules():
    """Returns a list of URL rules for the application. The list can be
    defined entirely here or in separate ``urls.py`` files. Here we show an
    example of joining all rules from the ``apps_installed`` listed in
    config.
    """
    entry_points = get_config('tipfy', 'apps_entry_points')

    if get_config('moe', 'use_subdomain', False):
        kwargs = {'subdomain': '<area_name>'}
    else:
        kwargs = {'defaults': {'area_name': 'www'}}

    rules = [
        # This is a dummy rule pointing to wiki start page. Replace it by
        # one pointing to a homepage handler.
        Rule('/', endpoint='home/index', handler='moe.wiki.handlers.WikiViewHandler', **kwargs),
    ]

    for app_module in get_config('tipfy', 'apps_installed'):
        try:
            # Get the rules from each app installed and extend our rules.
            app_rules = import_string('%s.urls.get_rules' % app_module)()
            entry_point = entry_points.get(app_module)
            if entry_point:
                # Submount using the entry point.
                rules.append(Submount(entry_point, app_rules))
            else:
                # Just append the rules.
                rules.extend(app_rules)
        except ImportError:
            pass

    return rules
