####################
ConverseJS - WebChat
####################

Currently there is a clone of the upstream repo
`here <https://github.com/jabber-at/converse.js>`_.

There are four relevant branches right now

# master - upstream master
# jabber-at - local, jabber.at specific changes
# csp-compat-2 - patches to improve CSP compat
# jabber-at-csp - jabber-at + csp-compat-2

To build new version::

   make clean dist
   cp -r css/* dist/* ...../hp/hp/conversejs/static/conversejs/
