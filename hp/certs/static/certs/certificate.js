$(document).ready(function() {
    $('form#cert-selection div.submit-row').hide();
    $('form#cert-selection select#id_certificate').change(function(e) {
        $('form#cert-selection').submit();
    });
});
