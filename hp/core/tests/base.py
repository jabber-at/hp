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

import re
from contextlib import contextmanager
from unittest import mock

from celery import task
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase as DjangoTestCase


class HomepageTestCaseMixin(object):
    def assertIsTask(self, t, expected):
        self.assertEqual(t, task(expected))

    def assertTaskCount(self, mocked, count):
        """Assert that `count` Celery tasks have been called."""
        self.assertEqual(mocked.call_count, count)

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

        with mock.patch('celery.app.task.Task.apply_async', side_effect=run, autospec=True) as mocked:
            yield mocked


class SeleniumMixin(object):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver(executable_path=settings.GECKODRIVER_PATH)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    class wait_for_css_property(object):
        def __init__(self, elem, prop, value):
            self.elem = elem
            self.prop = prop
            self.value = value

        def __call__(self, driver):
            if self.elem.value_of_css_property(self.prop) == self.value:
                return self.elem
            else:
                return False

    def wait_for_display(self, elem, wait=2):
        WebDriverWait(self.selenium, wait).until(lambda d: elem.is_displayed())

    def wait_for_page_load(self, wait=2):
        WebDriverWait(self.selenium, wait).until(lambda driver: driver.find_element_by_tag_name('body'))

    def wait_for_valid_form(self, form=None, wait=2):
        """Wait until a form becomes valid according to HTML5 form validation.

        The registration form becomes valid only after a split second, for some reason.
        """
        if form is None:
            form = self.find('form')

        WebDriverWait(self.selenium, wait).until(
            lambda driver: self.selenium.execute_script('return arguments[0].checkValidity() === true', form))

    def wait_for_focus(self, elem):
        # when an element gets focus, it turns blue:
        wait = WebDriverWait(self.selenium, 10)
        wait.until(self.wait_for_css_property(elem, 'border-top-color', 'rgb(128, 189, 255)'))

    def wait_for_invalid(self, elem):
        wait = WebDriverWait(self.selenium, 10)
        wait.until(self.wait_for_css_property(elem, 'border-top-color', 'rgb(220, 53, 69)'))

    def wait_for_valid(self, elem):
        wait = WebDriverWait(self.selenium, 10)
        wait.until(self.wait_for_css_property(elem, 'border-top-color', 'rgb(40, 167, 69)'))

    def find(self, selector):
        """Find an element by CSS selector."""

        return self.selenium.find_element_by_css_selector(selector)

    def get_classes(self, elem):
        """Get CSS classes from the passed Element."""

        return re.split('\s*', elem.get_attribute('class').strip())

    def get_validity(self, elem):
        """Get validity object from a HTML5 form field."""

        return self.selenium.execute_script('return arguments[0].validity', elem)

    def get_valid(self, elem):
        val = self.get_validity(elem)
        return val['valid']

    def assertDisplayed(self, elem):
        if isinstance(elem, str):
            elem = self.find(elem)
        self.assertTrue(elem.is_displayed())

    def assertNotDisplayed(self, elem):
        if isinstance(elem, str):
            elem = self.find(elem)
        self.assertFalse(elem.is_displayed())

    def assertClass(self, elem, cls):
        """Assert that an element has a CSS class."""

        self.assertIn(cls, self.get_classes(elem))

    def assertNotClass(self, elem, cls):
        """Assert that an element does **not** have a CSS class."""

        self.assertNotIn(cls, self.get_classes(elem))

    def assertCSSBorderColor(self, elem, color):
        """Assert that an element has a given border color."""

        self.assertEqual(elem.value_of_css_property('border-right-color'), color)
        self.assertEqual(elem.value_of_css_property('border-left-color'), color)
        self.assertEqual(elem.value_of_css_property('border-top-color'), color)
        self.assertEqual(elem.value_of_css_property('border-bottom-color'), color)

    def assertNotValidated(self, fg, elem):
        """Assert that a Bootstrap input element is not validated."""

        self.assertNotClass(fg, 'was-validated')
        for feedback in fg.find_elements_by_css_selector('.invalid-feedback'):
            self.assertFalse(feedback.is_displayed())

        if self.selenium.switch_to.active_element != elem:  # passed element is not currently active
            self.assertCSSBorderColor(elem, 'rgb(206, 212, 218)')
        else:
            self.assertCSSBorderColor(elem, 'rgb(128, 189, 255)')

    def assertInvalid(self, fg, elem, *errors):
        """Assert that a Bootstrap input element validates as invalid."""

        self.assertClass(fg, 'was-validated')
        errors = set(['invalid-%s' % e for e in errors])
        for feedback in fg.find_elements_by_css_selector('.invalid-feedback'):
            classes = set(self.get_classes(feedback))
            if errors & classes:
                self.assertTrue(feedback.is_displayed(), '.%s is not displayed' % ('.'.join(classes)))
            else:
                self.assertFalse(feedback.is_displayed(), '.%s is displayed' % ('.'.join(classes)))
        self.assertCSSBorderColor(elem, 'rgb(220, 53, 69)')
        self.assertFalse(self.get_valid(elem))

    def assertValid(self, fg, elem):
        """Assert that a Bootstrap input element validates as valid."""

        self.assertClass(fg, 'was-validated')
        for feedback in fg.find_elements_by_css_selector('.invalid-feedback'):
            self.assertFalse(feedback.is_displayed())
        self.assertCSSBorderColor(elem, 'rgb(40, 167, 69)')
        self.assertTrue(self.get_valid(elem))


class TestCase(HomepageTestCaseMixin, DjangoTestCase):
    pass


class SeleniumTestCase(SeleniumMixin, HomepageTestCaseMixin, StaticLiveServerTestCase):
    pass
