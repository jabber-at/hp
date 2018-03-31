var bs4_forms_set_error = function(elem, cls) {
    let cls_name = 'invalid-' + cls;
    let form_group = elem.parents('.form-group');
    
    form_group.addClass(cls_name);
    let message = form_group.find('.invalid-feedback.' + cls_name).text();
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
    $('form').attr('novalidate', true);

    /**
     * Add was-validated class to form group elements.
     *
     * If min-validation-length is set, check for that length first.  Used e.g.  by the email field to not
     * validate initial input on the first few characters.
     */
    $('.form-group:not(.was-validated) input').on('input propertychange paste', function(e) {
        let input = $(e.target);
        let value = input.val();
        let min_length = input.data('min-validation-length');

        if (typeof min_length === 'undefined' || value.length > min_length) {
            input.parents('.form-group').addClass('was-validated');
        }
    });

    $('.form-group input').on('input propertychange paste', function(e) {
        let input = $(e.target);
        let value = input.val();
        let form_group = input.parents('.form-group');

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
        let target = $(e.target);
        let filename = target.val().split('\\').pop();
        target.siblings('label.custom-file-label').text(filename);
        console.log('file changed: ' + filename);

    });

    $('.form-group.invalid-mime-type').each(function(i, elem) {
        elem = $(elem);
        let input = elem.find('input[type="file"]');
        let error = elem.find('.invalid-feedback.invalid-mime-type').text().trim();
        input.each(function(j, input) {
            input.setCustomValidity(error);
        });
    });

    /**
     * Handle password-confirmation fields
     */
});
