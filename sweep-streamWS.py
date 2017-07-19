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
from operator import itemgetter

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
        self.sweep = None
        self.parser = etree.XMLParser(recover=True, strip_cdata=True)
        self.cpt = 0
        self.list = mp.Manager().list()
        self.to = 0.0
        self.gap = 0.0 
        self.opt = False
        self.nlast = 10
        self.nbQueries = 0
        self.nbEntries = 0
        self.nbCancelledQueries = 0
        self.nbQBF = 0
        self.nbTO = 0
        self.nbEQ = 0
        self.nbOther = 0
        self.nbClientError = 0
        self.nbEmpty = 0
        
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

@app.route('/bestof')
def bo():
    t = '<table cellspacing="50"><tr>'

    rep = '<td><h1>Frequent deduced BGPs</h1><p>('+str(ctx.nlast)+' more frequents)</p>'
    rep += '<table cellspacing="5" border="1" cellpadding="2">'
    rep += '<thead><td>BGP</td><td>Nb Occ.</td><td>Query Exemple</td>'
    ctx.sweep.rankingBGPs.sort(key=itemgetter(1), reverse=True)
    for (bgp, freq, query, lines, precision, recall) in ctx.sweep.rankingBGPs[:ctx.nlast]:
        rep += '<tr>'
        rep += '<td>'
        for (s,p,o) in simplifyVars(bgp):
            rep += html.escape(toStr(s,p,o))+' . <br/>'
        rep += '</td>'
        rep += '<td>%d</td><td>%s</td>'%(freq,html.escape(query))
        rep += '</tr>'
    rep += '</table></td>'

    rep += '<td><h1>Frequent Ground Truth Queries</h1><p>('+str(ctx.nlast)+' more frequents)</p>'
    rep += '<table cellspacing="5" border="1" cellpadding="2">'
    rep += '<thead><td>BGP</td><td>Nb Occ.</td><td>Query Exemple</td><td>Avg. Precision</td><td>Avg. Recall</td>'
    ctx.sweep.rankingQueries.sort(key=itemgetter(1), reverse=True)
    for (bgp, freq, query, lines, precision, recall) in ctx.sweep.rankingQueries[:ctx.nlast]:
        rep += '<tr>'
        rep += '<td>'
        for (s,p,o) in simplifyVars(bgp):
            rep += html.escape(toStr(s,p,o))+' . <br/>'
        rep += '</td>'
        rep += '<td>%d</td><td>%s</td><td>%2.3f</td><td>%2.3f</td>'%(freq,html.escape(query), precision/freq, recall/freq)
        rep += '</tr>'
    rep += '</table></td>'

    t += rep + '<tr></table>' 

    return rep #'<p>Not implemented</p>'


