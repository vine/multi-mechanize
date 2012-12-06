#!/usr/bin/env python
#
#  Copyright (c) 2010-2012 Corey Goldberg (corey@goldb.org)
#  License: GNU LGPLv3
#
#  This file is part of Multi-Mechanize | Performance Test Framework
#


import SimpleXMLRPCServer
import socket
import threading
import multiprocessing

class TestThread(threading.Thread):
    def __init__(self,project_name,cmd_opts,run_callback,rpc_self):
        super(TestThread, self).__init__()
        self.project_name = project_name
        self.cmd_opts = cmd_opts
        self.rpc_self = rpc_self
        self.run_callback = run_callback

    def run(self):
        self.run_callback(self.project_name, self.cmd_opts,self.rpc_self)

def launch_rpc_server(bind_addr, port, project_name, cmd_opts,run_callback):
    server = SimpleXMLRPCServer.SimpleXMLRPCServer((bind_addr, port), logRequests=False)
    server.register_instance(RemoteControl(project_name,cmd_opts,run_callback))
    server.register_introspection_functions()
    print '\nMulti-Mechanize: %s listening on port %i' % (bind_addr, port)
    print 'waiting for xml-rpc commands...\n'
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


class RemoteControl(object):
    def __init__(self, project_name, cmd_opts,run_callback):
        self.project_name = project_name
        self.run_callback = run_callback
        self.cmd_opts = cmd_opts
        self.test_running = False
        self.output_dir = None
        self.thread = False

    def run_test(self):
        if self.check_test_running():
            return 'Test Already Running'
        else:
            self.thread = TestThread(self.project_name, self.cmd_opts,self.run_callback,self)
            self.thread.start()
            return 'Test Started'

    def check_test_running(self):
        if self.thread:
            self.thread.join(0.1)
            self.test_running = self.thread.isAlive()
        return self.test_running

    def update_config(self, config):
        with open('%s/config.cfg' % self.project_name, 'w') as f:
            f.write(config)
            return True

    def upload_test(self,content):
        with open('%s/test_scripts/uploaded_test.py' % self.project_name, 'w') as f:
            f.write(content)
            return True        

    def get_config(self):
        with open('%s/config.cfg' % self.project_name, 'r') as f:
            return f.read()

    def get_project_name(self):
        return self.project_name

    def get_results(self):
        if self.output_dir is None:
            return 'Results Not Available'
        else:
            with open(self.output_dir + 'results.csv', 'r') as f:
                return f.read()
