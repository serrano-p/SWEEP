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

# import multiprocessing as mp

import datetime as dt
import iso8601 # https://pypi.python.org/pypi/iso8601/     http://pyiso8601.readthedocs.io/en/latest/
import time

from tools.tools import *
from tools.Endpoint import *

import json

import requests as http
# http://docs.python-requests.org/en/master/user/quickstart/

# import re
import argparse


from lxml import etree  # http://lxml.de/index.html#documentation
# from lib.bgp import *

# from io import StringIO


#==================================================

class Query(object):
	"""docstring for Query"""
	def __init__(self, q, time):
		super(Query, self).__init__()
		self.q = q
		self.time = time

#==================================================	

def queryThread(sInfo, sp, doPR, query,ref):
    duration = query.time - ref
    print('Sleep:',duration.total_seconds(),' second(s)')
    time.sleep(duration.total_seconds())
    print('Query:',query.q)
    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # s.connect(sInfo)
    #(ip,port) = s.getsockname()
    (host,port) = sInfo
    try:
        if doPR:
            mess = '<query time="'+date2str(dt.datetime.now())+'"><![CDATA['+query.q+']]></query>'
            url = host+':'+str(port)+'/query'
            print('on:',url)
            s = http.post(url,data={'data':mess})
            print('Request posted : ',s.json()['result'])
        # 	mess = '<query time="'+date2str(query.time)+'" client="'+str(ip)+'"><![CDATA['+query.q+']]></query>'
        # 	print("Send query:",mess)
        # 	s.send(mess.encode('utf8'))
        # 	rep = s.recv(2048)
        # 	print('ok:',rep)
        print(sp.query(query.q))
    except Exception as e:
        print('Exception',e)

#==================================================

def play(file,sp,doValid, sInfo):
 
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
            date = fromISO(entry.get('datetime'))
            ide = entry.get('logline')
            valid = entry.get("valid")
            if valid is not None :
            	if valid == 'TPF' :
            		query = entry.find('request').text
            		t = Thread(target=queryThread ,args=(sInfo,sp,doValid,Query(query,date),date_ref))
            		t.start()

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
parser.add_argument("-t", "--time", default='', dest="now", help="Time reference (now by default)")
parser.add_argument("-v", "--valid", default='', dest="valid", action="store_true", help="Do precision/recall")
parser.add_argument("-to", "--timeout", type=float, default=0, dest="timeout",
                    help="TPF server Time Out in minutes (%d by default). If '-to 0', the timeout is the gap." % 0)

args = parser.parse_args()

# http://localhost:5000/lift : serveur TPF LIFT (exemple du papier)
# http://localhost:5001/dbpedia_3_9 server dppedia si : ssh -L 5001:172.16.9.3:5001 desmontils@172.16.9.15

sp = TPFEP(service = args.tpfServer, dataset = args.dataset)#, clientParams= '-s '+args.host+':'+str(args.port)  ) #'http://localhost:5000/lift') 
sp.setEngine(args.tpfClient) #'/Users/desmontils-e/Programmation/TPF/Client.js-master/bin/ldf-client')

if args.now =='':
	now = now()
else: now = dt.datetime(args.now)

# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.connect((args.host,args.port))

file_set = args.files
for file in file_set:
    if existFile(file):
    	play(file,sp,args.valid, (args.host,args.port)  )
