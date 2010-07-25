# -*- coding: utf-8 -*-
import re

import creoleparser
import creoleparser.elements

import genshi
import genshi.core

import pygments
import pygments.lexers
import pygments.formatters

from werkzeug import url_quote

from tipfy import local, escape, url_for
from tipfy.ext.i18n import _
from tipfy.ext.db import _slugify

from moe.wiki import WikiPath


formatter = pygments.formatters.HtmlFormatter()
default_lexer = pygments.lexers.get_lexer_by_name('text')


class Heading(creoleparser.elements.Heading):
    def _build(self, mo, element_store, environ):
        heading_tag = self.tags[len(mo.group(1))-1]
        heading_text = mo.group(2)

        slug = _slugify(heading_text, default='heading')
        if environ is not None:
            headings = environ.setdefault('headings', [])
            i = 1
            original_slug = slug
            while True:
                if slug not in headings:
                    headings.append(slug)
                    break

                slug = '%s_%d' % (original_slug, i)
                i += 1

            toc = environ.setdefault('toc', [])
            toc.append((heading_tag, escape(heading_text), slug))

        # The heading itself.
        text = creoleparser.core.fragmentize(heading_text,
            self.child_elements, element_store, environ)
        # The anchor and link to the anchor.
        anchor = genshi.builder.tag.span(id=slug)
        anchor_link = genshi.builder.tag.a(genshi.core.Markup('&para;'),
            class_='headerlink', href='#' + slug,
            title=escape(_('Permalink to this headline')))

        heading = genshi.builder.tag.__getattr__(heading_tag)
        return heading([text, anchor, anchor_link], class_='heading')


def parse_macro(name, arg_string, body, isblock, environ):
    macro = MACROS.get(name, None)
    if not macro:
        return

    args, kwargs = creoleparser.parse_args(arg_string)
    return macro(name, arg_string, body, isblock, environ, *args, **kwargs)


def macro_code(name, arg_string, body, isblock, environ, *args, **kwargs):
    """A macro to allow syntax highlighting in wiki pages.

        <<code python>>
        def hello(who):
            print 'Hello, %s!' % who

        hello('World')
        <</code>>
    """
    if body is None:
        body = ''

    if len(args) > 0:
        language = args[0].strip()

        if language == 'pycon':
            lines = []
            for line in body.splitlines():
                if not line.startswith('>>>'):
                    line = '>>> ' + line.strip()

                lines.append(line)

            body = u'\n'.join(lines)

        try:
            lexer = pygments.lexers.get_lexer_by_name(language)
        except pygments.lexers.ClassNotFound:
            lexer = default_lexer
    else:
        lexer = default_lexer

    return genshi.core.Markup(pygments.highlight(body, lexer,
        formatter))


def macro_note(name, arg_string, body, isblock, environ, *args, **kwargs):
    """A macro to create notes and warnings.

        <<note>>
        I am a note.
        <</code>>

        <<warning>>
        I am a warning!
        <</warning>>
    """
    body = wiki_parser.parse(body)
    return genshi.Markup("""<div class="macro-note %s">
        <p class="title">%s:</p>
        %s
    </div>""" % (name, name.capitalize(), body))


def create_wiki_link(path):
    """Creates a wiki link given a path."""
    anchor = None
    parts = path.split('#', 1)
    if len(parts) > 1:
        path = parts[0]
        anchor = parts[1]

    page_path = WikiPath(path).normalized_path
    url = url_for('wiki/index', page_path=page_path, area_name=local.area.name)
    if anchor:
        url += '#' + url_quote(anchor)

    return url


def get_wiki_link_func(area):
    def create_wiki_link(path):
        """Creates a wiki link given a path."""
        anchor = None
        parts = path.split('#', 1)
        if len(parts) > 1:
            path = parts[0]
            anchor = parts[1]

        page_path = WikiPath(path).normalized_path
        url = url_for('wiki/index', page_path=page_path, area_name=area.name)
        if anchor:
            url += '#' + url_quote(anchor)

        return url

    return create_wiki_link


def get_page_sections(body, index=None):
    """Returns a section of the page."""
    sections = []
    section = ''
    for line in body.splitlines():
        res = heading_re.match(line)
        if res:
            #if index is not None and len(sections) == index:
            #    return section.strip()
            sections.append(section.strip())
            section = line + '\n'
        else:
            section += line + '\n'

    sections.append(section.strip())
    return sections


def heading_re_string():
    token = '='
    tags = ['h1','h2','h3','h4','h5','h6']
    whitespace = r'[ \t]*'
    tokens = '(' + re.escape(token) + '{1,' + str(len(tags)) +'})'
    content = '(.*?)'
    trailing_markup = '(' + re.escape(token) + r'+[ \t]*)?(\n|\Z)'
    return '^' + whitespace + tokens + \
           whitespace + content + whitespace + trailing_markup


def get_toc(data):
    """A very rudimentar TOC creator. No nested lists. Simple."""
    if len(data) <= 1:
        return ''

    res = u'<ul class="toc">'
    for level, title, anchor in data:
        res += u'<li class="toc-%s"><a href="#%s">%s</a></li>' % (level,
            anchor, escape(title))

    return res + u'</ul>'


def parse_page(body_raw, environ, area):
    # Factory link creation function to use current area.
    wiki_parser.dialect.link.path_func = get_wiki_link_func(area)

    # Parse wiki markup.
    body = wiki_parser(body_raw, environ=environ)
    toc = get_toc(environ.get('toc'))
    return (body, toc)


heading_re = re.compile(heading_re_string(), re.MULTILINE)

dialect = creoleparser.create_dialect(
    creoleparser.dialects.creole11_base,
    #wiki_links_path_func=create_wiki_link,
    macro_func=parse_macro,
)
dialect.headings = Heading(['h1','h2','h3','h4','h5','h6'], '=')
wiki_parser = creoleparser.Parser(dialect=dialect, encoding=None)

MACROS = {
    'code':    macro_code,
    'note':    macro_note,
    'warning': macro_note,
    'seealso': macro_note,
}
