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
    /* emulate the behaviour of a twitter follow button */
    $('div.twitter-follow-btn a').click(function(e) {
        var href = $(e.currentTarget).attr('href');
        window.open(href, 'foo', 'width=525, height=550');
        return false;
    });
    $('div.twitter-link-btn a, div.facebook-link-btn a').click(function(e) {
        var href = $(e.currentTarget).attr('href');
        window.open(href, '_blank');
        return false;
    });

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
