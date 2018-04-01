$(document).ready(function() {
    $('.gpg-content.hidden-with-js').hide();
    $('.gpg-header-row.hidden-with-js .fa-angle-right').show();
    $('.gpg-header-row.hidden-with-js .fa-angle-down').hide();

    $('.gpg-header-row').click(function(data) {
        $('.gpg-content').slideToggle("fast");
        $('.gpg-header-row').toggleClass('show-gpg');
    });
});
