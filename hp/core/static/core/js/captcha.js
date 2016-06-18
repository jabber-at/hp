$(document).ready(function() {
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
