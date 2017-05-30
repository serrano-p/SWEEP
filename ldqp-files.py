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

import ldqp

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

for (no,file) in enumerate(file_set):
    ip = '193.52.19.26'
    node_log = makeLog('lift2@193.52.19.26')
    ldqp.startSession()
    otree = etree.parse(file, parser)
    for x in otree.getroot():
        if x.tag == 'entry': 
            x.attrib['client'] = ip
        ldqp.put(x)
    ldqp.endSession()
    i = 1
    res = resQueue.get()
    while res != None:
        i += 1
        addBGP(str(no)+str(i), res, node_log)
        res = ldqp.get()
    file_lift = file[:-4]+'-ldqp.xml'
    save(node_log, file_lift)

ldqp.stop()

# print('Arrêt des processus d' 'analyse')
# ps.stop()

print('Fin')
