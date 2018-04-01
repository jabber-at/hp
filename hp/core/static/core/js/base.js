// Function to get the current value of the CSRF cookie
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            var csrftoken = getCookie('csrftoken');
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

$(document).ready(function() {
    /**
     * Activate any footnotes.
     */
    $('[data-toggle="tooltip"]').each(function() {
        var elem = $(this);
        elem.tooltip({
            html:true,
            container: elem,
            delay: {hide:400}
        });
    });

    /**
     * Generic icon buttons in table cells, used e.g. GPG key and XEP-0363 overviews.
     */
    $('td .icon-button').click(function(e) {
        var icon = $(e.currentTarget);
        var url = icon.data('url');
        var type = icon.data('type') || 'GET';
        var action = icon.data('action');
        $.ajax({
            url: url,
            type: type,
            success: function(result) {
                if (action == 'remove-row') {
                    icon.parents('tr').remove();
                } else if (action == 'notification') {
                    $('div.messages').append(
                            '<div class="alert alert-' + result.status + '">' + result.message + '</div>');
                } else if (action == 'refresh-row') {
                    icon.parents('tr').replaceWith(result);
                }
            }
        });
    });
});
