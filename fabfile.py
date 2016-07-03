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

import configparser

from fabric.api import local
from fabric.api import task

from fabric_webbuilders import BuildBootstrapTask

# Currently not working because of general incompetence of the NodeJS community.
#build_jquery = BuildJqueryTask(
#    excludes='-deprecated,-dimensions',
#    dest_dir='hp/core/static/lib/jquery/',
#    version='2.1.3'
#)
build_bootstrap = BuildBootstrapTask(
    config='hp/core/static/bootstrap-config.json',
    dest_dir='hp/core/static/lib/bootstrap/',
    version='~3'
)

@task
def deploy(section):
    """Deploy current master."""
    config = configparser.ConfigParser()
    config.read('fab.conf')
    config = config[section]

    host = config.get('host')
    path = config.get('path')
    venv = config.get('virtualenv', path).rstrip('/')

    ssh = lambda c: local('ssh %s %s' % (host, c))
    sudo = lambda c: ssh('sudo sh -c \'"%s"\'' % c)
    python = lambda c: sudo('%s/bin/python %s' % (venv, c))
    pip = lambda c: sudo('%s/bin/pip %s' % (venv, c))
    manage = lambda c: python('%s/hp/manage.py %s' % (path, c))

    local('git push origin master')
    sudo('cd %s && git pull origin master' % path)
    pip('install -U -r %s/requirements.txt' % path)
    manage('migrate')
    manage('collectstatic --noinput')
    sudo('touch /etc/uwsgi-emperor/vassals/%s.ini' % section)
