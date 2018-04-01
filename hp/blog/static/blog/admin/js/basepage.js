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

});

/**
 * TinyMCE setup function.
 */
var tinymce_setup = function(editor) {
    let is_fontawesome_icon = function(elem) {
        return (editor.dom.hasClass(anchorElm, 'fas') || 
                editor.dom.hasClass(anchorElm, 'far') ||
                editor.dom.hasClass(anchorElm, 'fal') ||
                editor.dom.hasClass(anchorElm, 'fab'))
    };

    /** Buttons for the table menu */
    ['tablestriped', 'tablebordered', 'tablecondensed', 'tablehover', 'tableresponsive'].forEach(function(cls) {
        var stateSelector  = 'table.table.table-' + cls.substr(5);
        name = cls.substr(5);
        name = name.charAt(0).toUpperCase() + name.slice(1);
        editor.addButton(cls, {
            text: name,
            stateSelector: stateSelector,
            onclick: function() {
                editor.execCommand('mceToggleFormat', false, cls);
            },
        });
    });

    /**
     * Fontawesome icons
     */
    let fontawesome_icons = [
        'ban',
        'check',
        'edit',
        'envelope',
        'exclamation',
        'external-link-alt',
        'filter',
        'flag',
        'info',
        'minus',
        'plus',
        'redo',
        'reply',
        'rss',
        'search',
        'search-minus',
        'search-plus',
        'sort-alpha-down',
        'sort-alpha-up',
        'star',
        'sync',
        'thumbs-down',
        'thumbs-up',
        'times',
        'trash',
        'user',
    ]

    editor.addButton('icons', {
        type: 'listbox',
        text: false,
        icon: 'flag fab fa-font-awesome-flag',

        onselect: function (e) {
            /**
             * NOTE: 
             *
             * (1) We append a zero-width space at the *end* of the span because otherwise adding a Glyph in
             *     an empty paragraph eates the next element.
             * (2) We prepend a zero-width space at the beginning, because otherwise adding a Glyph in an
             *     empty paragraph will make it undeletable.
             */
            editor.insertContent('&#x200b;<span class="fas fa-' + this.value() + '"></span>&#x200b;');
        },
        values: function() {
            //alert('values!');
            let vals = [];
            fontawesome_icons.forEach(function(icon) {
                let text = icon.replace(/-/, ' ');
                text = text.replace(/\w\S*/g, function(txt) {  // capitalize words
                    return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
                });
                vals.push({
                    text: text,

                    /* NOTE: the icon property requires some custom CSS in basepage.css because TinyMCE
                     * overrides some of FontAwesome' CSS */
                    icon: "check fas fa-" + icon,
                    value: icon,
                });
            });
            return vals;
        }(),
        onPostRender: function () {
            var button = this;
            editor.on('NodeChange', function(e) {
                // Make sure that the listbuton name is always the same
                button.value('');
            });
            return;
        }
    });

    /** The lables list box */
    editor.addButton('badges', {
        type: 'listbox',
        text: 'Badges',
        onselect: function (e) {
            var val = this.value();
            if (val == 'Labels') {
                return;
            }

            if (tinymce.activeEditor.formatter.match(val)) {
                // format is already applied, so remove it
                tinymce.activeEditor.formatter.remove(val);
            } else {
                tinymce.activeEditor.formatter.remove('badge_primary');
                tinymce.activeEditor.formatter.remove('badge_secondary');
                tinymce.activeEditor.formatter.remove('badge_success');
                tinymce.activeEditor.formatter.remove('badge_info');
                tinymce.activeEditor.formatter.remove('badge_warning');
                tinymce.activeEditor.formatter.remove('badge_danger');
                tinymce.activeEditor.formatter.apply(val);
            }
        },
        values: [
            {text: 'Primary', value: 'badge_primary', 'classes': 'badge badge-primary',
             format: 'badge_primary'
            },
            {text: 'Secondary', value: 'badge_secondary' },
            {text: 'Success', value: 'badge_success', 'classes': 'badge badge-success',
             format: {name: 'badge_success'}
            },
            {text: 'Info', value: 'badge_info', 'classes': 'badge badge-info',
             style: 'font-weight: 200'
            },
            {text: 'Warning', value: 'badge_warning', 'classes': 'badge badge-warning'},
            {text: 'Danger', value: 'badge_danger', 'classes': 'badge badge-danger'},
        ],
        onpostrender: function() {
            var button = this;

            editor.on('NodeChange', function(e) {
                if (! tinymce.activeEditor.formatter) {
                    return;
                }

                var matched = tinymce.activeEditor.formatter.matchAll(
                        ['badge_secondary', 'badge_primary', 'badge_success', 'badge_info',
                         'badge_warning', 'badge_danger'])
                if (matched.length == 0) {
                    button.value('Labels');
                } else {
                    button.value(matched[0]);
                }
            });
        }
    });

    editor.addButton('tooltips', {
        icon: 'bogus fas fa-superscript',
        tooltip: "Insert/edit footnote",
        stateSelector: '[data-toggle="tooltip"]',
        onclick: function() {
            var text_body;
            var data = {};
            var selection = editor.selection;

            /**
             * This is more or less copied from the TinyMCE source code:
             * src/plugins/link/src/main/js/Plugin.js, where the link plugin is defined.
             *
             * Essentially we define a "data" object and populate it with tooltip and text from the
             * current selection. The object is passed to editor.windowManager.open() to populate 
             * the form fields defined in the "body" property.
             */
            selectedElm = selection.getNode();
            // .fas,.far,.fal,.fab matches all FontAwesome style prefixes
            anchorElm = editor.dom.getParent(
                    selectedElm,
                    '[data-toggle="tooltip"],.fas,.far,.fal,.fab');
            data.text = initialText = anchorElm ? (anchorElm.innerText || anchorElm.textContent) : selection.getContent({ format: 'text' });
            data.tooltip = anchorElm ? editor.dom.getAttrib(anchorElm, 'title') : '';

            if (! is_fontawesome_icon(anchorElm)) {
                text_body = {type: 'textbox', name: 'text', label: 'Text', 
                             onchange: function() {  /* Update the data dict on any change */
                                 data.text = this.value();
                            }
                };
            }

            editor.windowManager.open({
                title: 'Tooltip',
                body: [
                  {type: 'textbox', name: 'tooltip', label: 'Tooltip',
                   onchange: function() {  /* Update the data dict on any change */
                       data.tooltip = this.value();
                   }
                  },
                  text_body
                ],
                data: data,  /* Sets the initial values of the body elements */
                onsubmit: function(e) {
                    var createTooltip = function() {
                        var attrs = {
                            title: data.tooltip,
                            "data-toggle": "tooltip"
                        };

                        /* if anchorElm is defined, we are already in a tooltip and need to update it */
                        if (anchorElm) {
                            editor.focus();

                            if (data.text != initialText) {
                                if ("innerText" in anchorElm) {
                                    anchorElm.innerText = data.text;
                                } else {
                                    anchorElm.textContent = data.text;
                                }
                            }
                            editor.dom.setAttribs(anchorElm, attrs);

                            /* No idea what this does, but present in link plugin: */
                            selection.select(anchorElm);
                            editor.undoManager.add();
                        } else {  /* new tooltip */
                            editor.insertContent(editor.dom.createHTML(
                                'span', attrs, editor.dom.encode(data.text)
                            ));
                        }
                    }

                    var insertTooltip = function() {
                        editor.undoManager.transact(createTooltip);
                    }

                    data = tinyMCE.EditorManager.extend(data, e.data);

                    var tooltip = data.tooltip;
                    if (!tooltip) {
                        editor.dom.remove(anchorElm, true);
                        return;
                    }

                    insertTooltip();
                }
            });
        }
    });
};
