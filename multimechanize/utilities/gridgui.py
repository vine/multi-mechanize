#!/usr/bin/env python
#
#  Copyright (c) 2010 Corey Goldberg (corey@goldb.org)
#  License: GNU LGPLv3
#
#  This file is part of Multi-Mechanize | Performance Test Framework
#


"""
Multi-Mechanize Grid Controller
sample gui application for controlling multi-mechanize instances via the remote management api
"""


import socket
import ScrolledText
import Tkinter
import tkFileDialog
import xmlrpclib
import sys
import string
import re
import os
import time
import multimechanize.results as results
from optparse import OptionParser



# list of hosts:ports where multi-mechanize is listening
NODES = [
    '192.168.1.2:9001',
    '192.168.1.3:9001',
]



class Application:
    def __init__(self, root, hosts,clients,run_time,rampup = 30,script = "apiclient.py",groups = 1,results_dir = "/tmp/multimech/"):
        self.hosts = hosts
        self.root = root
        self.groups = groups
        self.clients = int(clients)
        self.run_time = int(run_time)
        self.script = script        
        self.rampup = int(rampup)
        self.num_clients = self.clients
        self.root.geometry('%dx%d%+d%+d' % (600, 400, 100, 100))
        self.root.title('Multi-Mechanize Grid Controller')
        self.results_ts_interval = 10
        self.progress_bar = "on"
        self.console_logging = "off"
        self.xml_report = "off"
        self.start_time = 0
        self.results_directory = results_dir
        if not re.match('/$',self.results_directory):
            self.results_directory += "/"
        Tkinter.Button(self.root, text='List Nodes', command=self.list_nodes, width=15,).place(x=5, y=5)
        Tkinter.Button(self.root, text='Check Tests', command=self.check_servers, width=15,).place(x=5, y=35)
        Tkinter.Button(self.root, text='Get Project Names', command=self.get_project_names, width=15).place(x=5, y=65)
        Tkinter.Button(self.root, text='Get Configs', command=self.get_configs, width=15).place(x=5, y=95)
        Tkinter.Button(self.root, text='Load Config File', command=self.loadfile_config, width=15).place(x=5, y=125)
        Tkinter.Button(self.root, text='Upload Test File', command=self.uploadtest_script, width=15).place(x=5, y=155)
        Tkinter.Button(self.root, text='Get Results', command=self.get_results, width=15).place(x=5, y=185)
        Tkinter.Button(self.root, text='Gen Config', command=self.generate_config, width=15).place(x=5, y=215)
        Tkinter.Button(self.root, text='Push Config', command=self.push_config, width=15).place(x=5, y=245)
        Tkinter.Button(self.root, text='Run Tests', command=self.run_tests, width=15).place(x=5, y=275)
        self.text_box = ScrolledText.ScrolledText(self.root, width=59, height=24, font=('Helvetica', 9))
        self.text_box.place(x=162, y=5)
        self.uploadtest_script(initial=True)


    def clear_window(self):
        self.text_box.delete(1.0, Tkinter.END)


    def list_nodes(self):
        self.clear_window()
        for host, port in self.hosts:
            self.text_box.insert(Tkinter.END, '%s:%s\n' % (host, port))


    def run_tests(self):
        self.clear_window()
        for host, port in self.hosts:
            server = xmlrpclib.ServerProxy('http://%s:%s' % (host, port))
            try:
                status = server.run_test()
                self.text_box.insert(Tkinter.END, '%s:%s:\n%s\n\n\n' % (host, port, status))
                self.start_time = time.time()
            except socket.error:
                self.text_box.insert(Tkinter.END, 'can not make connection to: %s:%s\n' % (host, port))

    def time_remaining(self):
        if not self.start_time == 0:
            time_left = self.run_time - (time.time() - self.start_time)
            self.text_box.insert(Tkinter.END, '%s seconds left until test complete' % (time_left))



    def get_configs(self):
        self.clear_window()
        for host, port in self.hosts:
            server = xmlrpclib.ServerProxy('http://%s:%s' % (host, port))
            try:
                config = server.get_config()
                self.text_box.insert(Tkinter.END, '%s:%s config:\n%s\n\n\n' % (host, port, config))
            except socket.error:
                self.text_box.insert(Tkinter.END, 'can not make connection to: %s:%s\n' % (host, port))


    def loadfile_config(self):
        self.clear_window()
        f = tkFileDialog.askopenfile(parent=self.root, initialdir='./', title='Select a Config File')
        self.config = f.read()

    def uploadtest_script(self,initial=False):
        self.clear_window()
        if initial and os.path.exists(self.script):
            f = open(self.script, 'r')
        else:
            f = tkFileDialog.askopenfile(parent=self.root, initialdir='./', title='Select a Config File')
        self.test_script = f.read()
        for host, port in self.hosts:
            server = xmlrpclib.ServerProxy('http://%s:%s' % (host, port))
            try:
                status = server.upload_test(self.test_script)
                self.text_box.insert(Tkinter.END, '%s:%s config updated:\n%s\n\n' % (host, port, status))
                self.script = "uploaded_test.py"
                self.generate_config()
            except socket.error:
                self.text_box.insert(Tkinter.END, 'can not make connection to: %s:%s\n' % (host, port))

    def push_config(self):
        self.clear_window()
        try:
            self.config
        except AttributeError:
            self.text_box.insert(Tkinter.END, 'ERROR: Please Generate or Load Config')
            pass
        for host, port in self.hosts:
            server = xmlrpclib.ServerProxy('http://%s:%s' % (host, port))
            try:
                status = server.update_config(self.config)
                self.text_box.insert(Tkinter.END, '%s:%s config updated:\n%s\n\n' % (host, port, status))
            except socket.error:
                self.text_box.insert(Tkinter.END, 'can not make connection to: %s:%s\n' % (host, port))

    def user_groups(self):
        groups = {}
        for i in xrange(self.groups):
            group_name = "user_group"+str(i)
            group = { 
                group_name: {
                    "threads": self.num_clients / self.groups,
                    "script": self.script
                    }
            }
            groups.update(group)
        return groups

    def generate_config(self):
        self.clear_window()
        run_time, rampup, num_clients = self.run_time,self.rampup,self.num_clients
        global_config = { "global":
                            {
                                "run_time":self.run_time,
                                "rampup": self.rampup,
                                "results_ts_interval": self.results_ts_interval,
                                "progress_bar": self.progress_bar,
                                "console_logging": self.console_logging,
                                "xml_report":self.xml_report
                            }}
        gen_config = self.user_groups()
        gen_config.update(global_config)
        config = ""
        for k,v in gen_config.items():
            config += "["+str(k)+"]\n"
            if isinstance(v,dict):
                for name,value in v.items():
                    config += str(name)+" = "+str(value)+"\n"
            config += "\n"
        self.text_box.insert(Tkinter.END, config )
        self.config = config
        self.text_box.insert(Tkinter.END, "Config Stored in Memory, click Push to update")


    def get_results(self):
        self.clear_window()
        self.all_results = ""
        for host, port in self.hosts:
            server = xmlrpclib.ServerProxy('http://%s:%s' % (host, port))
            try:
                results = server.get_results()
                self.text_box.insert(Tkinter.END, '%s:%s results:\n%s\n\n\n' % (host, port, results))
                self.all_results += results
            except socket.error:
                self.text_box.insert(Tkinter.END, 'can not make connection to: %s:%s\n' % (host, port))

        if not os.path.exists(self.results_directory):
            os.makedirs(self.results_directory)
        with open('%sresults.csv' % (self.results_directory), 'w') as f:
            f.write(self.all_results)
        self.generate_html()
        return True

    def generate_html(self):
        self.text_box.insert(Tkinter.END, '\n\nanalyzing results...\n')
        results.output_results(self.results_directory, 'results.csv', self.run_time, self.rampup, self.results_ts_interval)
        self.text_box.insert(Tkinter.END, 'created: %sresults.html\n' % self.results_directory)


    def get_project_names(self):
        self.clear_window()
        for host, port in self.hosts:
            server = xmlrpclib.ServerProxy('http://%s:%s' % (host, port))
            try:
                name = server.get_project_name()
                self.text_box.insert(Tkinter.END, '%s:%s project name:\n%s\n\n' % (host, port, name))
            except socket.error:
                self.text_box.insert(Tkinter.END, 'can not make connection to: %s:%s\n' % (host, port))


    def check_servers(self):
        self.clear_window()
        still_running = False
        for host, port in self.hosts:
            server = xmlrpclib.ServerProxy('http://%s:%s' % (host, port))
            try:
                is_running = server.check_test_running()
                self.text_box.insert(Tkinter.END, '%s:%s test running:\n%s\n\n' % (host, port, is_running))
                still_running = is_running
                self.time_remaining()
            except socket.error:
                self.text_box.insert(Tkinter.END, 'can not make connection to: %s:%s\n' % (host, port))
        return still_running