@app.route('/sweep')
def sweep():
    ctx.cpt += 1
    nb = ctx.sweep.stat['nbQueries']
    nbbgp = ctx.sweep.stat['nbBGP']
    if nb>0:
        avgPrecision = ctx.sweep.stat['sumPrecision']/nb
        avgRecall = ctx.sweep.stat['sumRecall']/nb
        avgQual = ctx.sweep.stat['sumQuality']/nb
    else:
        avgPrecision = 0
        avgRecall = 0
        avgQual = 0
    if nbbgp>0 :                
        Acuteness = ctx.sweep.stat['sumSelectedBGP'] / nbbgp
    else:
        Acuteness = 0

    rep = '<table cellspacing="50"><tr><td><h1>SWEEP parameters</h1><table border="1"><thead>'
    rep += '<td>Gap</td><td>Time out</td><td>Opt</td></thead><tr>'
    rep += '<td>%s</td><td>%s</td><td>%s</td>'%(dt.timedelta(minutes= ctx.gap),dt.timedelta(minutes= ctx.to),str(ctx.opt))
    rep += '</tr></table></td>'

    rep += '<td><h1>Global measures</h1><table border="1"><thead>'
    rep += '<td>Nb Evaluated Queries</td><td>Nb Cancelled Queries</td><td>Nb Empty Queries</td><td>Nb Timeout Queries</td><td>Nb Bad formed Queries</td><td>Nb TPF Client Error</td><td>Nb TPF Client Query Error</td><td>Nb Other query Error</td>'   
    rep += '<td>Nb BGP</td><td>Nb Entries</td>'
    rep += '<td>Avg Precision</td><td>Avg Recall</td><td>Avg Quality</td><td>Acuteness</td></thead><tr>'

    rep += '<td>%d / %d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td>'%(nb,ctx.nbQueries,ctx.nbCancelledQueries,ctx.nbEmpty,ctx.nbTO,ctx.nbQBF,ctx.nbClientError,ctx.nbEQ,ctx.nbOther)

    rep += '<td>%d</td><td>%d</td>'%(nbbgp,ctx.nbEntries)
    rep += '<td>%2.3f</td><td>%2.3f</td><td>%2.3f</td><td>%2.3f</td>'%(avgPrecision,avgRecall,avgQual,Acuteness)
    rep += '</tr></table></td></tr></table>\n<hr size="2" width="100" align="CENTER" />'

    rep += '<h1>BGPs</h1><p>('+str(ctx.nlast)+' more recents)</p><table cellspacing="5" border="1" cellpadding="2">\n'
    rep += '<thead><td>ip</td><td>time</td><td>bgp</td><td>Original query</td><td>Precision</td><td>Recall</td><td>Quality</td></thead>\n'
    for (i,idQ, t,ip,query,bgp,precision,recall) in ctx.sweep.memory[-1*ctx.nlast:] :
        if i==0:
            rep +='<tr><td>'+bgp.client+'</td><td>'+str(bgp.time)+'</td><td>'
            for (s,p,o) in simplifyVars([tp for (tp,sm,pm,om) in bgp.tp_set]):
                rep += html.escape(toStr(s,p,o))+' . <br/>'
            rep += '</td><td>No query assigned</td><td></td><td></td><td></td></tr>'
        else:
            rep +='<tr><td>'+ip+'</td><td>'+str(t)+'</td><td>'
            if bgp is not None:
                for (s,p,o) in simplifyVars([tp for (tp,sm,pm,om) in bgp.tp_set]):
                    rep += html.escape(toStr(s,p,o))+' . <br/>'
            else:
                rep += 'No BGP assigned !'
            rep += '</td><td>'+idQ+'<br/>'+html.escape(query)+'</td><td>%2.3f</td><td>%2.3f</td><td>%2.3f</td></tr>'%(precision,recall,(precision+recall)/2)
    rep += '</table>'
    return rep

# @app.route('/delquery', methods=['post','get'])
# def processDelQuery():
#     if request.method == 'POST':
#         ip = request.remote_addr
#         # data = request.form['data']
#         ctx.sweep.stat['nbQueries'] -= 1
#         ctx.nbCancelledQueries += 1
#         # ctx.nbQueries -= 1
#         return jsonify(result=True)
#     else:
#         print('"delquery" not implemented for HTTP GET')
#         return jsonify(result=False)

@app.route('/inform', methods=['post','get'])
def processInform():
    if request.method == 'POST':
        ip = request.remote_addr
        errtype = request.form['errtype']
        queryNb = request.form['no']
        if errtype == 'QBF':
            print('(%s)'%queryNb,'Query Bad Formed :',request.form['data'])
            ctx.sweep.delQuery(queryNb)
            ctx.nbCancelledQueries += 1 
            ctx.nbQBF += 1
        elif errtype == 'TO':
            print('(%s)'%queryNb,'Time Out :',request.form['data'])
            ctx.sweep.delQuery(queryNb)
            ctx.nbCancelledQueries += 1 
            ctx.nbTO += 1
        elif errtype == 'CltErr':
            print('(%s)'%queryNb,'TPF Client Error for :',request.form['data'])
            ctx.sweep.delQuery(queryNb)
            ctx.nbCancelledQueries += 1 
            ctx.nbClientError += 1
        elif errtype == 'EQ':
            print('(%s)'%queryNb,'Error Query for :',request.form['data'])
            ctx.sweep.delQuery(queryNb)
            ctx.nbCancelledQueries += 1 
            ctx.nbEQ += 1
        elif errtype == 'Other':
            print('(%s)'%queryNb,'Unknown Pb for query :',request.form['data'])
            ctx.sweep.delQuery(queryNb)  
            ctx.nbCancelledQueries += 1       
            ctx.nbOther += 1 
        elif errtype == 'Empty':
            print('(%s)'%queryNb,'Empty for :',request.form['data'])
            ctx.nbEmpty += 1
        else:
            print('(%s)'%queryNb,'Unknown Pb for query :',request.form['data'])
            ctx.sweep.delQuery(queryNb)
            ctx.nbCancelledQueries += 1 
            ctx.nbOther += 1
        return jsonify(result=True)
    else:
        print('"inform" not implemented for HTTP GET')
        return jsonify(result=False)

