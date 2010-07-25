# -*- coding: utf-8 -*-
import re

from tipfy import get_config, cached_property

#: Default configuration values for this module. Keys are:
#: - ``protected_path``: Name of the path used for internal, non-wiki pages.
#:   Anything inside this path is not accepted as a valid wiki URL. Default is
#:   'pages'.
#: - ``start_page``: Name of the start page. Default is 'start'.
#: - ``max_path_depth``: Maximum number of path parts to be accepted in a URL.
#:   Default is 5.
default_config = {
    'protected_path': 'pages',
    'start_page':     'start',
    'max_path_depth': 5,
}


class WikiPath(object):
    """Helper to normalize and validate a wiki URL path and get path parts."""
    def __init__(self, path, endpoint=None):
        self.endpoint = endpoint
        if path:
            self._parts = [p for p in path.strip('/').split('/') if p.strip()]
            if self.max_path_depth:
                # Limit paths to the configured value.
                self._parts = self._parts[:self.max_path_depth]
        else:
            self._parts = []

    @cached_property
    def protected_path(self):
        return get_config(__name__, 'protected_path')

    @cached_property
    def start_page(self):
        return get_config(__name__, 'start_page') + '/'

    @cached_property
    def max_path_depth(self):
        return get_config(__name__, 'max_path_depth')

    @cached_property
    def path_parts(self):
        return [camel_to_dashes(part) for part in self._parts]

    @cached_property
    def normalized_path(self):
        return '/'.join(self.path_parts) + '/'

    @cached_property
    def page_name(self):
        if self._parts:
            return self.get_page_name(self._parts[-1])

    @cached_property
    def all_paths(self):
        all_paths = []
        path = ''
        for part in self.path_parts:
            path += part + '/'
            all_paths.append(path)

        return all_paths

    @cached_property
    def parent_paths(self):
        return self.all_paths[:-1]

    @cached_property
    def parent_path(self):
        if self.parent_paths:
            return self.parent_paths[-1]

    @cached_property
    def breadcrumbs(self):
        res = []

        if self.endpoint == 'wiki/index' and self.is_start_path():
            # Add all pages except the initial one in view mode.
            return res

        for path in self.all_paths:
            name = self.get_page_name(path.rstrip('/').rsplit('/', 1)[-1])
            res.append((path, name))

        return res

    def is_valid_path(self):
        """Checks if the path is using the protected path."""
        if self.path_parts and self.path_parts[0] == self.protected_path:
            return False

        return True

    def is_start_path(self):
        return (self.normalized_path == self.start_page)

    def get_page_name(self, normalized_path_part):
        return ' '.join(normalized_path_part.split('-')).title()


# inflection functions
def to_dashes(string):
    """Returns a string converted to use dashes with only lowercase
    alphanumerics.
    """
    string = re.sub('\s+', '-', string.strip().lower())
    string = re.sub('[^A-Za-z0-9-]', '', string)
    return re.sub('-+', '-', string).strip('-')


def to_under(string):
    """Returns a string converted to use dashes with only lowercase
    alphanumerics.
    """
    string = re.sub('\s+', '_', string.strip().lower())
    string = re.sub('[^A-Za-z0-9_]', '', string)
    return re.sub('_+', '_', string).strip('_')


def to_camel(string):
    """Converts a string to CamelCase using only alphanumerics: "foo bar",
    "foo-bar" or "foo_bar" are converted to "FooBar".
    """
    string = re.sub('[^A-Za-z0-9]', ' ', string).strip()
    return ''.join(part[0].upper() + part[1:] for part in string.split(' '))


def camel_to_dashes(string):
    """Converts "camelCapsWord" and "CamelCapsWord" to "camel-caps-word"."""
    string = re.sub('([a-z0-9])([A-Z])', '\\1-\\2', string).strip().lower()
    res = re.sub('-+', '-', string)
    return to_dashes(res)


def camel_to_under(string):
    """Converts "camelCapsWord" and "CamelCapsWord" to "camel_caps_word"."""
    string = re.sub('([a-z0-9])([A-Z])', '\\1_\\2', string).strip().lower()
    res = re.sub('_+', '_', string)
    return to_under(res)
