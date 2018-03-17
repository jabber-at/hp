$(document).ready(function() {
    $('input[type="text"].gpg-fingerprint').on('input propertychange paste', function(data) {
        var re = /^[A-Fa-f0-9]*$/;
        var input = $(this);
        var value = input.val();
        var form_group = input.parents('div.form-group');
        var icon = form_group.find('.glyphicon');

        // replace all spaces, should have 40 characters by then
        value = value.replace(/\s/g, '');
    });
});
