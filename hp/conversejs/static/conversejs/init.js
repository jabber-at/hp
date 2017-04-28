//require(['converse'], function (converse) {
    converse.initialize({
        bosh_service_url: 'https://jabber.at/http-bind/', // Please use this connection manager only for testing purposes
        i18n: locales.en, // Refer to ./locale/locales.js to see which locales are supported
        show_controlbox_by_default: true,
        roster_groups: true,
        allow_registration: false
    });
//});
