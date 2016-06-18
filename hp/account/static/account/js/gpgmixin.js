$(document).ready(function() {
    $('.gpg-header-row').click(function(data) {
        $('.gpg-content').slideToggle("fast");
        $('.gpg-header-row').toggleClass('show-gpg');
    });
});
