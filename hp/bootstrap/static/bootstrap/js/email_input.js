$(document).ready(function() {
    $('input[type="email"].valid-email').on('input propertychange paste', function(data) {
        var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;

        var input = $(this);
        var value = input.val();
        var form_group = input.parents('div.form-group');
        var icon = form_group.find('.glyphicon');
    });
});
