#!/usr/bin/env python
from __future__ import division
import boto
import pprint
import time
import socket
import sys
import yaml
from subprocess import call
from fabric.api import *
from fabric.colors import *
from fabric.operations import prompt
from fabric.contrib.console import confirm
from boto.ec2.connection import EC2Connection


class AWS(object):
	def __init__(self,access_id,secret_key,region='us-east-1',host_suffix='.stg.vine.co',host_prefix='loadtest'):
		self.conn = EC2Connection(access_id, secret_key)
		self.host_list = []
		self.count=1
		self.host_suffix = host_suffix
		self.host_prefix = host_prefix

	def start_instances(self,AMI,SIZE,GROUPS,KEY,NUM=1):
		self.reservation = self.conn.run_instances(
	        AMI,
	        min_count=NUM,
	        max_count=NUM,
	        key_name=KEY,
	        instance_type=SIZE,
	        security_groups=GROUPS)
		for instance in self.reservation.instances:
			print "Waiting for instances to launch"
			status = instance.update()
			while status == "pending":
				time.sleep(10)
				status = instance.update()
			hostname = self.host_prefix+str(self.count)+self.host_suffix
			self.create_tags([ str(instance.id) ],{"Name": hostname })
			self.host_list.append(instance.public_dns_name)
		return self.reservation.instances

	def create_tags(self,instance_id,tags={}):
		return self.conn.create_tags(instance_id,tags)

	def get_host_list(self):
		return self.host_list
 
class Fab(object):
	def __init__(self,user,key = "~/.ssh/id_rsa"):
		env.user = user
		env.key_filename = key
		env.hosts = []
		self.run_list = [ self.apt_update,self.install_progs,self.install_deps,self.package,self.deploy,self.build_newproject,self.start_mech ]

	def config_nodes(self,hosts=env.hosts):
		if len(hosts) == 0:
			raise Exception("Fab: No Hosts Specified")
		for task in self.run_list:
			for host in hosts:
				env.host_string = host
				task()

	def addHost(self,host):
		print "Added host:"+host
		env.hosts.append(host)
		print "HOSTS:"+str(env.hosts)

	def getHosts(self):
		return env.hosts

	def apt_update(self):
		sudo("apt-get -y update",pty=False)
		sudo("apt-get -y update",pty=False)

	def install_progs(self):
		sudo("apt-get -y install python-pip",pty=False)
		sudo("apt-get -y install screen",pty=False)
		sudo("apt-get -y install python-gevent",pty=False)
		sudo("apt-get -y install python-matplotlib",pty=False)

	def install_deps(self):
		sudo("pip install requests")

	def package(self):
	    with lcd('../'):
	        with settings(hide('stdout', 'stderr'), warn_only=True):
	            local('python setup.py sdist --formats=gztar', capture=False)

	def deploy(self):
	    with lcd('../'):
	        dist = local('python setup.py --fullname', capture=True).strip()
	        put('dist/%s.tar.gz' % dist, '/tmp/%s.tar.gz' % dist)

	    with cd('/tmp'):
	        run('tar xzf /tmp/%s.tar.gz' % dist,pty=False)
	    
	    with cd('/tmp/%s' % dist):
	        with settings(hide('stdout', 'stderr'), warn_only=True):
	            sudo('python /tmp/%s/setup.py install' % dist,pty=False)
	    sudo('rm -Rf /tmp/%s' % dist,pty=False)

	def build_newproject(self):
			run('multimech-newproject ~/vineproject',pty=False)

	def start_mech(self):
		with cd('~/'):
			sudo("screen -dmS multimech multimech-run -b 0.0.0.0 -p 8001 vineproject",pty=False)

def get_hoststring(hosts):
	string = ""
	for i in xrange(len(hosts)):
		string += hosts[i]+":8001"
		if (i+1) != len(hosts):
			string += ","
	return string

def isClosed(ip,port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
		s.connect((ip, int(port)))
		s.shutdown(2)
		return False
    except:
		return True

def launchAwsNodes(config):
	conn = AWS(config['aws']['access_id'],config['aws']['secret_key'])
	num_float = round(float((config['test_config']['clients'] / config['test_config']['clients_per_node'])))
	if num_float < 1:
		num = 1
	else:
		num = int(str(num_float).split('.')[0])
	instances = conn.start_instances(config['aws']['ami'],config['aws']['node_size'],config['aws']['groups'],config['aws']['ssh_key'],num)
	return { 'conn': conn,'instances': instances, 'num_nodes': num}

def print_execstring(launch_array):
	string = ""
	append = " "
	for i in xrange(len(launch_array)):
		if i == len(launch_array):
			append = ""
		string += "%s%s" % (launch_array[i],append)
	print string

def launchGridUI(config,aws_res):
	test_config = config['test_config']
	client_float = round(float((test_config['clients'] / aws_res['num_nodes'])))
	num_clients = int(str(client_float).split('.')[0])
	rampup = test_config['rampup']
	run_time = test_config['run_time']
	script = test_config['script']
	results_dir = test_config['results_dir']
	launch_array = ['multimech-gridgui', '--nodes=%s ' % (get_hoststring(aws_res['conn'].get_host_list())), '--clients=%s' % (num_clients), '--rampup=%s' % rampup, '--run_time=%s' % run_time,'--script="%s"' % script, '--results_dir=%s' % results_dir]
	call(launch_array)
	print "Exec Grid UI again with this string:"
	print_execstring(launch_array)


def wait_for_ssh(hosts):
	for host in hosts:
		print "%s Waiting for ssh" % host
		while isClosed(host,'22'):
			time.sleep(1)
		print "%s SSH Ready." % host

def main():
	config = yaml.load(open('config.yaml'))
	aws_res = launchAwsNodes(config)
	wait_for_ssh(aws_res['conn'].get_host_list())
	fab = Fab(config['test_config']['ssh_user'],config['test_config']['ssh_key'])
	fab.config_nodes(aws_res['conn'].get_host_list())
	launchGridUI(config,aws_res)	
	

if __name__ == '__main__':
	main()
