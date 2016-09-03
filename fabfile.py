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

configfile = configparser.ConfigParser({
    'home': '/usr/local/home/hp',
    'path': '%(home)s/hp',
    'upstream': 'https://github.com/jabber-at/hp',
})
configfile.read('fab.conf')

ssh = lambda h, c: local('ssh %s %s' % (h, c))
sudo = lambda h, c: ssh(h, 'sudo sh -c \'"%s"\'' % c)
python = lambda h, v, c: sudo(h, '%s/bin/python %s' % (v, c))
pip = lambda h, v, c: sudo(h, '%s/bin/pip %s' % (v, c))
manage = lambda c: python('%s/hp/manage.py %s' % (path, c))

@task
def setup(section):
    config = configfile[section]
    local('git push origin master')
    host = config.get('host')
    home = config.get('home')
    path = config.get('path')
    venv = config.get('venv', home).rstrip('/')

    upstream = config.get('upstream')

    sudo(host, 'git clone %s %s' % (upstream, path))
    sudo(host, 'virtualenv -p /usr/bin/python3 %s' % venv)
    pip(host, venv, 'install pip setuptools mysqlclient')
    pip(host, venv, 'install -U -r %s/requirements.txt' % path)

    sudo(host, 'ln -s %s/files/systemd/hp-celery.tmpfiles /etc/tmpfiles.d/hp-celery.conf' % path)
    sudo(host,
         'ln -s %s/files/systemd/hp-celery.service /etc/systemd/system/hp-celery.service' % path)
    sudo(host, 'ln -s %s/files/systemd/hp-celery.conf /etc/conf.d/' % path)


@task
def deploy(section):
    """Deploy current master."""
    config = configfile[section]
    hostname = config.get('hostname')
    host = config.get('host')
    path = config.get('path')
    venv = config.get('home', path).rstrip('/')

    local('git push origin master')
    sudo('cd %s && git pull origin master' % path)
    pip('install -U pip setuptools mysqlclient')
    pip('install -U -r %s/requirements.txt' % path)
    manage('migrate')
    manage('collectstatic --noinput')
    manage('compilemessages -l de')
    sudo('touch /etc/uwsgi-emperor/vassals/%s.ini' % section)
    sudo('mkdir -p /var/www/%s/static /var/www/%s/media' % (hostname, hostname)

    # handle celery
    sudo('systemctl daemon-reload')
    sudo('systemctl restart hp-celery')
