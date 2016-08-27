var check_new_password = function(input) {
};

$(document).ready(function() {
    $('input[type="password"]').on('input propertychange paste', function(data) {
        var input = $(this);
        var minlength = input.attr('minlength');
        var form = input.parents('form');

        var input = form.find('input[type="password"]#id_password');
        var input2 = form.find('input[type="password"]#id_password2');

        var value = input.val();
        var value2 = input2.val();

        if (! value) {  // empty field
            form.find('div.form-group').removeClass('has-error').removeClass('has-success');
            form.find('.glyphicon').removeClass('glyphicon-remove').removeClass('glyphicon-ok');
        } else if (value.length < minlength || value !== value2) {
            form.find('div.form-group').addClass('has-error').removeClass('has-success');
            form.find('.glyphicon').addClass('glyphicon-remove').removeClass('glyphicon-ok');
        } else {
            form.find('div.form-group').removeClass('has-error').addClass('has-success');
            form.find('.glyphicon').removeClass('glyphicon-remove').addClass('glyphicon-ok');
        }
    });
});
