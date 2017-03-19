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

    editor.addButton('tableresponsive', {
        text: 'Responsive',
        stateSelector: 'div.table-responsive',
        onclick: function() {
            selectedElm = editor.selection.getNode();
            wrapperElm = editor.dom.getParent(selectedElm, 'div.table-responsive');

            var table = editor.dom.getParent(selectedElm, 'table');
            if (! table ) {
                return;
            }

            if (wrapperElm) {
                editor.dom.remove(wrapperElm, true);
            } else {
                var tableHtml = editor.dom.getOuterHTML(table);
                var wrapper = editor.dom.create('div', {'class': 'table-responsive'}, tableHtml);
                editor.dom.replace(wrapper, table);
            }
        }
    });

    var glyphs = [
        'download',
        'envelope',
        'exclamation-sign',
        'file', 
        'home', 
        'minus',
        'ok',
        'pencil',
        'plus', 
        'question-sign',
        'refresh',
        'remove',
        'repeat',
        'zoom-in',
        'zoom-out', 
    ];
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
            $('.mce-menu-item-glyphicon').each(function() {
                var elem = $(this);
                var glyph_cls = elem.attr('class').split(/\s+/).filter(function(e) {
                    return e.startsWith('mce-menu-item-glyphicon-');
                })[0];
                glyph = glyph_cls.substr(24);
                $('.' + glyph_cls + ' .mce-ico').replaceWith(
                    '<span class="glyphicon glyphicon-' + glyph + '"></span>');
            });
        },
        values: function() {
            var vals = [];
            glyphs.forEach(function(glyph) {
                var text = glyph.replace(/-/, ' ');
                var text = text.replace(/\w\S*/g, function(txt) {  // capitalize words
                    return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
                });
                vals.push({
                    text: text,
                    value: glyph,
                    classes: 'menu-item-glyphicon menu-item-glyphicon-' + glyph
                });
            });
            return vals;
        }(),
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

    editor.addButton('tooltips', {
        icon: 'superscript',
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
            anchorElm = editor.dom.getParent(selectedElm, '[data-toggle="tooltip"],span.glyphicon');
            data.text = initialText = anchorElm ? (anchorElm.innerText || anchorElm.textContent) : selection.getContent({ format: 'text' });
            data.tooltip = anchorElm ? editor.dom.getAttrib(anchorElm, 'title') : '';

            /* Determine if this is a glyph. If yes, we don't display the text element! 
             * NOTE: We use the ternary operator (instead of &&) because null && false == null.
             * */
            var is_glyph = anchorElm ? anchorElm.nodeName === 'SPAN' && editor.dom.hasClass(anchorElm, 'glyphicon') : false;

            if (! is_glyph) {
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
