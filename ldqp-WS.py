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

import datetime as dt
import argparse
from tools.Endpoint import *
from tools.tools import  *

from flask import Flask, render_template, request, jsonify
# http://flask.pocoo.org/docs/0.12/


class Context(object):
    """docstring for Context"""
    def __init__(self):
        super(Context, self).__init__()
        self.host = '127.0.0.1'
        self.port = 5002
        self.tpfc = TPFEP(service = 'http://localhost:5000/lift') 
        self.tpfc.setEngine('/Users/desmontils-e/Programmation/TPF/Client.js-master/bin/ldf-client')

    def setLDQPServer(self, host, port):
        self.host = host
        self.port = port

    def setTPFClient(self,tpfc):
        self.tpfc = tpfc
        
ctx = Context()

#==================================================

# Initialize the Flask application
app = Flask(__name__)
 
# This route will show a form to perform an AJAX request
# jQuery is loaded to execute the request and update the
# value of the operation
@app.route('/')
def index():
    return render_template('index.html')
 
# Route that will process the AJAX request, sum up two
# integer numbers (defaulted to zero) and return the
# result as a proper JSON response (Content-Type, etc.)
@app.route('/_add_numbers')
def add_numbers():
    a = request.args.get('a', 0, type=int)
    b = request.args.get('b', 0, type=int)
    return jsonify(result=a + b)

@app.route('/_post_query', methods=['post'])
def post_query():
    param = request.form['query'] # pour POST
    print(param)
    return jsonify(result=treat(param))

@app.route('/_get_query', methods=['get'])
def get_query():
    param = request.args.get('query', '', type=str)
    print(param)
    return jsonify(result=treat(param))

def treat(query):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect( (ctx.host,ctx.port) )
    (ip,port) = s.getsockname()
    try:
        mess = '<query time="'+date2str(now())+'" client="'+str(ip)+'"><![CDATA['+query+']]></query>'
        print("Send query:",mess)
        s.send(mess.encode('utf8'))
        rep = s.recv(2048)
        print('ok:',rep)
        res=ctx.tpfc.query(query)
    except Exception as e:
        print('Exception',e)
        res='Error'
    finally:
        return res

#==================================================
#==================================================
#==================================================
 
# launch : python3.6 ldqp-WS.py 
# example to request : curl -d 'query="select * where {?s :p1 ?o}"' http://127.0.0.1:8090/_add_query

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Linked Data Query Profiler (for a modified TPF server)')
    # parser.add_argument('files', metavar='file', nargs='+',help='files to analyse')

    parser.add_argument("--port", type=int, default=5002, dest="port", help="Port (5002 by default)")
    parser.add_argument("--host", default='127.0.0.1', dest="host", help="Host ('127.0.0.1' by default)")
    parser.add_argument("-s","--server", default='http://localhost:5000/lift', dest="tpfServer", help="TPF Server ('http://localhost:5000/lift' by default)")
    parser.add_argument("-c", "--client", default='/Users/desmontils-e/Programmation/TPF/Client.js-master/bin/ldf-client', dest="tpfClient", help="TPF Client ('...' by default)")
    parser.add_argument("-t", "--time", default='', dest="now", help="Time reference (now by default)")
    parser.add_argument("-v", "--valid", default='', dest="valid", action="store_true", help="Do precision/recall")

    args = parser.parse_args()
    ctx.setLDQPServer(args.host,args.port)
    # http://localhost:5000/lift : serveur TPF LIFT (exemple du papier)
    # http://localhost:5001/dbpedia_3_9 server dppedia si : ssh -L 5001:172.16.9.3:5001 desmontils@172.16.9.15
    
    sp = TPFEP(service = args.tpfServer ) #'http://localhost:5000/lift') 
    sp.setEngine(args.tpfClient) #'/Users/desmontils-e/Programmation/TPF/Client.js-master/bin/ldf-client')
    ctx.setTPFClient(sp)

    try:
        app.run(
            host="0.0.0.0",
            port=int("8090"),
            debug=True
        )
    except KeyboardInterrupt: 
        pass
    finally:   
        pass # sp.close()
    print('Fin')

