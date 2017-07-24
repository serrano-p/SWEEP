#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
"""
Application to test request on SPARQL or TPF server
"""
#    Copyright (C) 2017 by
#    Emmanuel Desmontils <emmanuel.desmontils@univ-nantes.fr>
#    Patricia Serrano-Alvarado <patricia.serrano-alvarado@univ-nantes.fr>
#    All rights reserved.
#    GPL v 2.0 license.

import multiprocessing as mp
from queue import Empty
import os

import datetime as dt
import iso8601 # https://pypi.python.org/pypi/iso8601/     http://pyiso8601.readthedocs.io/en/latest/

import re
import argparse

from tools.tools import *

from tools.ProcessSet import *
from tools.Stat import *

from lxml import etree  # http://lxml.de/index.html#documentation
from lib.bgp import *

from ldqp import *

#==================================================

parser = argparse.ArgumentParser(description='Etude des requêtes')
parser.add_argument('files', metavar='file', nargs='+',
                    help='files to analyse')
parser.add_argument("-p", "--proc", type=int, default=mp.cpu_count(), dest="nb_processes",
                    help="Number of processes used (%d by default)" % mp.cpu_count())

parser.add_argument("-g", "--gap", type=int, default=60, dest="gap", help="Gap in minutes (60 by default)")

args = parser.parse_args()
file_set = args.files
current_dir = os.getcwd()

# nb_processes = args.nb_processes
# print('Lancement des %d processus d\'analyse' % nb_processes)
# ps = ProcessSet(nb_processes, analysis)
# ps.start()

ldqp = LDQP_XML(dt.timedelta(minutes= args.gap))
parser = etree.XMLParser(recover=True, strip_cdata=True)

old_rep = ''
old_ip = ''
no = 0
for file in file_set:
    if existFile(file):
        no += 1
        t = file.split('/')
        n = len(t)
        m = re.search('\Atraces_(?P<ip>.*)-be4dbp-tested-TPF-ranking\Z',t[n-2])
        ip = m.group('ip')
        rep = '/'.join(t[:-2])
        name = t[n-1]

        if ip != old_ip:
            if old_ip != '': 
                ldqp.endSession()
                i = 1
                res = ldqp.get()
                while res != None:
                    i += 1
                    addBGP(str(no)+str(i), res, node_log)
                    res = ldqp.get()
                save(node_log, file_lift)
            if not (os.path.isdir(rep)):
                os.makedirs(rep)
            old_rep = rep
            old_ip = ip
            file_lift = old_rep+'/'+old_ip+'-ldqp.xml'
            node_log = makeLog(ip)
            ldqp.startSession()
        print('Analyse de ',file)
        otree = etree.parse(file, parser)
        for x in otree.getroot():
            if x.tag == 'entry': 
                x.attrib['client'] = ip
            ldqp.put(x)

if old_ip != '': 
    ldqp.endSession()
    i = 1
    res = ldqp.get()
    while res != None:
        i += 1
        addBGP(str(no)+str(i), res, node_log)
        res = ldqp.get()
    save(node_log, file_lift)


ldqp.stop()

# print('Arrêt des processus d' 'analyse')
# ps.stop()

print('Fin')
