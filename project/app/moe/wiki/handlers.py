# -*- coding: utf-8 -*-
"""
    moe.wiki.handler
    ~~~~~~~~~~~~~~~~

    Wiki application.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import difflib

import diff_match_patch

from werkzeug import escape, url_quote_plus
from werkzeug.contrib.atom import AtomFeed

from tipfy import (abort, get_config, escape, redirect, redirect_to, url_for)
from tipfy.ext.i18n import _, ngettext
from tipfy.ext.auth import user_required, get_current_user
from tipfy.ext.db import _slugify

from moe.base.handlers import AreaRequestHandler
from moe.wiki import WikiPath
from moe.wiki.models import (WikiPage, wiki_list_pager, WikiRevision,
    WikiRevisionForm, wiki_changes_pager, wiki_list_pager,
    wiki_revisions_pager)
from moe.wiki.parser import get_page_sections, parse_page


class WikiMiddleware(object):
    """Before processing a request, checks if the requested wiki path is
    valid and returns an error if not, or normalizes and redirects to the
    normalized URL if needed.
    """
    def pre_dispatch(self, handler):
        if handler.wiki_path:
            if handler._raw_path != handler._normalized_path:
                # Path is not normalized. Redirect.
                url = handler.request.path[:-len(handler._raw_path)] + \
                    handler._normalized_path
                return redirect(url)

            if not handler.wiki_path.is_valid_path():
                # Path is invalid.
                abort(404, _('This address is not valid.'))


class WikiBaseHandler(AreaRequestHandler):
    middleware = [WikiMiddleware] + AreaRequestHandler.middleware

    #: A WikiPath instance if the URL rule has `page_path`, or `None`.
    wiki_path = _raw_path = _normalized_path = None

    def __init__(self, app, request):
        """Base handler for all home pages."""
        AreaRequestHandler.__init__(self, app, request)

        page_path = self.request.rule_args.get('page_path', None)
        endpoint = self.request.rule.endpoint
        if page_path or endpoint in ('wiki/index', 'home/index'):
            if not page_path:
                # The default start page name. Must end with a slash,
                # like all pages.
                page_path = get_config('moe.wiki', 'start_page') + '/'

            # Normalize and validate page and path.
            self.wiki_path = WikiPath(page_path, endpoint)
            self._raw_path = page_path
            self._normalized_path = self.wiki_path.normalized_path

        # Add some common stuff to context.
        self.request.context.update({
            # Set a flag in context for menus.
            'current_app':      'wiki',
            'current_endpoint': endpoint,
        })

    def set_breadcrumbs(self, page=None):
        """Sets a list of urls and page names to build a breadcrumbs navbar."""
        # Common values for all rules.
        kwargs = {}
        # Default endpoint for page paths.
        endpoint = 'wiki/index'

        # Initial breadcrumbs for this app.
        self.breadcrumbs = []
        self.add_breadcrumb('home/index', _('Home'))
        self.add_breadcrumb('wiki/index', _('Wiki'))

        if self.wiki_path:
            kwargs['page_path'] = self.wiki_path.normalized_path

        if page == 'view':
            # home -> wiki -> ...page path...
            self.add_path_breadcrumb('wiki/index')
        elif page == 'edit':
            # Edit
            # home -> wiki -> ...page path... -> edit
            self.add_path_breadcrumb('wiki/index')
            self.add_breadcrumb('wiki/edit', _('Edit'), **kwargs)
        elif page in ('changes', 'diff'):
            # Changes & Diff
            # home -> wiki -> history
            # home -> wiki -> history -> diff
            # home -> wiki -> ...page path... -> history -> diff
            self.add_path_breadcrumb('wiki/index')
            self.add_breadcrumb('wiki/changes', _('History'), **kwargs)
            if page == 'diff':
                self.add_breadcrumb('wiki/diff', _('Diff'), **kwargs)
        elif page == 'list':
            # Page lists
            # home -> wiki -> all pages
            # home -> wiki -> all pages -> ...page path...
            self.add_breadcrumb('wiki/list', _('All Pages'))
            self.add_path_breadcrumb('wiki/list')
        elif page == 'pages':
            # Internal page namespace.
            # home -> wiki -> pages
            self.add_breadcrumb('wiki/pages', _('Overview'))

        self.request.context['breadcrumbs'] = self.breadcrumbs

    def add_breadcrumb(self, endpoint, text, **kwargs):
        self.breadcrumbs.append((url_for(endpoint, area_name=self.area.name,
            **kwargs), text))

    def add_path_breadcrumb(self, endpoint, **kwargs):
        if not self.wiki_path:
            return

        for path, name in self.wiki_path.breadcrumbs:
            kwargs['page_path'] = path
            self.add_breadcrumb(endpoint, name, **kwargs)


class WikiViewHandler(WikiBaseHandler):
    """Displays a wiki page."""
    def get(self, **kwargs):
        page_name = self.wiki_path.page_name
        page_path = self.wiki_path.normalized_path
        version = self.request.args.get('version', None, type=int)

        revision = WikiPage.get_revision(self.area, page_path, version)

        if version and not revision:
            # Bad request.
            abort(404)

        self.set_breadcrumbs(page='view')
        if version:
            text = _('Version %(version)s', version=version)
            self.add_breadcrumb('wiki/index', text, page_path=page_path,
                version=version)

        context = {
            'page_name': page_name,
            'page_path': page_path,
            'revision':  revision,
            'version':   version,
        }

        if revision:
            context.update({
                'slug': _slugify(revision.title, default='heading'),
                'title_quoted': url_quote_plus(revision.title),
                'current_url_quoted': url_quote_plus(self.request.url),
            })

        return self.render_response('wiki/page_view.html', **context)


class WikiOverviewHandler(WikiBaseHandler):
    """Displays an overview of the wiki."""
    def get(self, **kwargs):

        self.set_breadcrumbs(page='pages')
        context = {
        }
        return self.render_response('wiki/overview.html', **context)


class WikiPageListHandler(WikiBaseHandler):
    """Displays a list with all content pages."""
    def get_context(self):
        if self.wiki_path:
            page_name = self.wiki_path.page_name
            page_path = self.wiki_path.normalized_path
            revision = WikiPage.get_revision(self.area, page_path)
            if not revision:
                abort(404)
        else:
            page_name = page_path = revision = None

        curr_cursor = self.request.args.get('start')
        pages, cursor = wiki_list_pager(self.area, parent_path=page_path,
            cursor=curr_cursor)

        return {
            'page_name':     page_name,
            'page_path':     page_path,
            'revision':      revision,
            'pages':         pages,
            'is_first_page': curr_cursor is None,
            'next_page':     cursor,
        }

    def get(self, **kwargs):
        self.set_breadcrumbs(page='list')
        return self.render_response('wiki/page_list.html',
            **self.get_context())


class WikiPageListFeedHandler(WikiPageListHandler):
    """Displays a list with all content pages (Atom format)."""
    def get(self, **kwargs):
        """TODO: cache."""
        context = self.get_context()

        url_kwargs = {'area_name': self.area.name}

        if context.get('page_path'):
            page_title = _('All pages in %(page_name)s',
                page_name=escape(context.get('page_name')))
            url_kwargs['page_path'] = context.get('page_path')
        else:
            page_title = _('All Pages')

        sitename = get_config('moe', 'sitename')
        page_title += ' - ' + sitename
        url = url_for('wiki/list', full=True, **url_kwargs)
        generator = (sitename, None, None)
        feed = AtomFeed(page_title, feed_url=self.request.url, url=url,
                        generator=generator)

        for page in context.get('pages'):
            revision = page.latest_revision
            feed.add(revision.title, unicode(revision.body),
                     content_type='html',
                     author=revision.editor.username,
                     url=url_for('wiki/index', area_name=self.area.name,
                                 page_path=page.path),
                     updated=revision.updated,
                     published=revision.created,
                     xml_base=self.request.url_root)

        return feed.get_response()


class WikiChangesHandler(WikiBaseHandler):
    """Displays lists of recent changes in the whole wiki."""
    def get(self, **kwargs):
        self.set_breadcrumbs(page='changes')

        curr_cursor = self.request.args.get('start')
        entities, cursor = wiki_changes_pager(self.area, cursor=curr_cursor)

        context = {
            'pages': entities,
            'is_first_page': curr_cursor is None,
            'next_page': cursor,
        }
        return self.render_response('wiki/latest_changes.html', **context)


class WikiChangesFeedHandler(WikiBaseHandler):
    """Displays lists of recent changes in the whole wiki."""
    def get(self, **kwargs):
        curr_cursor = self.request.args.get('start')
        pages, cursor = wiki_changes_pager(self.area, cursor=curr_cursor)
        if pages is None:
            pages = []

        sitename = get_config('moe', 'sitename')
        page_title = _('Latest Changes')
        page_title += ' - ' + sitename
        url = url_for('wiki/changes', full=True, area_name=self.area.name)
        generator = (sitename, None, None)

        feed = AtomFeed(page_title, feed_url=self.request.url, url=url,
                        generator=generator)

        for page in pages:
            revision = page.latest_revision
            feed.add(revision.title, unicode(revision.body),
                     content_type='html',
                     author=revision.editor.username,
                     url=url_for('wiki/index', area_name=self.area.name,
                         page_path=page.path),
                     updated=revision.updated,
                     published=revision.created,
                     xml_base=self.request.url_root)

        return feed.get_response()


class WikiPageChangesHandler(WikiBaseHandler):
    """Displays lists of recent changes for a given page."""
    def get_context(self):
        page_name = self.wiki_path.page_name
        page_path = self.wiki_path.normalized_path

        wiki_page = WikiPage.get_page(self.area, page_path)
        if not wiki_page:
            abort(404)

        revision = wiki_page.latest_revision
        if not revision:
            abort(404)

        curr_cursor = self.request.args.get('start')
        revisions, cursor = wiki_revisions_pager(revision, cursor=curr_cursor)

        return {
            'page_name':     page_name,
            'page_path':     page_path,
            'revisions':     revisions,
            'revision':      revision,
            'is_first_page': curr_cursor is None,
            'next_page':     cursor,
        }

    def get(self, **kwargs):
        self.set_breadcrumbs(page='changes')
        return self.render_response('wiki/page_changes.html',
            **self.get_context())

    def post(self, **kwargs):
        """Just redirect to the diff page passing the requested versions."""
        return redirect_to('wiki/diff', version1=self.request.form.get('version1'),
            version2=self.request.form.get('version2'), **kwargs)


class WikiPageChangesFeedHandler(WikiPageChangesHandler):
    """Displays lists of recent changes for a given page."""
    def get(self, **kwargs):
        context = self.get_context()

        url_kwargs = {
            'area_name': self.area.name,
            'page_path': context.get('page_path'),
        }

        sitename = get_config('moe', 'sitename')
        page_title = _('History for %(page_name)s', page_name= escape(
            context.get('revision').title))
        page_title += ' - ' + sitename
        url = url_for('wiki/changes', full=True, **url_kwargs)
        generator = (sitename, None, None)

        feed = AtomFeed(page_title, feed_url=self.request.url, url=url,
                        generator=generator)

        for revision in context.get('revisions'):
            feed.add(revision.title, unicode(revision.body),
                     content_type='html',
                     author=revision.editor.username,
                     url=url_for('wiki/index', version=revision.version.lower(),
                         **url_kwargs),
                     updated=revision.updated,
                     published=revision.created,
                     xml_base=self.request.url_root)

        return feed.get_response()


class WikiDiffHandler(WikiBaseHandler):
    """Displays a page diff."""
    def get_normalized_version(self, key):
        version = self.request.args.get(key)
        if version is None or version == 'latest':
            return None

        try:
            return int(version)
        except ValueError:
            abort(400, _('Please provide a valid version number.'))

    def get(self, **kwargs):
        page_name = self.wiki_path.page_name
        page_path = self.wiki_path.normalized_path

        rev1 = rev2 = None
        version1 = self.get_normalized_version('version1')
        version2 = self.get_normalized_version('version2')

        if version1 is None and version2 is None:
            # Show diff between 2 latest revisions.
            revs = WikiRevision.get_latest_revisions(self.area, page_path)
            if len(revs) == 2:
                rev2, rev1 = revs
        elif version1 is None or version2 is None:
            # Show diff between given revision and current one.
            version = version1 or version2
            rev1 = WikiRevision.get_revision(self.area, page_path)
            rev2 = WikiRevision.get_revision(self.area, page_path, version)
        else:
            # Show diff between two given revisions.
            rev1 = WikiRevision.get_revision(self.area, page_path, version1)
            rev2 = WikiRevision.get_revision(self.area, page_path, version2)

        if not rev1 or not rev2:
            abort(404)

        if rev1.updated < rev2.updated:
            # Always make the most updated revision the first.
            r1 = rev1
            rev1 = rev2
            rev2 = r1

        if rev1.id == 'latest':
            tofile = _('latest revision')
        else:
            tofile = _('revision %s') % rev1.id

        if rev2.id == 'latest':
            fromfile = _('latest revision')
        else:
            fromfile = _('revision %s') % rev2.id

        fromlines = rev2.body_raw.splitlines()
        tolines = rev1.body_raw.splitlines()

        fromdate = None
        todate = None

        """
        diff = self.get_unified_diff(fromlines, tolines, fromfile, tofile,
            fromdate, todate, numlines=5)
        """

        diff = self.get_table_diff(fromlines, tolines, fromfile, tofile)

        self.set_breadcrumbs(page='diff')
        context = {
            'page_name': page_name,
            'page_path': page_path,
            'revision1': rev1,
            'revision2': rev2,
            'diff':      diff,
        }
        return self.render_response('wiki/page_diff.html', **context)

    def get_context_diff(self, fromlines, tolines, fromfile, tofile,
        fromdate, todate, numlines=5):

        diff_gen = difflib.context_diff(fromlines, tolines, fromfile, tofile,
            fromdate, todate, n=numlines)

    def get_table_diff(self, fromlines, tolines, fromfile, tofile, numlines=5):
        diff = difflib.HtmlDiff().make_table(fromlines, tolines, fromfile,
            tofile, context=True, numlines=numlines)

        diff = diff.replace(' nowrap="nowrap"', '')
        diff = diff.replace('<th colspan="2" class="diff_header">', '<th colspan="2" class="diff_foo">')
        diff = diff.replace('&nbsp;', ' ')
        return diff

    def get_unified_diff(self, fromlines, tolines, fromfile, tofile,
        fromdate, todate, numlines=5):

        diff_gen = difflib.unified_diff(fromlines, tolines, fromfile, tofile,
            fromdate, todate, n=numlines)

        diff = ''
        for line in diff_gen:
            line = escape(line)
            if line.startswith('+'):
                diff += '<p class="diff_add"><pre>%s</pre></p>' % line
            elif line.startswith('-'):
                diff += '<p class="diff_sub"><pre>%s</pre></p>' % line
            else:
                diff += '<p class="diff_what"><pre>%s</pre></p>' % line

        return diff

    def get_diff_match_patch(self):
        dmp = diff_match_patch.diff_match_patch()
        diffs = dmp.diff_main(rev2.body_raw, rev1.body_raw)
        dmp.diff_cleanupSemantic(diffs)
        diff = dmp.diff_prettyHtml(diffs)

        return diff


class WikiEditHandler(WikiBaseHandler):
    """Displays and handles a form to edit or create wiki pages."""
    form = None

    @user_required
    def get(self, **kwargs):
        page_path = self.wiki_path.normalized_path
        version = self.request.args.get('version', None, type=int)
        revision = WikiPage.get_revision(self.area, page_path, version)
        if revision:
            section = self.request.args.get('section', None, type=int)
            if section is not None:
                # Edit only part of the page, starting at a heading.
                sections = get_page_sections(revision.body_raw)
                try:
                    body = sections[section]
                except IndexError, e:
                    abort(404, _('Invalid page section.'))
            else:
                body = revision.body_raw

            data = {'title': revision.title, 'body': body}
        else:
            data = {
                'title': self.wiki_path.page_name,
                'note': _('Page created')
            }

        self.form = WikiRevisionForm(**data)
        return self._render_response()

    @user_required
    def post(self, **kwargs):
        page_path = self.wiki_path.normalized_path
        parent_path = self.wiki_path.parent_path
        parent_paths = self.wiki_path.parent_paths

        self.form = form = WikiRevisionForm(self.request.form)

        version = self.request.args.get('version', None, type=int)
        section = self.request.args.get('section', None, type=int)

        if form.validate():
            # Get user.
            editor_key = str(get_current_user().key())
            # Get title.
            title = form.title.data.strip()
            # Get body.
            body_raw = form.body.data.strip()
            # Get page note.
            note = form.note.data.strip()
            # Get the revision being editted.
            revision = WikiPage.get_revision(self.area, page_path,
                version)

            if body_raw or section is not None:
                slug = _slugify(title, default=u'heading')
                environ = {
                    'headings': [slug],
                    'toc':      [('h1', escape(title), slug)],
                }

                if section is not None:
                    # Only part of the body was submitted.
                    if revision:
                        sections = get_page_sections(revision.body_raw)
                    else:
                        sections = ['']

                    try:
                        sections.pop(section)
                        sections.insert(section, body_raw)
                        body_raw = u'\n\n'.join(sections)
                    except IndexError, e:
                        abort(404, _('Invalid page section.'))

                try:
                    body, toc = parse_page(body_raw, environ, self.area)
                except:
                    # Probably syntax errors. Render the form again.
                    self.set_message('error', _("Ooops. There are syntax "
                        "errors in the page you submitted. Please verify "
                        "if you didn't forget to close any tags."),
                        title=_('Error'))
                    return self._render_response()
            else:
                # Don't parse anything.
                body, toc = '', ''

            if revision is not None and (revision.body_raw == body_raw) and \
                (revision.title == title):
                # Nothing changed.
                return self.success(_('Nothing changed.'), environ, page_path,
                    section)

            # Values for the revision.
            rev_values = {
                'editor_key': editor_key,
                'editor_ip':  self.request.remote_addr,
                'title':      title,
                'body_raw':   body_raw,
                'body':       body,
                'toc':        toc,
                'notes':      note,
                'format':     'creole',
            }

            # Values for the page.
            page_values = {
                'parent_path': parent_path,
                'parent_paths': parent_paths,
            }

            try:
                # Create or update page and revision.
                WikiRevision.update(self.area, page_path, **rev_values)
                WikiPage.update(self.area, page_path, **page_values)
                return self.success(_('Page saved.'), environ, page_path,
                    section)
            except:
                self.set_message('error', _('Ooops. A problem occurred '
                    'trying to save the page. Please make a backup of your '
                    'changes and try again.'), title=_('Error'))
                return self._render_response()

        # Form failed. Render the form again.
        self.set_form_error()
        return self._render_response()

    def success(self, message, environ, page_path, section):
        # Success. Redirect to the saved page.
        self.set_message('success', message, flash=True)

        anchor = None
        if section is not None:
            try:
                # Add an anchor.
                anchor = environ.get('toc')[section][2]
            except IndexError:
                # Section was removed, so don't use anchor.
                pass

        return redirect_to('wiki/index', area_name=self.area.name,
            page_path=page_path, _anchor=anchor)

    def _render_response(self):
        self.set_breadcrumbs(page='edit')

        context = {
            'page_name': self.wiki_path.page_name,
            'page_path': self.wiki_path.normalized_path,
            'form':      self.form,
        }
        return self.render_response('wiki/page_edit.html', **context)


class WikiEditOverviewHandler(WikiBaseHandler):
    def get(self, **kwargs):
        self.set_breadcrumbs(page='edit')
        return self.render_response('wiki/overview_edit.html')


class WikiDiffOverviewHandler(WikiBaseHandler):
    def get(self, **kwargs):
        self.set_breadcrumbs(page='diff')
        return self.render_response('wiki/overview_diff.html')


class WikiReparseHandler(WikiBaseHandler):
    """Reparse all pages."""
    def get(self, **kwargs):
        return self.post(**kwargs)

    def post(self, **kwargs):
        cursor = self.request.form.get('cursor')
        query = WikiRevision.all().order('updated')
        if cursor is not None:
            query.with_cursor(cursor)

        entities = query.fetch(5)
        if entities:
            import google.appengine.api.labs.taskqueue

            # Reparse all.
            for entity in entities:
                slug = _slugify(entity.title, default=u'heading')
                environ = {
                    'headings': [slug],
                    'toc':      [('h1', escape(entity.title), slug)],
                }
                body, toc = parse_page(entity.body_raw, environ, self.area)
                entity.body = body
                entity.toc = toc
                entity.save()

            # Set a task to reparse next ones.
            from google.appengine.api.labs import taskqueue
            url = url_for('wiki/reparse', area_name=self.area.name)
            taskqueue.add(url=url, params={'cursor': query.cursor()})

        return ''
