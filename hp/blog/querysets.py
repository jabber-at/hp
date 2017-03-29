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

from django.conf import settings
from django.db import models
from django.utils import timezone


class BasePageQuerySet(models.QuerySet):
    def slug(self, slug):
        """Filters for a given slug in any language."""

        query = None
        for lang, _name in settings.LANGUAGES:
            if query is None:
                query = models.Q(**{'slug_%s' % lang: slug})
            else:
                query |= models.Q(**{'slug_%s' % lang: slug})

        return self.filter(query)


class PageQuerySet(BasePageQuerySet):
    pass


class BlogPostQuerySet(BasePageQuerySet):
    def published(self, now=None):
        if now is None:
            now = timezone.now()

        return self.filter(published=True, publication_date__lt=now)

    def blog_order(self):
        return self.order_by('-sticky', '-created')
