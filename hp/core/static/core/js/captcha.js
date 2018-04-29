$(document).ready(function() {
    $('.form-group.fg_captcha.invalid-invalid').each(function(i, elem) {
        fg = $(elem);
        var input = fg.find('input[type="text"]');
        var error = fg.find('.invalid-feedback.invalid-invalid').text().trim();
        input.each(function(j, input) {
            input.setCustomValidity(error);
        });
    });

    $('.form-group.fg_captcha .captcha-refresh').click(function(){
        var captcha_refresh_url = $('meta[name="captcha-refresh-url"]').attr('content');
        var form_group = $(this).parents('div.form-group');
        console.log(form_group);

        $.getJSON(captcha_refresh_url, {}, function(json) {
            // This should update your captcha image src and captcha hidden input
            form_group.find('img.captcha').attr('src', json.image_url);
            form_group.find('input[type="hidden"]').attr('value', json.key);
        });

        return false;
    });
});
