# -*- coding: utf-8 -*-
"""
    config
    ~~~~~~

    Configuration settings.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE for more details.
"""
config = {}

# Configuration for the 'tipfy' module.
config['tipfy'] = {
    # Enable debugger. It will be loaded only in development.
    'middleware': [
        'tipfy.ext.debugger.DebuggerMiddleware',
    ],
    # Set the active apps.
    'apps_installed': [
        'moe.users',
        'moe.paste',
        'moe.wiki',
    ],
    # Set base paths for apps.
    'apps_entry_points': {
        'moe.paste': '/paste',
        'moe.wiki':  '/wiki',
    },
}

# Configuration for the 'tipfy.ext.session' module.
config['tipfy.ext.session'] = {
    # Important: set a random secret key for sessions!
    'secret_key': 'my secret key',
}

# Configuration for the 'moe' module.
config['moe'] = {
    'sitename':       'My Moe Site',
    'admin_email':    'me@my_moe_site.com',
    'analytics_code': None,
    'use_subdomain':  False,
}
