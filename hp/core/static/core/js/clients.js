$(document).ready(function() {
    $('form#clients-form select#id_os').change(function(e) {
        var value = $(e.target).val();
        console.log('changing: ' + value);
        if (value == "any") {
            $('table#clients-table tr').show();
        } else {
            $('table#clients-table tr').hide();
            $('table#clients-table tr.header-row').show();
            $('table#clients-table tr.' + value).show();
        }
    });
});
