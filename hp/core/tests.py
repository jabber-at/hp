# -*- coding: utf-8 -*-
#
# This file is part of the jabber.at homepage (https://github.com/jabber-at/hp).
#
# This project is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with this project. If not, see
# <http://www.gnu.org/licenses/>.

import doctest
from contextlib import contextmanager
from unittest import mock

from celery import task

from django.test import TestCase as DjangoTestCase

from . import utils


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(utils))
    return tests


class HomepageTestCaseMixin(object):
    def assertIsTask(self, t, expected):
        self.assertEqual(t, task(expected))

    def assertTaskCall(self, mocked, task, *args, **kwargs):
        self.assertTrue(mocked.called)
        a, k = mocked.call_args
        self.assertEqual(k, {})  # apply_async receives task args/kwargs as tuple/dict arg

        instance, called_args, called_kwargs = a

        self.assertIsTask(instance, task)
        self.assertEqual(args, called_args)
        self.assertEqual(kwargs, called_kwargs)

    @contextmanager
    def mock_celery(self):
        def run(self, args, kwargs):
            return self.run(*args, **kwargs)

        with mock.patch('celery.app.task.Task.apply_async', side_effect=run, autospec=True) as func:
            yield func


class TestCase(HomepageTestCaseMixin, DjangoTestCase):
    pass
