var check_username = function(form_group, timer) {
    let input = form_group.find('input#id_username_0');
    let domain_select = form_group.find('select#id_username_1');

    clearTimeout(timer);

    if (input[0].checkValidity()) {
        timer = setTimeout(function() {
            let exists_url = $('meta[name="account:api-check-user"]').attr('content');

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
    } else {
        invalid_syntax();
    }
};

$(document).ready(function() {
    var username_timer;

    $('input#id_username_0[data-check-existance="true"]').on('input propertychange paste', function(e) {
        let form_group = $(e.target).parents('.form-group');
        if (e.target.checkValidity()) {  // only check existance if input is valid
            check_username(form_group, username_timer);
        }
    });
    $('#id_username_1').change(function(e) {
        let form_group = $(e.target).parents('.form-group');
        check_username(form_group, username_timer);
    });
});