def usage():
    print "Usage: "+sys.argv[0]+"--nodes=num --rampup=num --clients=num --run_time=num"

def main():

    parser = OptionParser()
    parser.add_option("-n", "--nodes", dest="NODES",
                  help="a comma seperated list of host:port")
    parser.add_option("-c", "--clients", dest="clients",
                  help="Total Number of clients per node")
    parser.add_option("-t", "--run_time", dest="run_time",
                  help="Runtime duration in seconds")
    parser.add_option("-r", "--rampup", dest="rampup",
                  help="Duration to start total number of clients")
    parser.add_option("-s", "--script", dest="script",default="apiclient.py",
                  help="Define script name default apiclient.py")    
    parser.add_option("-g", "--groups", dest="groups",default=1,
                  help="Define number of thread groups per node, default 1")
    parser.add_option("-d","--results_dir", dest="results_dir",default='/tmp/multimech/',
              help="Define where the results appear, default /tmp/multimech/")
    (options, args) = parser.parse_args()
    if not (options.NODES or options.clients or options.run_time or options.rampup):
        parser.error("Required Field Missing!")
    hosts = [(host_port.split(':')[0], host_port.split(':')[1]) for host_port in options.NODES.split(',')]
    root = Tkinter.Tk()
    app = Application(root,hosts,options.clients,options.run_time,options.rampup,script=options.script,groups=int(options.groups),results_dir=options.results_dir)
    root.mainloop()


if __name__ == '__main__':
    main()

