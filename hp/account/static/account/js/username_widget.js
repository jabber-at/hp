var check_username = function(input, timer) {
    let minlength = parseInt(input.attr('minlength'), 10);
    let is_validating = input.data('validating');
    let value = input.val();

    // As soon as the user has entered the amount of minimum characters once, we start validating.
    // The "validating" property is already present on any submitted form.
    if (value.length >= minlength && is_validating === undefined) {
        is_validating = true;
        input.data('validating', true);
    }

    // We are not validating at this point, so return right away.
    else if (is_validating === undefined) {
        return;
    }

    let form_group = input.parents('.form-group.form-group-username');
    let domain_select = form_group.find('select#id_username_1');
    form_group.addClass('was-validated');

    let mark_valid = function() {
        form_group.addClass('fg-valid');
        form_group.removeClass('fg-invalid-syntax');
        form_group.removeClass('fg-invalid-exists');
        form_group.removeClass('fg-invalid-error');

        input[0].setCustomValidity('');
        domain_select[0].setCustomValidity('');
    }
    let invalid_syntax = function() {
        form_group.addClass('fg-invalid-syntax');
        form_group.removeClass('fg-valid');
        form_group.removeClass('fg-invalid-exists');
        form_group.removeClass('fg-invalid-error');

        let invalid_msg = form_group.find('.invalid-exists').text().trim();
        domain_select[0].setCustomValidity(invalid_msg);
    }

    let check_existance = input.data('check-existance');
    input[0].setCustomValidity('');

    if (check_existance) {
        clearTimeout(timer);

        if (input[0].checkValidity()) {
            timer = setTimeout(function() {
                let domain = form_group.find('select#id_username_1 option:selected').val();
                let exists_url = $('meta[name="account:api-check-user"]').attr('content');

                $.post(exists_url, {
                    username: value,
                    domain: domain
                }).done(function(data) { // user exists!
                    mark_valid();
                }).fail(function(data) {
                    if (data.status == 409) {  // 409 = HTTP conflict -> The user already exists.
                        let exists_msg = form_group.find('.invalid-exists').text().trim();
                        input[0].setCustomValidity(exists_msg);
                        domain_select[0].setCustomValidity(exists_msg);
                        
                        form_group.addClass('fg-invalid-exists');
                        form_group.removeClass('fg-valid');
                    } else {
                        form_group.addClass('fg-invalid-error');
                        form_group.removeClass('fg-valid');

                        let error_msg = form_group.find('.invalid-error').text().trim();
                        input[0].setCustomValidity(error_msg);
                        domain_select[0].setCustomValidity(error_msg);
                    }
                });
            }, 100);
        } else {
            invalid_syntax();
        }
    } else {
        if (input[0].checkValidity()) {
            mark_valid();
        } else {
            invalid_syntax();
        }
    }
};

$(document).ready(function() {
    var username_timer;

    $('#id_username_0').on('input propertychange paste', function(e) {
        check_username($(e.target), username_timer);
    });
    $('#id_username_1').change(function(e) {
        check_username($(e.target), username_timer);
    });
});
