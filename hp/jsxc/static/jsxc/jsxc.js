$(function() {
    jsxc.init({
        xmpp: {
            url: 'https://http.jabber.at/http-bind/'
        },
        root: '/static/jsxc/lib/jsxc/'
    });

    $('#jsxc-main-form #jsxc-login').click(function(){
        console.log('submit')
        var node = $('#jsxc-main-form #id_username_0').val();
        var domain = $('#jsxc-main-form #id_username_1').val();
        var password = $('#id_password').val();
        var jid = node + '@' + domain;
        jsxc.start(jid , password);
        return false;
    });

    /*
    jsxc.init({
        loginForm: {
            form: '#jsxc-main-form',
            jid: '#id_username_0',
            pass: '#id_password'
        },
        logoutElement: $('#logout'),
        root: '/static/jsxc/lib/jsxc/',
        xmpp: {
            url: 'https://http.jabber.at/http-bind/',
            domain: 'localhost',
            resource: 'jsxc'
        }
    });
    */
});
