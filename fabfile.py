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
from datetime import datetime

from fabric.api import local
from fabric.api import task
from fabric.tasks import Task

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
manage = lambda h, v, p, c: python(h, v, '%s/hp/manage.py %s' % (p, c))


class DeploymentTaskMixin(object):
    def sudo(self, cmd, chdir=''):
        if chdir:
            return local('ssh %s sudo sh -c \'"cd %s && %s"\'' % (self.host, chdir, cmd))
        else:
            return local('ssh %s sudo %s' % (self.host, cmd))

    def sg(self, cmd, chdir=''):
        if not self.group:
            return self.sudo(cmd, chdir=chdir)

        sg_cmd = 'ssh %s sudo sg %s -c' % (self.host, self.group)
        if chdir:
            return local('%s \'"cd %s && %s"\'' % (sg_cmd, chdir, cmd))
        else:
            return local('%s \'"%s"\'' % (sg_cmd, cmd))

    def pip(self, cmd):
        return self.sudo('%s/bin/pip %s' % (self.venv, cmd))

    def manage(self, cmd):
        return self.sudo('%s/bin/python hp/manage.py %s' % (self.venv, cmd), chdir=self.path)


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


class DeployTask(DeploymentTaskMixin, Task):
    """Deploy current master."""
    def run(self, section='DEFAULT'):
        local('flake8 hp')

        config = configfile[section]
        self.hostname = config.get('hostname')
        self.host = config.get('host')
        self.path = config.get('path')
        self.venv = config.get('home', self.path).rstrip('/')

        local('git push origin master')
        self.sudo('git pull origin master', chdir=self.path)
        self.pip('install -U pip setuptools mysqlclient')
        self.pip('install -U -r %s/requirements.txt' % self.path)

        self.sudo('mkdir -p /var/www/%s/static /var/www/%s/media' % (self.hostname, self.hostname))

        self.manage('migrate')
        self.manage('collectstatic --noinput')
        self.manage('compilemessages -l de')

        # restart uwsgi
        self.sudo('touch /etc/uwsgi-emperor/vassals/hp.ini')

        # reload apache
        self.sudo('systemctl reload apache2')

        # handle celery
        self.sudo('systemctl daemon-reload')
        self.sudo('systemctl restart hp-celery')

        local('git tag %s/%s' % (self.hostname, datetime.utcnow().strftime('%Y%m%d-%H%M%S')))
        local('git push --tags')

deploy = DeployTask()
