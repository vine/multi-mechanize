import yaml
import sys
import dogapi
import socket
from fabric.api import *
from fabric.colors import *
from fabric.operations import prompt
from fabric.contrib.console import confirm

@task
@runs_once
def package():
    with lcd('../'):
        with settings(hide('stdout', 'stderr'), warn_only=True):
            local('python setup.py sdist --formats=gztar', capture=False)

@task
def deploy():
    with lcd('../'):
        dist = local('python setup.py --fullname', capture=True).strip()
        put('dist/%s.tar.gz' % dist, '/tmp/%s.tar.gz' % dist)

    with cd('/tmp'):
        run('tar xzf /tmp/%s.tar.gz' % dist)
    
    with cd('/tmp/%s' % dist):
        with settings(hide('stdout', 'stderr'), warn_only=True):
            sudo('python /tmp/%s/setup.py install' % dist)
    sudo('rm -Rf /tmp/%s' % dist)
