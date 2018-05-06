$(document).ready(function() {
    /**
     * Display server-side check if domain exists or not.
     */
    $('.form-group.invalid-domain-does-not-exist').each(function(i, elem) {
        elem = $(elem);
        var input = elem.find('input[type="email"]');
        var error = elem.find('.invalid-feedback.invalid-domain-does-not-exist').text().trim();
        input.each(function(j, input) {
            input.setCustomValidity(error);
        });
    });
    $('.form-group.invalid-domain-banned').each(function(i, elem) {
        elem = $(elem);
        var input = elem.find('input[type="email"]');
        var error = elem.find('.invalid-feedback.invalid-domain-banned').text().trim();

        input.each(function(j, input) {
            input.setCustomValidity(error);
        });
    });
});
