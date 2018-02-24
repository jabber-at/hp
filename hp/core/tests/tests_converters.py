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
# You should have received a copy of the GNU General Public License along with this project. If
# not, see <http://www.gnu.org/licenses/>.

from datetime import date

from ..converters import DateConverter
from .base import TestCase


class DateConverterTests(TestCase):
    def test_basic(self):
        converter = DateConverter()
        self.assertEqual(converter.to_python('2017-12-12'), date(2017, 12, 12))
        self.assertEqual(converter.to_python('2017-01-12'), date(2017, 1, 12))
        self.assertEqual(converter.to_python('2017-01-01'), date(2017, 1, 1))

    def test_errors(self):
        converter = DateConverter()

        with self.assertRaises(ValueError):
            converter.to_python('2017-13-12')
        with self.assertRaises(ValueError):
            converter.to_python('2017-13-32')
        with self.assertRaises(ValueError):
            converter.to_python('2017-02-30')
