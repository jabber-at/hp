$(function() {
   jsxc.init({
      loginForm: {
         form: '#form',
         jid: '#username',
         pass: '#password'
      },
      logoutElement: $('#logout'),
      root: '/jsxc.example/jsxc',
      xmpp: {
         url: 'https://http.jabber.at/http-bind/',
         domain: 'localhost',
         resource: 'example'
      }
   });
});
