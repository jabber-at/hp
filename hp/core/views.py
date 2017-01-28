# -*- coding: utf-8 -*-
#
# This file is part of the jabber.at homepage (https://github.com/jabber-at/hp).
#
# This project is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with django-xmpp-account.
# If not, see <http://www.gnu.org/licenses/>.

import ipaddress
import logging

from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.http import Http404
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.functional import Promise
from django.utils.http import is_safe_url
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.views.generic.edit import FormView
from ua_parser import user_agent_parser

from bootstrap.templatetags.bootstrap import glyph
from core.utils import canonical_link

from .constants import ACTIVITY_CONTACT
from .forms import AnonymousContactForm
from .forms import ContactForm
from .forms import SelectOSForm
from .utils import check_dnsbl
from .tasks import send_contact_email

log = logging.getLogger(__name__)
_BLACKLIST = getattr(settings, 'SPAM_BLACKLIST', set())
_RATELIMIT_WHITELIST = getattr(settings, 'RATELIMIT_WHITELIST', set())
_RATELIMIT_CONFIG = getattr(settings, 'RATELIMIT_CONFIG', {})


class TranslateSlugViewMixin(object):
    """A view mixin that allows DetailView to work with translated slugs.

    .. WARNING:: This mixin assumes:

       * There is a ``slug`` kwarg in the URL config
       * The model has a translated slug field (like core.BlogPost and core.Page)
       * The model has a ``get_absolute_url()`` method.

    Background: By default, get_object() would filter for the slug field, the translated
    database field uses the current active language. So this queryset::

        >>> from core.models import Page
        >>> Page.objects.filter(slug='foo')

    ... returns a different result depending on the browser language (on the database level,
    this would result in a ``WHERE slug_en="foo"`` in an English browser). This means that
    the URL "/page/english-slug" works in an English browser but NOT in a German browser.

    So ``get_object()`` is overwritten to filter for all language slugs. ``get()`` additionally
    returns a redirect to the slug in the current language if it's not the same as the one viewed.
    """

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # If the slug used in the view is different from the slug in the current language, redirect
        # to the latter.
        if kwargs['slug'] != self.object.slug.current:
            return HttpResponseRedirect(self.object.get_absolute_url())

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get(self.slug_url_kwarg)

        # filter for slugs in all languages
        filter = Q()
        for lang, _name in settings.LANGUAGES:
            filter |= Q(**{'slug_%s' % lang: slug})

        queryset = queryset.filter(filter)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj


class StaticContextMixin(object):
    """Simple mixin that allows you to add a static dictionary to the template context."""

    static_context = None

    def get_context_data(self, **kwargs):
        context = super(StaticContextMixin, self).get_context_data(**kwargs)
        if self.static_context is not None:
            context.update(self.static_context)

        urlname = '%s:%s' % (self.request.resolver_match.namespace,
                             self.request.resolver_match.url_name)

        if urlname in settings.SOCIAL_MEDIA_TEXTS:
            texts = settings.SOCIAL_MEDIA_TEXTS[urlname]

            for key, value in texts.items():
                if isinstance(value, (str, Promise)):
                    value = value % self.request.site
                context[key] = value

        # set default canonical URL
        context.setdefault('canonical_url', canonical_link(self.request.path))

        return context


