$(document).ready(function() {
    /**
     * Display server-side check if domain exists or not.
     */
    $('.form-group.invalid-domain-does-not-exist').each(function(i, elem) {
        elem = $(elem);
        let input = elem.find('input[type="email"]');
        let error = elem.find('.invalid-feedback.invalid-domain-does-not-exist').text().trim();
        input.each(function(j, input) {
            input.setCustomValidity(error);
        });
    });
});
