/** 
 * Javascript to hide thie widgets not used in the current target type selection.
 *
 * WARNING: This currently only works with _one_ LinkTargetField on a page. 
 */

var linktarget_show_fields = function(value) {
    if (value === "0") {
        django.jQuery('.linktarget-wrapper .wrap_target_1').show();
        django.jQuery('.linktarget-wrapper .wrap_target_2').hide();
        django.jQuery('.linktarget-wrapper .wrap_target_3').hide();
        django.jQuery('.linktarget-wrapper .wrap_target_4').hide();
        django.jQuery('.linktarget-wrapper .wrap_target_5').hide();
    } else if (value === "1") {
        django.jQuery('.linktarget-wrapper .wrap_target_1').show();
        django.jQuery('.linktarget-wrapper .wrap_target_2').show();
        django.jQuery('.linktarget-wrapper .wrap_target_3').show();
        django.jQuery('.linktarget-wrapper .wrap_target_4').hide();
        django.jQuery('.linktarget-wrapper .wrap_target_5').hide();
    } else if (value === "2") {
        django.jQuery('.linktarget-wrapper .wrap_target_1').hide();
        django.jQuery('.linktarget-wrapper .wrap_target_2').hide();
        django.jQuery('.linktarget-wrapper .wrap_target_3').hide();
        django.jQuery('.linktarget-wrapper .wrap_target_4').show();
        django.jQuery('.linktarget-wrapper .wrap_target_5').show();
    }
}

django.jQuery(document).ready(function() {
    /* setup the widget */
    linktarget_show_fields(
            django.jQuery('.linktarget-wrapper input[name="target_0"]:checked').val())

    django.jQuery('.linktarget-wrapper input[name="target_0"]').on('change', function(e) {
        linktarget_show_fields(
                django.jQuery('.linktarget-wrapper input[name="target_0"]:checked').val())
    });
});
