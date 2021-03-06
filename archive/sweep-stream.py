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
import socket
# from tools.Socket import *
from threading import *

import multiprocessing as mp

import datetime as dt
import iso8601 # https://pypi.python.org/pypi/iso8601/     http://pyiso8601.readthedocs.io/en/latest/

import re
import argparse

from tools.tools import *

from lxml import etree  # http://lxml.de/index.html#documentation
from lib.bgp import *

from io import StringIO

from ldqp import *

#==================================================

def processResults(ldqp):
    i = 0
    try:
        res = ldqp.get()
        while res != None:
            i += 1
            res.print()
            res = ldqp.get()
    except KeyboardInterrupt:
        pass

#==================================================

#Function for handling connections. This will be used to create threads
def clientthread(conn, ldqp, parser):
    #Sending message to connected client
    #conn.send('Welcome to the server. Type something and hit enter\n') #send only takes string
    (ip,port) = conn.getpeername() 
    while True:   
        #Receiving from client
        try:
            mess = conn.recv(2048)
            data = mess.decode("utf-8")
            # print('received data:',data)
            if not data: 
                break
            else:
                try:
                    tree = etree.parse(StringIO('<msg>'+data+'</msg>'), parser)
                    root = tree.getroot()
                    for x in root: 
                        client = x.get('client')
                        if client is not None:
                            x.set('client',str(ip) )
                        ldqp.put(x)               
                except Exception as e:
                    print('Exception',e)
                    print('About:',data)
                    conn.send(b'0')
                    break
            conn.send(b'1')
        except KeyboardInterrupt:
            break
    #came out of loop
    conn.close()
    # print('end thread')

#==================================================


def processIn(ldqp, host,port):
    parser = etree.XMLParser(recover=True, strip_cdata=True)
    ldqp.startSession()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host,port))
    except socket.error as msg:
        print ('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
        sys.exit()   
    print ('Socket bind complete')
    s.listen(10)
    print ('Socket now listening')

    try:
        while 1:
            (conn, addr) = s.accept()
            t = Thread(target=clientthread ,args=(conn,ldqp, parser))
            t.start()
    except KeyboardInterrupt:
        s.close()
        ldqp.endSession() 

#==================================================
#==================================================
#==================================================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Linked Data Query Profiler (for a modified TPF server)')
    # parser.add_argument('files', metavar='file', nargs='+',help='files to analyse')
    parser.add_argument("-g", "--gap", type=float, default=60, dest="gap", help="Gap in minutes (60 by default)")
    parser.add_argument("--port", type=int, default=5002, dest="port", help="Port (5002 by default)")
    parser.add_argument("--host", default='127.0.0.1', dest="host", help="Host ('127.0.0.1' by default)")
    parser.add_argument("-to", "--timeout", type=float, default=0, dest="timeout",
                        help="TPF server Time Out in minutes (%d by default). If '-to 0', the timeout is the gap." % 0)
    parser.add_argument("-o","--optimistic", help="BGP time is the last TP added (False by default)",
                    action="store_true",dest="doOptimistic")

    args = parser.parse_args()

    ldqp = LDQP_XML(dt.timedelta(minutes= args.gap))
    resProcess = mp.Process(target=processResults, args=(ldqp,))
    inProcess = mp.Process(target=processIn, args=(ldqp,args.host,args.port) )

    if args.timeout > 0 : ldqp.setTimeout(dt.timedelta(minutes= args.timeout))
    if args.doOptimistic: ldqp.swapOptimistic()

    try:
        inProcess.start()
        resProcess.start()
        while 1:
            time.sleep(60)
    except KeyboardInterrupt:    
        ldqp.stop()
        resProcess.join()
        inProcess.join()
    print('Fin')
