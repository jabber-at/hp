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

import configparser

from fabric.api import local
from fabric.api import run
from fabric.api import task


@task
def deploy(section):
    config = configparser.ConfigParser()
    config.read('fab.conf')
    config = config[section]

    host = config.get('host')
    path = config.get('path')
    venv = config.get('virtualenv', path).rstrip('/')

    ssh = lambda c: local('ssh %s %s' % (host, c))
    python = lambda c: ssh('%s/bin/python %s' % (venv, c))
    manage = lambda c: python('%s/hp/manage.py %s' % (path, c))

    local('git push origin master')
    manage('migrate')
    manage('collectstatic --noinput')
    ssh('touch /etc/uwsgi-emperor/vassals/%s.ini' % section)
