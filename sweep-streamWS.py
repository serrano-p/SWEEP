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
import html

from tools.tools import *

from lxml import etree  # http://lxml.de/index.html#documentation
from lib.bgp import *

from io import StringIO

from sweep import *

from flask import Flask, render_template, request, jsonify, session,url_for
# http://flask.pocoo.org/docs/0.12/

class Context(object):
    """docstring for Context"""
    def __init__(self):
        super(Context, self).__init__()
        self.ldqp = None
        self.parser = etree.XMLParser(recover=True, strip_cdata=True)
        self.cpt = 0
        self.list = mp.Manager().list()
        
ctx = Context()

#==================================================

# Initialize the Flask application
app = Flask(__name__)
# set the secret key.  keep this really secret:
app.secret_key = '\x0ctD\xe3g\xe1XNJ\x86\x02\x03`O\x98\x84\xfd,e/5\x8b\xd1\x11'

@app.route('/')
# @login_required
def index():
    return render_template('index-sweep.html',nom_appli="SWEEP Monitor", version="0.1")

@app.route('/lift')
def lift():
    ctx.cpt += 1
    rep = ''
    rep += '<table border="1"><thead><td>Precision</td><td>Recall</td><td>Quality</td><td>Acureness</td></thead><tr><td>%2.3f</td><td>%2.3f</td><td>%2.3f</td><td>%2.3f</td></tr></table>\n'%(ctx.ldqp.avgPrecision.value,ctx.ldqp.avgRecall.value,ctx.ldqp.avgQual.value,ctx.ldqp.Acuteness.value)
    rep += '<table cellspacing="5" border="1" cellpadding="2">\n'
    rep += '<thead><td>ip</td><td>time</td><td>bgp</td></thead>\n'
    for bgp in ctx.list:
        rep +='<tr><td>'+bgp.client+'</td><td>'+str(bgp.time)+'</td><td>'
        for ((s,p,o),sm,pm,om) in bgp.tp_set:
            rep += html.escape(toStr(s,p,o))+'<br/>'
        rep += '</td></tr>'
    rep += '</table>'
    return rep

@app.route('/query', methods=['post','get'])
def processQuery():
    if request.method == 'POST':
        ip = request.remote_addr
        data = request.form['data']
        print('Receiving request:',data)
        try:
            tree = etree.parse(StringIO(data), ctx.parser)
            query = tree.getroot()
            client = query.get('client')
            if client is None:
                query.set('client',str(ip) )
            elif client in ["undefined","", "undefine"]:
                query.set('client',str(ip) )
            elif "::ffff:" in client:
                query.set('client', client[7:])
            ctx.ldqp.put(query)   
            return jsonify(result=True)            
        except Exception as e:
            print('Exception',e)
            print('About:',data)
            return jsonify(result=False)       
    else:
        print('"query" not implemented for HTTP GET')
        return jsonify(result=False)

@app.route('/entry', methods=['post','get'])
def processEntry():
    if request.method == 'POST':
        ip = request.remote_addr
        data = request.form['data']
        print('Receiving entry:',data)
        try:
            tree = etree.parse(StringIO(data), ctx.parser)
            query = tree.getroot()
            client = query.get('client')
            if client is None:
                query.set('client',str(ip) )
            elif client in ["undefined","", "undefine"]:
                query.set('client',str(ip) )
            elif "::ffff:" in client:
                query.set('client', client[7:])
            ctx.ldqp.put(query)  
            return jsonify(result=True)             
        except Exception as e:
            print('Exception',e)
            print('About:',data)
            return jsonify(result=False)       
    else:
        print('"entry" not implemented for HTTP GET')
        return jsonify(result=False)

@app.route('/data', methods=['post','get'])
@app.route('/end', methods=['post','get'])
def processData():
    if request.method == 'POST':
        data = request.form['data']
        print('Receiving data:',data)
        try:
            tree = etree.parse(StringIO(data), ctx.parser)
            ctx.ldqp.put(tree.getroot()) 
            return jsonify(result=True)              
        except Exception as e:
            print('Exception',e)
            print('About:',data)
            return jsonify(result=False)       
    else:
        print('"entry/data/end" not implemented for HTTP GET')
        return jsonify(result=False)

#==================================================

def processResults(ldqp,list):
    i = 0
    try:
        res = ldqp.get()
        while res != None:
            i += 1
            res.print()
            list.append(res)
            res = ldqp.get()
    except KeyboardInterrupt:
        pass

#==================================================
#==================================================
#==================================================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Linked Data Query Profiler (for a modified TPF server)')
    # parser.add_argument('files', metavar='file', nargs='+',help='files to analyse')
    parser.add_argument("-g", "--gap", type=float, default=60, dest="gap", help="Gap in minutes (60 by default)")
    parser.add_argument("-to", "--timeout", type=float, default=0, dest="timeout",
                        help="TPF server Time Out in minutes (%d by default). If '-to 0', the timeout is the gap." % 0)
    parser.add_argument("-o","--optimistic", help="BGP time is the last TP added (False by default)",
                    action="store_true",dest="doOptimistic")

    args = parser.parse_args()

    ctx.ldqp = SWEEP_XML(dt.timedelta(minutes= args.gap))
    resProcess = mp.Process(target=processResults, args=(ctx.ldqp,ctx.list))

    if args.timeout > 0 : ctx.ldqp.setTimeout(dt.timedelta(minutes= args.timeout))
    if args.doOptimistic: ctx.ldqp.swapOptimistic()

    try:
        ctx.ldqp.startSession()
        resProcess.start()
        app.run(
            host="0.0.0.0",
            port=int("5002"),
            debug=True
        )
        # while 1:
        #     time.sleep(60)
    except KeyboardInterrupt:
        ctx.ldqp.endSession() 
        ctx.ldqp.stop()
        resProcess.join()
    print('Fin')
