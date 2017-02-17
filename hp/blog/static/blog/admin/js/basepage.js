django.jQuery(document).ready(function() {
    var calculate_length = function(input) {
        var checker = input.parent().find('.test-length');
        var max_length = parseInt(input.attr('maxlength'));
        checker.text(max_length - input.val().length);
    };

    django.jQuery('fieldset.meta-descriptions span.test-length').each(function() {
        var input = $(this).parents('div.field-box').find('input');
        calculate_length(input);
    });

    django.jQuery('fieldset.meta-descriptions input[id^="id_meta_summary_"]').on('input propertychange paste', function(e) {
        var input = django.jQuery(e.target);
        calculate_length(input);
    });
    django.jQuery('fieldset.meta-descriptions input[id^="id_twitter_summary_"]').on('input propertychange paste', function(e) {
        var input = django.jQuery(e.target);
        calculate_length(input);
    });

    django.jQuery('.mce-menu-item-glyphicon-ok .mce-text').text('foobar1');
});

/**
 * TinyMCE setup function.
 */
var tinymce_setup = function(editor) {
    /** Buttons for the table menu */
    ['tablestriped', 'tablebordered', 'tablecondensed', 'tablehover'].forEach(function(cls) {
        name = cls.substr(5);
        name = name.charAt(0).toUpperCase() + name.slice(1);
        editor.addButton(cls, {
            text: name,
            onclick: function() {
                editor.execCommand('mceToggleFormat', false, cls);
            },
            onpostrender: function() {
                /** 
                 * Note: This is supposed to activate the button when the style is active (e.g.
                 * like th bold button when you're in bold text), but it only works in the main
                 * toolbar.
                 */
                
                var btn = this;
                editor.on('init', function() {
                    editor.formatter.formatChanged(cls, function(state) {
                        btn.active(state);
                    });
                });
            }
        });
    });

    /**
     * Glyphicons
     */
    editor.addButton('glyphs', {
        type: 'listbox',
        text: 'Glyphs',
        icon: false,
        onselect: function (e) {
            /**
             * NOTE: We append a zero-width space at the end of the span because otherwise adding a
             * Glyph in an empty paragraph eates the next element.
             */
            var val = this.value();
            editor.insertContent(
                '<span class="glyphicon glyphicon-' + val + '" aria-hidden="true"></span>&#x200b;'
            );
        },
        onclick: function(e) {
            $('.mce-menu-item-glyphicon-ok .mce-ico').replaceWith(
                    '<span class="glyphicon glyphicon-ok"></span>');
            $('.mce-menu-item-glyphicon-remove .mce-ico').replaceWith(
                    '<span class="glyphicon glyphicon-remove"></span>');
            $('.mce-menu-item-glyphicon-refresh .mce-ico').replaceWith(
                    '<span class="glyphicon glyphicon-refresh"></span>');
            $('.mce-menu-item-glyphicon-exclamation-sign .mce-ico').replaceWith(
                    '<span class="glyphicon glyphicon-exclamation-sign"></span>');
            $('.mce-menu-item-glyphicon-download .mce-ico').replaceWith(
                    '<span class="glyphicon glyphicon-download"></span>');
        },
        values: [
            {text: 'OK', classes: 'menu-item-glyphicon-ok', value: 'ok' },
            {text: 'Remove', classes: 'menu-item-glyphicon-remove', value: 'remove' },
            {text: 'Refresh', classes: 'menu-item-glyphicon-refresh', value: 'refresh' },
            {text: 'Exclamation', classes: 'menu-item-glyphicon-exclamation-sign', 
             value: 'exclamation-sign' },
            {text: 'Download', classes: 'menu-item-glyphicon-download', value: 'download' },
        ],
        onPostRender: function () {
            var button = this;
            editor.on('NodeChange', function(e) {
                // Make sure that the listbuton name is always the same
                button.value('Glyphs');
            });
            return;
        }
    });

    /** The lables list box */
    editor.addButton('labels', {
        type: 'listbox',
        text: 'Labels',
        icon: false,
        onselect: function (e) {
            var val = this.value();
            if (val == 'Labels') {
                return;
            }

            if (tinymce.activeEditor.formatter.match(val)) {
                // format is already applied, so remove it
                tinymce.activeEditor.formatter.remove(val);
            } else {
                tinymce.activeEditor.formatter.remove('label_default');
                tinymce.activeEditor.formatter.remove('label_primary');
                tinymce.activeEditor.formatter.remove('label_success');
                tinymce.activeEditor.formatter.remove('label_info');
                tinymce.activeEditor.formatter.remove('label_warning');
                tinymce.activeEditor.formatter.remove('label_danger');
                tinymce.activeEditor.formatter.apply(val);
            }
        },
        values: [
            {text: 'Default', value: 'label_default' },
            {text: 'Primary', value: 'label_primary', 'classes': 'label label-primary',
             format: 'label_primary'
            },
            {text: 'Success', value: 'label_success', 'classes': 'label label-success',
             format: {name: 'label_success'}
            },
            {text: 'Info', value: 'label_info', 'classes': 'label label-info',
             style: 'font-weight: 200'
            },
            {text: 'Warning', value: 'label_warning', 'classes': 'label label-warning'},
            {text: 'Danger', value: 'label_danger', 'classes': 'label label-danger'},
        ],
        onpostrender: function() {
            var button = this;

            editor.on('NodeChange', function(e) {
                if (! tinymce.activeEditor.formatter) {
                    return;
                }

                var matched = tinymce.activeEditor.formatter.matchAll(
                        ['label_default', 'label_primary', 'label_success', 'label_info',
                         'label_warning', 'label_danger'])
                if (matched.length == 0) {
                    button.value('Labels');
                } else {
                    button.value(matched[0]);
                }
            });
        }
    });
};
