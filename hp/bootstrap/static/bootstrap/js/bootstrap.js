var bs4_forms_set_error = function(elem, cls) {
    var cls_name = 'invalid-' + cls;
    var form_group = elem.parents('.form-group');
    
    form_group.addClass(cls_name);
    var message = form_group.find('.invalid-feedback.' + cls_name).text();
    message = message ? message.trim() : null;
    if (message) {
        elem[0].setCustomValidity(message);
    }

    return {
        message: message
    }
};

var bs4_forms_clear_error = function(form_group) {
    form_group.removeClass(function(index, className) {
        return (className.match (/(^|\s)invalid-\S+/g) || []).join(' ');
    });
};

$(document).ready(function() {
    /* Disable built-in form validation and use javascript. */
    $('form.needs-validation').attr('novalidate', true);

    /**
     * Prevent form submission if the form is not yet valid.
     */
    $('form.needs-validation').submit(function(e) {
        if (e.target.checkValidity() === false) {
            $(e.target).find('.form-group').each(function(i, fg) {
                var form_group = $(fg);
                if (! form_group.hasClass('was-validated')) {
                    form_group.addClass('was-validated');
                    form_group.find(':invalid').each(function(i, inp) {
                        var input = $(inp);
                        var value = input.val();

                        if (value.length == 0 && input.prop('required')) {
                            bs4_forms_set_error(input, 'required');
                        } else if (e.target.validity.tooShort && form_group.find('.invalid-min_length').length) {
                            bs4_forms_set_error(input, 'min_length');
                        } else if (e.target.validity.tooLong && form_group.find('.invalid-max_length').length) {
                            bs4_forms_set_error(input, 'max_length');
                        } else {
                            bs4_forms_set_error(input, 'invalid');
                        }
                    });
                }
            });
            return false;
        }
        return true;
    });

    /**
     * Add was-validated class to form group elements.
     *
     * If min-validation-length is set, check for that length first.  Used e.g. by the email field to not
     * validate initial input on the first few characters.
     */
    $('.form-group:not(.was-validated) :input').on('input propertychange paste', function(e) {
        var input = $(e.target);
        var value = input.val();
        var min_length = input.data('min-validation-length');

        if (typeof min_length === 'undefined' || value.length > min_length) {
            input.parents('.form-group').addClass('was-validated');
        }
    });

    $('.form-group :input').on('input propertychange paste', function(e) {
        var input = $(e.target);
        var value = input.val();
        var form_group = input.parents('.form-group');

        // first, clear any custom message
        e.target.setCustomValidity('');
        bs4_forms_clear_error(form_group);

        // if the field is required, display the appropriate message
        if (! e.target.checkValidity()) {
            if (value.length == 0 && input.prop('required')) {
                bs4_forms_set_error(input, 'required');
            } else if (e.target.validity.tooShort && form_group.find('.invalid-min_length').length) {
                bs4_forms_set_error(input, 'min_length');
            } else if (e.target.validity.tooLong && form_group.find('.invalid-max_length').length) {
                bs4_forms_set_error(input, 'max_length');
            } else {
                bs4_forms_set_error(input, 'invalid');
            }
        }
    });

    /**
     * Handle text in custom file inputs.
     */
    $('input[type="file"].custom-file-input').on('change', function(e) {
        var target = $(e.target);
        var filename = target.val().split('\\').pop();
        target.siblings('label.custom-file-label').text(filename);

        // clear validity, otherwise we're not allowed to submit
        e.target.setCustomValidity('');
        target.parents('.form-group').find('.invalid-feedback').hide();
    });

    $('.form-group.invalid-mime-type').each(function(i, elem) {
        elem = $(elem);
        var input = elem.find('input[type="file"]');
        var error = elem.find('.invalid-feedback.invalid-mime-type').text().trim();
        input.each(function(j, input) {
            input.setCustomValidity(error);
        });
    });
    $('.form-group.invalid-too-large').each(function(i, elem) {
        elem = $(elem);
        var input = elem.find('input[type="file"]');
        var error = elem.find('.invalid-feedback.invalid-too-large').text().trim();
        input.each(function(j, input) {
            input.setCustomValidity(error);
        });
    });

    /**
     * Handle password-confirmation fields
     */
    $('input[type="password"].set-password').on('input propertychange paste', function(e) {
        var pwd = $(e.target);
        var form = pwd.parents('form');
        var form_group = pwd.parents('.form-group')
        var value = pwd.val();
        var confirm_pwd = form.find('input[type="password"].confirm-password');
        var confirm_val = confirm_pwd.val();
        var confirm_fg = confirm_pwd.parents('.form-group');

        /**
         * Add was-validated to the confirmation field as soon as this field has it. 
         */
        if (form_group.hasClass('was-validated')) {
            confirm_fg.addClass('was-validated');
        }

        if (value === confirm_val && confirm_val) {
            confirm_pwd[0].setCustomValidity('');
            bs4_forms_clear_error(confirm_fg);
        } else if (! confirm_val) {
            confirm_fg.removeClass('invalid-no-match');
            confirm_fg.addClass('invalid-required');
        } else {
            bs4_forms_set_error(confirm_pwd, 'no-match');
        }
    });

    $('input[type="password"].confirm-password').on('input propertychange paste', function(e) {
        var confirm_pwd = $(e.target);
        var form = confirm_pwd.parents('form');
        var pwd = form.find('input[type="password"].set-password');
        var form_group = confirm_pwd.parents('.form-group');
        var value = confirm_pwd.val();

        if (value === pwd.val()) {
            bs4_forms_clear_error(form_group);
        } else if (value === '') {
            form_group.removeClass('invalid-no-match');
            form_group.addClass('invalid-required');
        } else {
            bs4_forms_set_error(confirm_pwd, 'no-match');
        }
    });
});
