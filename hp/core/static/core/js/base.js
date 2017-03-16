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

/**
 * Bare function to detect the operating system platform.
 *
 * Will return either 'linux', 'android', 'win', 'osx', 'ios' or an empty string, in which
 * case detection failed.
 */
function get_platform() {
    if (/^(Linux|Ubuntu)/i.test(navigator.platform)) {
        return 'linux';
    } else if (/^Android/i.test(navigator.platform)) {
        return 'android';
    } else if (/^Windows/i.test(navigator.platform)) {
        return 'win';
    } else if (/^Mac/i.test(navigator.platform)) {
        return 'osx';
    } else if (/^(iPhone|iPad|iPod)/i.test(navigator.platform)) {
        return 'ios';
    }
};

$(document).ready(function() {
    /**
     * Generic glyph buttons in table cells, used e.g. GPG key and XEP-0363 overviews.
     */
    $('td span.glyph-button').click(function(e) {
        console.log('clicked!');
        var glyph = $(e.currentTarget);
        var url = glyph.data('url');
        var type = glyph.data('type') || 'GET';
        var action = glyph.data('action');
        console.log(url, type, action);
        $.ajax({
            url: url,
            type: type,
            success: function(result) {
                if (action == 'remove-row') {
                    glyph.parents('tr').remove();
                } else if (action == 'notification') {
                    $('div.messages').append(
                            '<div class="alert alert-' + result.status + '">' + result.message + '</div>');
                } else if (action == 'refresh-row') {
                    glyph.parents('tr').replaceWith(result);
                }
            }
        });
    });
});