@app.route('/query', methods=['post','get'])
def processQuery():
    if request.method == 'POST':
        ip = request.remote_addr
        data = request.form['data']
        # print('Receiving request:',data)
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
            ctx.nbQueries += 1
            ctx.sweep.putQuery(query)
            return jsonify(result=True)            
        except Exception as e:
            print('Exception',e)
            print('About:',data)
            return jsonify(result=False)       
    else:
        print('"query" not implemented for HTTP GET')
        return jsonify(result=False)

# @app.route('/entry', methods=['post','get'])
# def processEntry():
#     if request.method == 'POST':
#         ip = request.remote_addr
#         data = request.form['data']
#         # print('Receiving entry:',data)
#         try:
#             tree = etree.parse(StringIO(data), ctx.parser)
#             entry = tree.getroot()
#             client = entry.get('client')
#             if client is None:
#                 entry.set('client',str(ip) )
#             elif client in ["undefined","", "undefine"]:
#                 entry.set('client',str(ip) )
#             elif "::ffff:" in client:
#                 entry.set('client', client[7:])
#             ctx.nbEntries += 1
#             ctx.sweep.put(entry)  
#             return jsonify(result=True)             
#         except Exception as e:
#             print('Exception',e)
#             print('About:',data)
#             return jsonify(result=False)       
#     else:
#         print('"entry" not implemented for HTTP GET')
#         return jsonify(result=False)

# @app.route('/data', methods=['post','get'])
# def processData():
#     if request.method == 'POST':
#         data = request.form['data']
#         # print('Receiving data:',data)
#         try:
#             tree = etree.parse(StringIO(data), ctx.parser)
#             ctx.sweep.put(tree.getroot()) 
#             return jsonify(result=True)              
#         except Exception as e:
#             print('Exception',e)
#             print('About:',data)
#             return jsonify(result=False)       
#     else:
#         print('"data" not implemented for HTTP GET')
#         return jsonify(result=False)

# @app.route('/end', methods=['post','get'])
# def processEnd():
#     if request.method == 'POST':
#         i = request.form['data']
#         try:
#             ctx.sweep.putEnd(i) 
#             return jsonify(result=True)              
#         except Exception as e:
#             print('Exception',e)
#             print('About:',data)
#             return jsonify(result=False)       
#     else:
#         print('"end" not implemented for HTTP GET')
#         return jsonify(result=False)

@app.route('/data', methods=['post','get'])
def processData():
    if request.method == 'POST':
        data = request.form['data']
        # print('Receiving data:',data)
        try:
            tree = etree.parse(StringIO(data), ctx.parser)
            for e in tree.getroot():
                if e.tag == 'entry':
                    entry = e
                    client = entry.get('client')
                    if client is None:
                        entry.set('client',str(ip) )
                    elif client in ["undefined","", "undefine"]:
                        entry.set('client',str(ip) )
                    elif "::ffff:" in client:
                        entry.set('client', client[7:])
                    ctx.nbEntries += 1
                    ctx.sweep.put(entry)  
                elif e.tag == 'data-triple-N3':
                    ctx.sweep.put(e)
                else:
                    pass
            return jsonify(result=True)              
        except Exception as e:
            print('Exception',e)
            print('About:',data)
            return jsonify(result=False)       
    else:
        print('"data" not implemented for HTTP GET')
        return jsonify(result=False)


#==================================================

def processResults(sweep,list):
    i = 0
    try:
        res = sweep.get()
        while res != None:
            i += 1
            # res.print()
            list.append(res)
            res = sweep.get()
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
    parser.add_argument("-l", "--last", type=int, default=10, dest="nlast", help="Number of last BGPs to view (10 by default)")
    args = parser.parse_args()
 
    ctx.gap = args.gap
    if args.timeout == 0:
        ctx.to = ctx.gap
    else:
        ctx.to = args.timeout

    if args.doOptimistic: ctx.sweep.swapOptimistic()
    ctx.opt = args.doOptimistic 

    ctx.sweep = SWEEP_XML(dt.timedelta(minutes= ctx.gap),dt.timedelta(minutes= ctx.to),ctx.opt)
    resProcess = mp.Process(target=processResults, args=(ctx.sweep,ctx.list))
    ctx.nlast = args.nlast


    try:
        ctx.sweep.startSession()
        resProcess.start()
        app.run(
            host="0.0.0.0",
            port=int("5002"),
            debug=False
        )
        # while 1:
        #     time.sleep(60)
    except KeyboardInterrupt:
        ctx.sweep.endSession() 
        ctx.sweep.stop()
        resProcess.join()
    print('Fin')
