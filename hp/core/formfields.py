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

import json
import logging

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.widgets import AdminTextInputWidget

from .constants import TARGET_CHOICES
from .constants import TARGET_NAMED_URL
from .constants import TARGET_MODEL
from .constants import TARGET_URL
from .widgets import LinkTargetWidget

log = logging.getLogger(__name__)


class LinkTargetField(forms.MultiValueField):
    """Form field for :py:class:`~core.modelfields.LinkTarget` database fields.

    Parameters
    ----------

    admin : bool, optional
        If True, the field will use the admin widgets instead of the default widgets.
    models : list, optional
        A list of models this target could link to. Each element of the list is either a model
        or the name identifying the model, e.g. "core.page".
    """

    def __init__(self, *args, **kwargs):
        is_admin = kwargs.pop('admin', False)  # TODO

        model_choices = []
        for model in kwargs.pop('models', ['core.page', 'blog.blogpost']):
            if isinstance(model, str):
                app_label, model = model.split('.', 1)
                model_choices.append(ContentType.objects.get_by_natural_key(app_label, model))
            else:
                model_choices.append(ContentType.objects.get_for_model(model))
        model_choices = ContentType.objects.filter(pk__in=[c.pk for c in model_choices])

        text_widget = forms.TextInput
        if is_admin is True:
            text_widget = AdminTextInputWidget

        fields = (
            forms.ChoiceField(choices=TARGET_CHOICES.items()),  # type

            # path (url or name of TARGET_NAMED_URL)
            forms.CharField(required=False, widget=text_widget),

            # args (for TARGET_NAMED_URL args)
            forms.CharField(required=False, widget=text_widget),

            # kwargs (for TARGET_NAMED_URL kwargs)
            forms.CharField(required=False, widget=text_widget),

            # For a generic link to an object
            forms.ModelChoiceField(queryset=model_choices, required=False, empty_label=None),
            forms.CharField(required=False),  # pk of the object, will be a nice select
        )
        self.widget = LinkTargetWidget(widgets=[f.widget for f in fields], models=model_choices)

        super(LinkTargetField, self).__init__(fields=fields,
                                              require_all_fields=False, *args,
                                              **kwargs)

    def compress(self, data_list):
        typ, path, args, kwargs, model, pk = data_list
        typ = int(typ)

        if typ == TARGET_URL:
            return {
                'typ': typ,
                'url': path,
            }
        elif typ == TARGET_NAMED_URL:
            return {
                'typ': typ,
                'name': path,
                'args': json.loads(args),
                'kwargs': json.loads(kwargs),
            }
        elif typ == TARGET_MODEL:
            return {
                'typ': typ,
                'content_type': model.pk,
                'object_id': int(pk),
            }
        log.error("Unkown target type %s", typ)
        return {typ: TARGET_URL, 'url': ''}
