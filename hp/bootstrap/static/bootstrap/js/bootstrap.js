$(document).ready(function() {
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
});
