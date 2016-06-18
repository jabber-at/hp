$(document).ready(function() {
    $('.gpg-header-row').click(function(data) {
        $('#fg_gpg_fingerprint').slideToggle("fast");
        $('#fg_gpg_key').slideToggle("fast");
    });
});
