/**
 * Revert the username input field back to the default state, as if the user
 * hasn't entered anyting.
 */
var default_username_state = function(form_group) {
    form_group.removeClass('has-error');
    form_group.removeClass('has-success');
    form_group.find('#status-check span').hide();
    form_group.find('.errorlist').hide();
    form_group.find('#status-check span#default').show();
    form_group.find('.glyphicon').removeClass('glyphicon-remove').removeClass('glyphicon-ok');
}
var show_username_local_error = function(form_group, error) {
    form_group.addClass('has-error');
    form_group.removeClass('has-success');

    form_group.find('#status-check span').hide();
    form_group.find('#status-check span#invalid').show();
    form_group.find('.glyphicon').addClass('glyphicon-remove').removeClass('glyphicon-ok');
};
var show_username_available = function(form_group) {
    form_group.removeClass('has-error');
    form_group.addClass('has-success');
    form_group.find('.errorlist').hide();
    form_group.find('#status-check span').hide();
    form_group.find('#status-check span#username-available').show();
    form_group.find('.glyphicon').removeClass('glyphicon-remove').addClass('glyphicon-ok');
}
var show_username_not_available = function(form_group) {
    form_group.addClass('has-error');
    form_group.removeClass('has-success');
    form_group.find('.errorlist').hide();
    form_group.find('#status-check span').hide();
    form_group.find('#status-check span#username-not-available').show();
    form_group.find('.glyphicon').addClass('glyphicon-remove').removeClass('glyphicon-ok');
}

var show_username_error = function(form_group) {
    form_group.addClass('has-error');
    form_group.removeClass('has-success');
    form_group.find('.errorlist').hide();
    form_group.find('#status-check span').hide();
    form_group.find('#status-check span#error').show();
    form_group.find('.glyphicon').addClass('glyphicon-remove').removeClass('glyphicon-ok');
}

var check_username = function(form_group) {
    var val = form_group.find('input#id_username_0').val();

//TODO
//    if (val.length < MIN_USERNAME_LENGTH) {
    if (val.length < 2) {
        default_username_state(form_group);
        return;
//TODO
//    } else if (/[@\s]/.test(val) || val.length > MAX_USERNAME_LENGTH) {
    } else if (/[@\s]/.test(val) || val.length > 64) {
        show_username_local_error(form_group);
        return;
    }

    var username = form_group.find('input#id_username_0').val();
    var domain = form_group.find('select#id_username_1 option:selected').val();

    var exists_url = $('meta[name="account:api-check-user"]').attr('content');

    $.post(exists_url, {
        username: username,
        domain: domain
    }).done(function(data) { // user exists!
        show_username_available(form_group);
    }).fail(function(data) {
        if (data.status == 409) {  // 409 = HTTP conflict -> The user already exists.
            show_username_not_available(form_group);
        } else {
            show_username_error(form_group);
        }
    });
};

$(document).ready(function() {
    $('#id_username_0.status-check').on('input propertychange paste', function(e) {
        var form_group = $(e.target).parents('.form-group.form-group-username');
        check_username(form_group);
    });
    $('#id_username_1.status-check').change(function(e) {
        var form_group = $(e.target).parents('.form-group.form-group-username');
        check_username(form_group);
    });
});
