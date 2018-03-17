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
    form_group.addClass('was-validated');

    let check_existance = input.data('check-existance');
    if (check_existance) {
        clearTimeout(timer);

        if (! input.validity.valid) {
            console.log("Username is not valid, hide any availability message.");
        } else {
            timer = setTimeout(function() {
                let domain = form_group.find('select#id_username_1 option:selected').val();
                let exists_url = $('meta[name="account:api-check-user"]').attr('content');

                $.post(exists_url, {
                    username: value,
                    domain: domain
                }).done(function(data) { // user exists!
                    //show_username_available(form_group);
                    console.log('AVAILABLE');
                }).fail(function(data) {
                    if (data.status == 409) {  // 409 = HTTP conflict -> The user already exists.
                        //show_username_not_available(form_group);
                        console.log('NOT AVAILABLE');
                    } else {
                        //show_username_error(form_group);
                        console.log('ERROR');
                    }
                });
            }, 1000);
        }
    }
};

$(document).ready(function() {
    var username_timer;

    $('#id_username_0.status-check').on('input propertychange paste', function(e) {
        check_username($(e.target), username_timer);
    });
    $('#id_username_1.status-check').change(function(e) {
        check_username($(e.target), username_timer);
    });
});
