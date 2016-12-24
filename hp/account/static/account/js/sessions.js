$(document).ready(function () {
    $('td.delete').click(function(e) {
        var td = $(e.currentTarget);
        var url = td.data('delete-url');
        console.log(url);
        $.ajax({
            url: url,
            type: 'DELETE',
            success: function(result) {
                td.parent('tr').remove();
            }
        });
    });
});
