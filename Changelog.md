# Changelog

## 2016-09-11

* Make the set-language view more fail-safe (e.g. missing query parameters) and pass the full path
  including the query string.
* Add `rel="nofollow"` set-language links.
* Remove dependency for python-gnupg (we use pygpgme now).

### Contact form

* Do not CC the message to anonmous users, to make sure that the contact form cannot be abused to
  send SPAM.
* Set the Reply-To header to the contact address and the users address. That way we can just hit
  "Reply" to answer more quickly.
* Add the IP-Address that submitted the contact form is passed in the `X-Homepage-Submit-Address`
  header.
* The user currently logged in, if any, is passed in the `X-Homepage-Logged-In-User` header.
