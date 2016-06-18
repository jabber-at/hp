$(document).ready(function() {
    $('input[type="text"].gpg-fingerprint').on('input propertychange paste', function(data) {
        var re = /^[A-Fa-f0-9]*$/;
        var input = $(this);
        var value = input.val();
        var form_group = input.parents('div.form-group');
        var icon = form_group.find('.glyphicon');

        // replace all spaces, should have 40 characters by then
        value = value.replace(/\s/g, '');
        console.log(value);

        if (! value) {  // empty field
            form_group.removeClass('has-error').removeClass('has-success');
            icon.removeClass('glyphicon-remove').removeClass('glyphicon-ok')
        } else if (re.test(value) && value.length == 40) {
            form_group.removeClass('has-error').addClass('has-success');
            icon.removeClass('glyphicon-remove').addClass('glyphicon-ok')
        } else {
            form_group.addClass('has-error').removeClass('has-success');
            icon.addClass('glyphicon-remove').removeClass('glyphicon-ok')
        }
    });
});