class AntiSpamMixin(object):
    blacklist_template = 'core/antispam/blacklist.html'
    dnsbl_template = 'core/antispam/dnsbl.html'
    rate_template = 'core/antispam/rate.html'
    rate_activity = None

    def get_rate_cache_key(self, request):
        return 'rate_%s_%s' % (self.rate_activity, request.META['REMOTE_ADDR'])

    def check_rate(self, request, rate_addr):
        """Check if the given IP is currently ratelimited for this view.

        Returns
        -------

        bool
            Returns ``False`` if the IP is currently ratelimited for this activity, ``True``
            otherwise.
        """

        if self.rate_activity is None:
            return True
        if rate_addr in _RATELIMIT_WHITELIST or settings.DEBUG is True:
            return True

        cache_key = self.get_rate_cache_key(request)
        now = timezone.now()
        timestamps = cache.get(cache_key) or []
        config = _RATELIMIT_CONFIG.get(self.rate_activity, {})

        for delta, ratelimit in config:
            offset = now - delta
            if len([t for t in timestamps if t >= offset]) > ratelimit:
                return False
        return True

    def ratelimit(self, request):
        if settings.DEBUG is True:
            rate_addr = request.GET.get('ratelimit', request.META['REMOTE_ADDR'])
        else:
            rate_addr = request.META['REMOTE_ADDR']

        if rate_addr in _RATELIMIT_WHITELIST or self.rate_activity is None:
            return

        cache_key = self.get_rate_cache_key(request)
        timestamps = cache.get(cache_key) or []
        timestamps.append(timezone.now())
        cache.set(cache_key, timestamps, timeout=86400)

    def dispatch(self, request, *args, **kwargs):
        if settings.DEBUG is True:
            bl_addr = request.GET.get('blacklist', request.META['REMOTE_ADDR'])
            dnsbl_addr = request.GET.get('dnsbl', request.META['REMOTE_ADDR'])
            rate_addr = request.GET.get('ratelimit', request.META['REMOTE_ADDR'])
        else:
            bl_addr = dnsbl_addr = rate_addr = request.META['REMOTE_ADDR']

        # Check static blacklist (settings.SPAM_BLACKLIST)
        bl_addr = ipaddress.ip_address(bl_addr)
        for network in _BLACKLIST:
            if bl_addr in network:
                log.info('%s: IP is in settings.BLACKLIST.', bl_addr)
                return TemplateResponse(request, self.blacklist_template, {})

        # Check ratelimits
        if self.check_rate(request, rate_addr) is False:
            log.info('%s: IP is ratelimited.', rate_addr)
            return TemplateResponse(request, self.rate_template, {})

        # Check DNS Blacklists
        blocks = check_dnsbl(dnsbl_addr)
        if blocks:
            log.info('%s: IP is on at least one DNSBL.', dnsbl_addr)
            return TemplateResponse(request, self.dnsbl_template, {
                'blocks': blocks,
            })

        return super(AntiSpamMixin, self).dispatch(request, *args, **kwargs)


class AnonymousRequiredMixin(object):
    """Opposite of LoginRequiredMixin.

    Some views only make sense for anonymous users - e.g. logging in, registering, ...,
    so we return the user to his details page if he is logged in.
    """

    redirect_url = reverse_lazy('account:detail')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return HttpResponseRedirect(self.redirect_url)
        return super(AnonymousRequiredMixin, self).dispatch(request, *args, **kwargs)


class ClientsView(StaticContextMixin, TemplateView):
    template_name = 'core/clients.html'

    def get_os(self):
        header = self.request.META.get('HTTP_USER_AGENT',
                                       self.request.META.get('HTTP_USERAGENT'))
        if not header:
            return

        ua = user_agent_parser.Parse(header)
        family = ua['os']['family']

        if family == 'Mac OS X':
            return 'osx'
        elif family == 'iOS':
            return 'ios'
        elif family in ['Linux', 'Ubuntu', ]:
            return 'linux'
        elif family == 'Android':
            return 'android'
        elif family.startswith('Windows'):
            return 'win'
        else:
            log.warn('Unknown os family: %s', family)

    def get_context_data(self, *args, **kwargs):
        initial = self.request.GET.get('os')

        if initial is None:
            initial = self.get_os()

        context = super(ClientsView, self).get_context_data()
        context['form'] = SelectOSForm(initial={'os': initial})
        context['y'] = glyph('ok', context='success')
        context['u'] = glyph('question-sign', context='muted')
        context['n'] = glyph('remove', context='danger')
        return context


class ContactView(AntiSpamMixin, StaticContextMixin, FormView):
    template_name = 'core/contact.html'
    rate_activity = ACTIVITY_CONTACT
    success_url = reverse_lazy('core:contact')

    def get_context_data(self, *args, **kwargs):
        context = super(ContactView, self).get_context_data(*args, **kwargs)
        context['CONTACT_MUC'] = settings.CONTACT_MUC
        return context

    def get_form_class(self):
        if self.request.user.is_authenticated():
            return ContactForm
        else:
            return AnonymousContactForm

    def form_valid(self, form):
        config = self.request.site['NAME']
        subject = form.cleaned_data['subject']
        message = form.cleaned_data['text']

        recipient = None
        user_pk = None

        if isinstance(form, AnonymousContactForm):
            recipient = form.cleaned_data['email']
        else:
            user_pk = self.request.user.pk

        send_contact_email.delay(config, subject, message, recipient=recipient, user_pk=user_pk,
                                 address=self.request.META['REMOTE_ADDR'])
        return self.render_to_response(self.get_context_data(form=form))


class SetLanguageView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        request = self.request

        # Some bots might attempt to use this link without the lang parameter. If not present, this
        # view basically does nothing.
        lang = request.GET.get('lang')
        if lang:
            request.session[LANGUAGE_SESSION_KEY] = lang

        redirect_to = request.GET.get('next')

        if not request.user.is_anonymous():
            request.user.default_language = lang
            request.user.save()

        # Ensure the user-originating redirection url is safe.
        if not redirect_to or not is_safe_url(url=redirect_to, host=request.get_host()):
            redirect_to = '/'

        return redirect_to
