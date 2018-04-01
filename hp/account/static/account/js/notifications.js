$(document).ready(function () {
    $('form.user-notifications input[type="checkbox"]').change(function(event) {
        let checkbox = $(event.currentTarget);
        let form = $('form.user-notifications');

        $.ajax({
            type: form.attr('method'),
            url: form.attr('action'),
            data: form.serialize(),
            success: function(data) {
                checkbox.siblings('.icon-success').fadeIn(150).delay(500).fadeOut(150);
            },
            error: function(data) {
                checkbox.siblings('.icon-error').fadeIn(150).delay(500).fadeOut(150);
            }
        });
    });
});
