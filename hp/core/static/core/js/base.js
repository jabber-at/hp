function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            csrftoken = $('head > meta[name="csrf-token"]').attr('content');
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});
