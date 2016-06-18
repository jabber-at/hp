$(document).ready(function() {
    $('input[type="email"].valid-email').on('input propertychange paste', function(data) {
        var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;

        var input = $(this);
        var value = input.val();
        var form_group = input.parents('div.form-group');
        var icon = form_group.find('.glyphicon');

        if (! value) {
            form_group.removeClass('has-error').removeClass('has-success');
            icon.removeClass('glyphicon-remove').removeClass('glyphicon-ok')
        } else if (re.test(value)) {
            form_group.removeClass('has-error').addClass('has-success');
            icon.removeClass('glyphicon-remove').addClass('glyphicon-ok')
        } else {
            form_group.addClass('has-error').removeClass('has-success');
            icon.addClass('glyphicon-remove').removeClass('glyphicon-ok')
        }
    });
});
