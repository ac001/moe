/*
    tipfy javascript utilities.
    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
*/
jQuery(function($) {
    $.tipfy = $.tipfy || {};
    $.tipfy.wiki = $.tipfy.wiki || {};

    $.tipfy.wiki.set_edit_section = function(url, text, title) {
        var match = url.search(/\?/);
        url += match == -1 ? '?' : '&';
        $('.heading').each(function(i, val) {
            var link = '<a class="editsectionlink" href="' + url + 'section='
                + i + '" title="' + title + '">' + text + '</a>',
                feedlink = $('.feedlink:first', this);

            if(feedlink.size()) {
                $(link).insertBefore(feedlink);
            } else {
                $(this).append(link);
            }
        });
    };
});
