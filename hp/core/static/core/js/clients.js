var update_client_list = function(elem) {
    var value = elem.val();
    if (value == "any") {
        $('table#clients-table tr').show();
    } else {
        $('table#clients-table tr').hide();
        $('table#clients-table tr.header-row').show();
        $('table#clients-table tr.' + value).show();
    }

    if (value == 'android' || value == 'ios' || value == 'any') {
        $('table#clients-table .mobile').show();
    } else {
        $('table#clients-table .mobile').hide();
    }
};

$(document).ready(function() {
    update_client_list($('form#clients-form select#id_os'));

    $('form#clients-form select#id_os').change(function(e) {
        update_client_list($(e.target));
    });
});
