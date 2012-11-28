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
from optparse import OptionParser



# list of hosts:ports where multi-mechanize is listening
NODES = [
    '192.168.1.2:9001',
    '192.168.1.3:9001',
]



class Application:
    def __init__(self, root, hosts,clients,run_time,rampup = 30):
        self.hosts = hosts
        self.root = root
        self.clients = int(clients)
        self.run_time = int(run_time)
        self.rampup = int(rampup)
        self.num_clients = (self.clients / len(self.hosts))
        self.root.geometry('%dx%d%+d%+d' % (600, 400, 100, 100))
        self.root.title('Multi-Mechanize Grid Controller')

        Tkinter.Button(self.root, text='List Nodes', command=self.list_nodes, width=15,).place(x=5, y=5)
        Tkinter.Button(self.root, text='Check Tests', command=self.check_servers, width=15,).place(x=5, y=35)
        Tkinter.Button(self.root, text='Get Project Names', command=self.get_project_names, width=15).place(x=5, y=65)
        Tkinter.Button(self.root, text='Get Configs', command=self.get_configs, width=15).place(x=5, y=95)
        Tkinter.Button(self.root, text='Load Config File', command=self.loadfile_config, width=15).place(x=5, y=125)
        Tkinter.Button(self.root, text='Get Results', command=self.get_results, width=15).place(x=5, y=155)
        Tkinter.Button(self.root, text='Gen Config', command=self.generate_config, width=15).place(x=5, y=185)
        Tkinter.Button(self.root, text='Push Config', command=self.push_config, width=15).place(x=5, y=215)
        Tkinter.Button(self.root, text='Run Tests', command=self.run_tests, width=15).place(x=5, y=245)

        self.text_box = ScrolledText.ScrolledText(self.root, width=59, height=24, font=('Helvetica', 9))
        self.text_box.place(x=162, y=5)


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
            except socket.error:
                self.text_box.insert(Tkinter.END, 'can not make connection to: %s:%s\n' % (host, port))


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


    def generate_config(self):
        self.clear_window()
        run_time, rampup, num_clients = self.run_time,self.rampup,self.num_clients
        config_template=string.Template("""        
[global]
run_time = $run_time
rampup = $rampup
results_ts_interval = 10
progress_bar = off
console_logging = off
xml_report = off

[user_group-1]
threads = $num_clients
script = apiclient.py
        """)
        config = config_template.substitute(locals())
        self.text_box.insert(Tkinter.END, config )
        self.config = config
        self.text_box.insert(Tkinter.END, "Config Stored in Memory, click Push to update")


    def get_results(self):
        self.clear_window()
        for host, port in self.hosts:
            server = xmlrpclib.ServerProxy('http://%s:%s' % (host, port))
            try:
                results = server.get_results()
                self.text_box.insert(Tkinter.END, '%s:%s results:\n%s\n\n\n' % (host, port, results))
            except socket.error:
                self.text_box.insert(Tkinter.END, 'can not make connection to: %s:%s\n' % (host, port))


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
        for host, port in self.hosts:
            server = xmlrpclib.ServerProxy('http://%s:%s' % (host, port))
            try:
                is_running = server.check_test_running()
                self.text_box.insert(Tkinter.END, '%s:%s test running:\n%s\n\n' % (host, port, is_running))
            except socket.error:
                self.text_box.insert(Tkinter.END, 'can not make connection to: %s:%s\n' % (host, port))


def usage():
    print "Usage: "+sys.argv[0]+"--nodes=num --rampup=num --clients=num --run_time=num"

def main():
    parser = OptionParser()
    parser.add_option("-n", "--nodes", dest="NODES",
                  help="a comma seperated list of host:port")
    parser.add_option("-c", "--clients", dest="clients",
                  help="Total Number of clients")
    parser.add_option("-t", "--run_time", dest="run_time",
                  help="Runtime duration in seconds")
    parser.add_option("-r", "--rampup", dest="rampup",
                  help="Duration to start total number of clients")
    (options, args) = parser.parse_args()
    hosts = [(host_port.split(':')[0], host_port.split(':')[1]) for host_port in options.NODES.split(',')]
    root = Tkinter.Tk()
    app = Application(root,hosts,options.clients,options.run_time,options.rampup)
    root.mainloop()


if __name__ == '__main__':
    main()

