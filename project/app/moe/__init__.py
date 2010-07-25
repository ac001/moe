from tipfy import REQUIRED_VALUE

#: Default configuration values for this module. Keys are:
#: - ``sitename``: Name of the site, used by default in some places. Default
#:   is ``tipfy.REQUIRED_VALUE``.
#: - ``admin_email``: Administrator e-mail. Default is
#:   ``tipfy.REQUIRED_VALUE``.
#: - ``analytics_code``: Google Analytics code.
#: - `use_subdomain`: If `True`, loads app data based on current subdomain.
default_config = {
    'sitename':       REQUIRED_VALUE,
    'admin_email':    REQUIRED_VALUE,
    'analytics_code': None,
    'use_subdomain':  False,
    'menu_items_func': 'moe.base.handlers.get_menu_items',
}
