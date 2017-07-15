#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
"""
Application ...
"""
#    Copyright (C) 2017 by
#    Emmanuel Desmontils <emmanuel.desmontils@univ-nantes.fr>
#    Patricia Serrano-Alvarado <patricia.serrano-alvarado@univ-nantes.fr>
#    All rights reserved.
#    GPL v 2.0 license.

# import sys
# from tools.Socket import *
from threading import *
import multiprocessing as mp

# import multiprocessing as mp

import datetime as dt
import iso8601 # https://pypi.python.org/pypi/iso8601/     http://pyiso8601.readthedocs.io/en/latest/
import time

from tools.tools import *
from tools.Endpoint import *
from tools.ProcessSet import *
from tools.Stat import *

import json

import requests as http
# http://docs.python-requests.org/en/master/user/quickstart/

# import re
import argparse

from lxml import etree  # http://lxml.de/index.html#documentation
# from lib.bgp import *

#==================================================	
#==================================================

def play(file,nb_processes, server,client,dataset,doValid, sInfo):
    (host,port) = sInfo
    compute_queue = mp.Queue(nb_processes)
    print('Traitement de %s' % file)
    parser = etree.XMLParser(recover=True, strip_cdata=True)
    tree = etree.parse(file, parser)
    #---
    dtd = etree.DTD('http://documents.ls2n.fr/be4dbp/log.dtd')
    assert dtd.validate(tree), '%s non valide au chargement : %s' % (
        file, dtd.error_log.filter_from_errors()[0])
    #---
    print('DTD valide !')

    nbe = 0
    date = 'no-date'
    ip = 'ip-'+tree.getroot().get('ip').split('-')[0]
    for entry in tree.getroot():
        nbe += 1
        if entry.tag == 'entry':
            print('(%d) new entry to add' % nbe)
            # print(entry.tag)
            if nbe == 1:
                date_ref = fromISO(entry.get('datetime'))
                current_date = dt.datetime.now()
                processes = []
                for i in range(nb_processes):
                    p = mp.Process(target=run, args=(compute_queue, server, client, dataset, host,port,doValid))
                    processes.append(p)
                for p in processes:
                    p.start()
            date = fromISO(entry.get('datetime'))
            ide = entry.get('logline')
            valid = entry.get("valid")
            if valid is not None :
                if valid == 'TPF' :
                    compute_queue.put( (nbe, entry.find('request').text, current_date+(date-date_ref) )  )
    if nbe>0: 
        for p in self.processes:
            compute_queue.put(None)
        for p in self.processes:
            p.join()

def run(inq, server, client, dataset, host, port, doPR):
    sp = TPFEP(service = server, dataset = dataset)#, clientParams= '-s '+host+':'+str(port)  ) #'http://localhost:5000/lift') 
    sp.setEngine(client) #'/Users/desmontils-e/Programmation/TPF/Client.js-master/bin/ldf-client')
    mss = inq.get()
    while mss is not None:
        (nbe,query,d) = mss
        duration = max(dt.timedelta.resolution, d-dt.datetime.now())
        print('(%d)'%nbe,'Sleep:',duration.total_seconds(),' second(s)')
        time.sleep(duration.total_seconds())
        print('(%d)'%nbe,'Query:',query)
        try:
            if doPR:
                mess = '<query time="'+date2str(dt.datetime.now())+'"><![CDATA['+query+']]></query>'
                url = host+':'+str(port)+'/query'
                print('on:',url)
                s = http.post(url,data={'data':mess})
                print('(%d)'%nbe,'Request posted : ',s.json()['result'])
            try:
                rep = sp.query(query)
                print('(%d)'%nbe,':',rep)
            except Exception as e:
                print('(%d)'%nbe,'Exception execution query... :',e)
                if doPR:
                    url = host+':'+str(port)+'/delquery'
                    s = http.post(url,data={'data':mess})
                    print('(%d)'%nbe,'Request cancelled : ',s.json()['result'])
            mss = inq.get()
        except Exception as e:
            print('Exception qsim run :',e)
            break

#==================================================
#==================================================
#==================================================

TPF_SERVEUR_HOST = 'http://127.0.0.1'
TPF_SERVEUR_PORT = 5000
TPF_SERVEUR_DATASET = 'lift'
TPF_CLIENT = '/Users/desmontils-e/Programmation/TPF/Client.js-master/bin/ldf-client'
SWEEP_SERVEUR_HOST = 'http://127.0.0.1'
SWEEP_SERVEUR_PORT = 5002


parser = argparse.ArgumentParser(description='Linked Data Query simulator (for a modified TPF server)')
parser.add_argument('files', metavar='file', nargs='+', help='files to analyse')
parser.add_argument("--port", type=int, default=SWEEP_SERVEUR_PORT, dest="port", help="SWEEP Port ('"+str(SWEEP_SERVEUR_PORT)+"' by default)")
parser.add_argument("--host", default=SWEEP_SERVEUR_HOST, dest="host", help="SWEEP Host ('"+SWEEP_SERVEUR_HOST+"' by default)")
parser.add_argument("-s","--server", default=TPF_SERVEUR_HOST+':'+str(TPF_SERVEUR_PORT), dest="tpfServer", help="TPF Server ('"+TPF_SERVEUR_HOST+':'+str(TPF_SERVEUR_PORT)+"' by default)")
parser.add_argument("-d", "--dataset", default=TPF_SERVEUR_DATASET, dest="dataset", help="TPF Server Dataset ('"+TPF_SERVEUR_DATASET+"' by default)")
parser.add_argument("-c", "--client", default=TPF_CLIENT, dest="tpfClient", help="TPF Client ('...' by default)")
parser.add_argument("-v", "--valid", default='', dest="valid", action="store_true", help="Do precision/recall")
parser.add_argument("-to", "--timeout", type=float, default=0, dest="timeout",
                    help="TPF server Time Out in minutes (%d by default). If '-to 0', the timeout is the gap." % 0)
parser.add_argument("-p", "--proc", type=int, default=mp.cpu_count(), dest="nb_processes",
                    help="Number of processes used (%d by default)" % mp.cpu_count())

args = parser.parse_args()

# http://localhost:5000/lift : serveur TPF LIFT (exemple du papier)
# http://localhost:5001/dbpedia_3_9 server dppedia si : ssh -L 5001:172.16.9.3:5001 desmontils@172.16.9.15
print('Start simulating with %d processes'%args.nb_processes)
file_set = args.files
for file in file_set:
    if existFile(file):
    	play(file,args.nb_processes, args.tpfServer, args.tpfClient, args.dataset,args.valid, (args.host,args.port)  )
