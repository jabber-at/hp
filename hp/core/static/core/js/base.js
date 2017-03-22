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
function detect_platform() {
    var userAgent = navigator.userAgent || navigator.vendor || window.opera;

    if (/^Android/i.test(navigator.platform) || /android/i.test(userAgent)) {
        return 'android';
    } else if (/iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream) {
        // see http://stackoverflow.com/questions/9038625/detect-if-device-is-ios/9039885#9039885
        return 'ios';
    } else if (/^(Linux|Ubuntu)/i.test(navigator.platform)) {
        return 'linux';
    } else if (/^Windows/i.test(navigator.platform)) {
        return 'win';
    } else if (/^Mac/i.test(navigator.platform)) {
        return 'osx';
    }
};

/**
 * Apply attributes stored in named data attributes.
 *
 * If you have this HTML:
 *
 * <p data-example-attrs='{"class": "example"}'><p>
 *
 * invoking 
 *
 * apply_attrs('example');
 *
 * ... will set the class "example" on the element.
 */
function apply_attrs(name) {
    $('[data-' + name + '-attrs]').each(function(i, elem) {
        var elem = $(elem);
        elem.attr(elem.data(name + '-attrs'));
    });
}

function show_os_specific(platform) {
    if (typeof platform === 'undefined') {
        // first get any os=value query parameter (...?os=linux)
        var url = new URL(document.location);
        var platform = url.searchParams.get('os');

        // If nothing was requested via query string, try to detect platform
        if (! platform) {
            var platform = detect_platform();
        }

        if (typeof platform !== 'undefined') {
            $('select#id_os').val(platform);
        }
    }

    if (platform == 'any' || typeof platform == 'undefined') {
        $('[class^="os-"], [class*=" os-*]').show();
        apply_attrs('os-any');
    } else {
        $('[class^="os-"], [class*=" os-*]').hide();
        $('.os-' + platform).show();
        apply_attrs('os-' + platform);

        if (platform == 'android' || platform == 'ios') {
            $('.os-mobile').show();
            apply_attrs('os-mobile');
        } else {
            apply_attrs('os-desktop');
        }
    }
};

$(document).ready(function() {
    show_os_specific();

    $('select#id_os').change(function(e) {
        var selected = $(e.target).val();
        show_os_specific(selected);

        var url = new URL(document.location);
        url.searchParams.set('os', selected);
        history.pushState({}, 'foo', url.href);
    });

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
     * Generic glyph buttons in table cells, used e.g. GPG key and XEP-0363 overviews.
     */
    $('td span.glyph-button').click(function(e) {
        var glyph = $(e.currentTarget);
        var url = glyph.data('url');
        var type = glyph.data('type') || 'GET';
        var action = glyph.data('action');
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
