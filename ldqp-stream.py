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

import sys
import socket
from threading import *

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

parser = argparse.ArgumentParser(description='Etude des requêtes')
parser.add_argument("-g", "--gap", type=int, default=60, dest="gap", help="Gap in minutes (60 by default)")

args = parser.parse_args()

ldqp = LDQP_XML(dt.timedelta(minutes= args.gap))
parser = etree.XMLParser(recover=True, strip_cdata=True)

# Socket server in python using select function
 
HOST = '127.0.0.1'   # Symbolic name meaning all available interfaces
PORT = 5002 # Arbitrary non-privileged port
 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print ('Socket created')
 
#Bind socket to local host and port
try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print ('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
    sys.exit()
     
print ('Socket bind complete')
 
#Start listening on socket
s.listen(10)
print ('Socket now listening')
 
#Function for handling connections. This will be used to create threads
def clientthread(conn):
    #Sending message to connected client
    #conn.send('Welcome to the server. Type something and hit enter\n') #send only takes string
     
    #infinite loop so that function do not terminate and thread do not end.
    while True:
         
        #Receiving from client
        mess = conn.recv(2048)
        data = mess.decode("utf-8")
        print('received:',data)

        if not data: 
            break
        else:
            try:
                tree = etree.parse(StringIO(data))
                root = tree.getroot()
                print('xml:',root.tag )                
            except Exception as e:
                print('Exception',e)
                print('About:',data)


        #conn.sendall(reply)
     
    #came out of loop
    conn.close()
    print('end thread')
 
#now keep talking with the client
while 1:
    #wait to accept a connection - blocking call
    conn, addr = s.accept()
    print ('Connected with ' + addr[0] + ':' + str(addr[1]))
    t = Thread(target=clientthread ,args=(conn,))
    t.start()
 
s.close()
ldqp.stop()

print('Fin')
