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
    });
});
