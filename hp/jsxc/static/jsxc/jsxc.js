$(function() {
   jsxc.init({
      loginForm: {
         form: '#jsxc-main-form',
         jid: '#id_username_0',
         pass: '#id_password'
      },
      logoutElement: $('#logout'),
      root: '/static/jsxc/lib/jsxc/'
      xmpp: {
         url: 'https://http.jabber.at/http-bind/',
         domain: 'localhost',
         resource: 'example'
      }
   });
});
