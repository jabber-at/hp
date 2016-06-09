/**
 * Create a slug of the given value.
 */
var slugify = function(value) {
    // replace any unsafe chars
    value = value.toLowerCase().replace(/[^a-z0-9-]/g, '-');

    // replace leading/trailing/multiple dashes
    value = value.replace(/^-*/, '').replace(/-*$/, '').replace(/-+/g, '-');

    return value;
}

django.jQuery(document).ready(function() {
    django.jQuery('input[id^="id_title_"]').on('input propertychange paste', function(e) {
        /**
         * Set the slug field for the appropriate language whenever the input changes.
         *
         * TODO: Maybe only update if the current value is identical to the old value?
         */
        var input = django.jQuery(e.target);
        var code = input.attr('id').split('_').slice(-1)[0];
        var selector = 'input#id_slug_' + code;
        django.jQuery(selector).val(slugify(input.val()));
    });
})
