$(document).ready(function () {
    $('form.user-notifications input[type="checkbox"]').change(function(event) {
        var checkbox = $(event.currentTarget);
        var form = $('form.user-notifications');
        console.log(form);

        $.ajax({
            type: form.attr('method'),
            url: form.attr('action'),
            data: form.serialize(),
            success: function(data) {
                checkbox.parent('label').find('.icon-success').fadeIn(150).delay(500).fadeOut(150);
            },
            error: function(data) {
                checkbox.parent('label').find('.icon-error').fadeIn(150).delay(500).fadeOut(150);
            }
        });
    });
});
