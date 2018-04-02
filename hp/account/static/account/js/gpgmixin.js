$(document).ready(function() {
    $('.gpg-content.hidden-with-js').hide();
    $('.gpg-header-row.hidden-with-js .icon-folded').show();
    $('.gpg-header-row.hidden-with-js .icon-unfolded').hide();

    $('.gpg-header-row').click(function(e) {
        var target = $(e.target);
        $('.gpg-content').slideToggle("fast");
        $(e.target).toggleClass('show-gpg');
        target.find('.icon-unfolded').toggle();
        target.find('.icon-folded').toggle();
    });
});
