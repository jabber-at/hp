$(document).ready(function() {
    $('.gpg-content.hidden-with-js').hide();
    $('.gpg-header-row.hidden-with-js .fa-angle-right').show();
    $('.gpg-header-row.hidden-with-js .fa-angle-down').hide();

    $('.gpg-header-row').click(function(e) {
        let target = $(e.target);
        $('.gpg-content').slideToggle("fast");
        $(e.target).toggleClass('show-gpg');
        target.find('.fa-angle-right').toggle();
        target.find('.fa-angle-down').toggle();
    });
});
