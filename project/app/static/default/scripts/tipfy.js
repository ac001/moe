/*
    tipfy javascript utilities.
    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
*/
jQuery(function($) {
    $.tipfy = $.tipfy || {};

    // Notification System - adapted from jGrowl by Stan Lemon <stanlemon@mac.com>
    $.tipfy.message_box = function(id) {
        var self = this;
        this.interval = false;
        this.interval_count = 0;

        this.box = $('#' + id);
        if(this.box.size() == 0) {
            this.box = $('<div/>').attr('id', id).addClass('tp-msg-box').appendTo('body');
            if ($.browser.msie && parseInt($.browser.version) < 7 && !window["XMLHttpRequest"]) {
                this.box.addClass('tp-msg-box-ie6');
            }
        }

        $('.tp-msg', this.box).each(function(k, v) {
            var life = $(this).attr('life');
            self.add_events($(this), (life != undefined && life != '') ? life * 1 : 0);
        });
    };
    $.extend($.tipfy.message_box.prototype, {
        set_timer: function(msg, life) {
            var self = this,
                update = function() {
                    $('div.tp-msg', self.box).each(function(k, v) {
                        data = $.data(v, 'msg');
                        if(data != undefined && data.pause != true &&
                           data.life != undefined && data.created != undefined &&
                           (data.created.getTime() + data.life) < (new Date()).getTime()) {
                            self.remove($(this));
                        }
                    });
                };

            this.interval_count++;
            $.data(msg, 'msg', {created: new Date(), life: life, pause: false});
            $(msg).bind('mouseover', function() { $(msg).data('msg').pause = true; })
                  .bind('mouseout', function() { $(msg).data('msg').pause = false; });
            if(this.interval == false) {
                this.interval = setInterval(update, 1000);
            }
        },
        add_events: function(msg, life) {
            var self = this;
            msg.fadeIn('normal', function() {
                if(life > 0) {
                    self.set_timer(this, life);
                }
            });
            $('.tp-msg-close', msg).click(function() { self.remove(msg); });
        },
        add: function(level, settings) {
            var options = $.extend({
                    bd: '',
                    hd: null,
                    life: 0,
                    closable: true
                }, settings),
                hd = options.hd ? '<div class="tp-msg-hd">' + options.hd + '</div>' : '',
                close = options.closable ? '<div class="tp-msg-close">&times;</div>' : '',
                msg = $('<div class="tp-msg tp-msg-' + level + '">' + hd + close + '<div class="tp-msg-bd">' + options.bd + '</div></div>');
                msg.prependTo(this.box);
                this.add_events(msg, options.life);
                return msg;
        },
        remove: function(msg) {
            var self = this;
            $(msg).fadeOut('normal', function() {
                if($.data(this, 'msg') != undefined) {
                    self.interval_count--;
                    if(self.interval_count == 0) {
                        clearInterval(self.interval)
                        self.interval = false;
                    }
                }
                $(this).remove();
            });
        },
        remove_all: function() {
            var self = this;
            $('div.tp-msg', this.box).each(function() { self.remove(this); });
        }
    });

    // Simplified tooltip - adapted from original by Alen Grakalic (http://cssglobe.com)
    $.fn.tooltip = function() {
        var tooltip = $('#tp-tooltip');
        if(tooltip.size() == 0) {
            tooltip = $('<p id="tp-tooltip"></p>').appendTo('body');
        }
        return this.each(function() {
            if(this.title || this.alt) {
                var xOffset = 10, yOffset = 25, tooltip_text = this.title || this.alt;
                $(this).removeAttr('title').removeAttr('alt').hover(function(e) {
                    tooltip.stop(true, true).hide().html(tooltip_text)
                    .css({top: (e.pageY - xOffset) + 'px', left: (e.pageX + yOffset) + 'px'})
                    .fadeIn('fast');
                },
                function() {
                    tooltip.hide();
                }).mousemove(function(e) {
                    tooltip.css({top: (e.pageY - xOffset) + 'px', left: (e.pageX + yOffset) + 'px'});
                });
            }
        });
    };

    $.tipfy.msg = new $.tipfy.message_box('tp-msg-box');
});
