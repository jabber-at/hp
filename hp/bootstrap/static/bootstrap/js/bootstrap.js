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

        // remove any classes

        // if the field is required, display the appropriate message
        if (! e.target.checkValidity()) {
            if (value.length == 0 && input.prop('required')) {
                bs4_forms_set_error(input, 'required');
            } else {
                bs4_forms_set_error(input, 'invalid');
            }
        }
    });
});
