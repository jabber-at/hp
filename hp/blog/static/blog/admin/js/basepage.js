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
    editor.addButton('labels', {
        type: 'listbox',
        text: 'Labels',
        icon: false,
        onselect: function (e) {
            if (tinymce.activeEditor.formatter.match(this.value())) {
                // format is applied
                tinymce.activeEditor.formatter.remove(this.value());
            } else {
                tinymce.activeEditor.formatter.remove('label_default');
                tinymce.activeEditor.formatter.remove('label_primary');
                tinymce.activeEditor.formatter.remove('label_success');
                tinymce.activeEditor.formatter.remove('label_info');
                tinymce.activeEditor.formatter.remove('label_warning');
                tinymce.activeEditor.formatter.remove('label_danger');
                tinymce.activeEditor.formatter.apply(this.value());
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
    });
};
