var check_username = function(form_group, timer) {
    var input = form_group.find('input#id_username_0');
    var domain_select = form_group.find('select#id_username_1');

    clearTimeout(timer);

    if (input[0].checkValidity()) { // only check if the username is syntactically valid
        timer = setTimeout(function() {
            var exists_url = $('meta[name="account:api-check-user"]').attr('content');

            $.post(exists_url, {
                username: input.val(),
                domain: domain_select.val()
            }).done(function(data) { // user does not exist yet
                input[0].setCustomValidity("");
                domain_select[0].setCustomValidity("");
            }).fail(function(data) {
                if (data.status == 409) {  // 409 = HTTP conflict -> The user already exists.
                    error = bs4_forms_set_error(input, 'unique');
                    domain_select[0].setCustomValidity(error.message);
                } else {
                    bs4_forms_set_error(input, 'error');

                    domain_select[0].setCustomValidity(error_msg);
                }
            });
        }, 100);
    }
};

$(document).ready(function() {
    var username_timer;

    $('input#id_username_0[data-check-existance="true"]').on('input propertychange paste', function(e) {
        var form_group = $(e.target).parents('.form-group');
        if (e.target.checkValidity()) {  // only check existance if input is valid
            check_username(form_group, username_timer);
        }
        // TODO: set domain as invalid if username is invalid
    });

    $('#id_username_1').change(function(e) {
        var form_group = $(e.target).parents('.form-group');

        /**
         * If the username is currently invalid because of a unique constraing (-> the username already
         * exists), we clear the constraint because the username might be valid in a different domain.
         */
        if (form_group.hasClass('invalid-unique')) {
            form_group.removeClass('invalid-unique');
            form_group.find('input#id_username_0')[0].setCustomValidity('');
        }
        check_username(form_group, username_timer);
    });
});
