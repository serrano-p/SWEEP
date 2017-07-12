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

from flask import Flask, render_template, request, jsonify, session,url_for
# http://flask.pocoo.org/docs/0.12/
# from flask_cas import CAS, login_required

from lxml import etree  # http://lxml.de/index.html#documentation

import requests as http
# http://docs.python-requests.org/en/master/user/quickstart/

class Context(object):
    """docstring for Context"""
    def __init__(self):
        super(Context, self).__init__()
        self.host = '127.0.0.1'
        self.port = 5002
        self.tpfc = TPFEP(service = 'http://localhost:5000/lift') 
        self.tpfc.setEngine('/Users/desmontils-e/Programmation/TPF/Client.js-master/bin/ldf-client')
        self.tree = None
        self.debug = False
        self.listeNoms = None
        self.listeBases = dict()
        self.listeSP = dict()
        self.version = '1.0'
        self.name = 'Name'
        self.ok = True        

    def setLDQPServer(self, host, port):
        self.host = host
        self.port = port

    def setTPFClient(self,tpfc):
        self.tpfc = tpfc
        
ctx = Context()

#==================================================

# Initialize the Flask application
app = Flask(__name__)
 
    # //authentification CAS
    # define("C_CASServer","cas-ha.univ-nantes.fr") ;
    # define("C_CASPort",443) ;
    # define("C_CASpath","/esup-cas-server") ;

# set the secret key.  keep this really secret:
app.secret_key = '\x0ctD\xe3g\xe1XNJ\x86\x02\x03`O\x98\x84\xfd,e/5\x8b\xd1\x11'

# cas = CAS(app)
# app.config['CAS_SERVER'] = 'https://cas-ha.univ-nantes.fr:443' 
# app.config['CAS_PORT'] = 443
# app.config['CAS_PATH'] = '/esup-cas-server'
# app.config['CAS_AFTER_LOGIN'] = 'route_root'


@app.route('/')
# @login_required
def index():
    return render_template(
        'index-qsim.html',
        # username = cas.username,
        # display_name = cas.attributes['cas:displayName'],
        nom_appli=ctx.name, version=ctx.version, listeNoms=ctx.listeNoms
    ) 

@app.route('/liste_noms')
def liste_noms():
    return jsonify(result=ctx.listeNoms)

@app.route('/liste_bases')
def liste_bases():
    return jsonify(result=ctx.listeBases)

@app.route('/end')
def end():
    return "<p>Bases purgées...</p>"

@app.route('/news')
def news():
    listeMessages = ctx.tree.getroot().findall('listeMessages/message')
    d = list()
    for message in listeMessages:
        r = dict()
        titre = message.get('titre')
        date = message.get('date')
        auteur = message.get('auteur')
        r['titre'] = titre
        r['post'] = "-> Le "+date+" par "+auteur
        s = ''
        for cont in message: s+= etree.tostring(cont, encoding='utf8').decode('utf8')
        r['s'] = s
        d.append(r)
    return jsonify(result=d)

@app.route('/mentions')
def mentions():
    m = ctx.tree.getroot().find('mentions')
    s = ''
    for cont in m: 
        if cont.text is not None: s+= etree.tostring(cont, encoding='utf8').decode('utf8')
    return s

@app.route('/apropos')
def apropos():
    m = ctx.tree.getroot().find('aPropos')
    s = ''
    for cont in m:
        if cont.text is not None: s+= etree.tostring(cont, encoding='utf8').decode('utf8')
    return s

@app.route('/help')
def help():
    m = ctx.tree.getroot().find('aides')
    s = ''
    for cont in m:
        if cont.text is not None: s+= etree.tostring(cont, encoding='utf8').decode('utf8')
    return s

@app.route('/envoyer', methods=['post'])
def envoyer():
    query = request.form['requete']
    datasource = request.form['base']
    # print(query)
    # print(datasource)
    ip = request.remote_addr
    s=treat(query,ip,datasource)
    tab = doTab(s)
    d = dict({'ok':s != 'Error','val':tab})
    return jsonify(result=d)

@app.route('/liste/bd/<datasource>')
def liste(datasource):
    ip = request.remote_addr
    # print(datasource, )
    s=treat("select * where{?s ?p ?o} limit 100",ip,datasource)
    tab = doTab(s)
    d = dict({'ok':s != 'Error','val':tab})
    return jsonify(result=d)    
    # return "<p>"+soumettre+"Pas de requête ou/et de base proposée !</p>"

def doTab(s):
    if len(s)>0:
        tab = '<table cellspacing="5" border="1" cellpadding="2">\n<thead>'
        m = s[0]
        for (var,val) in m.items():
            tab += '<th>'+var+'</th>'
        tab += '</thead>\n'
        for m in s:
            tab += '<tr>'
            for (var,val) in m.items():
                tab += '<td>'+val+'</td>'
            tab += '</tr>\n'
        tab += '</table>'
    else:
        tab = '<p> Empty </p>\n'
    return tab

def treat(query,ip,datasource):
    try:
        mess = '<query time="'+date2str(now())+'" client="'+str(ip)+'"><![CDATA['+query+']]></query>'
        url = 'http://'+ctx.host+':'+str(ctx.port)+'/query'
        # print('Send to ',url)
        # print('query',mess)
        s = http.post(url,data={'data':mess})
        # print('res:',s.json()['result'])
        res=  ctx.listeSP[datasource].query(query) # ctx.tpfc.query(query)
        # pprint(res)
        # print(type(res))
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

TPF_SERVEUR_HOST = 'http://127.0.0.1'
TPF_SERVEUR_PORT = 5000
TPF_CLIENT = '/Users/desmontils-e/Programmation/TPF/Client.js-master/bin/ldf-client'
SWEEP_SERVEUR_HOST = 'http://127.0.0.1'
SWEEP_SERVEUR_PORT = 5002

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Linked Data Query Profiler (for a modified TPF server)')
    # parser.add_argument('files', metavar='file', nargs='+',help='files to analyse')

    parser.add_argument("--port", type=int, default=SWEEP_SERVEUR_PORT, dest="port", help="SWEEP Port ('"+str(SWEEP_SERVEUR_PORT)+"' by default)")
    parser.add_argument("--host", default=SWEEP_SERVEUR_HOST, dest="host", help="SWEEP Host ('"+SWEEP_SERVEUR_HOST+"' by default)")
    parser.add_argument("-s","--server", default=TPF_SERVEUR_HOST+':'+str(TPF_SERVEUR_PORT), dest="tpfServer", help="TPF Server ('"+TPF_SERVEUR_HOST+':'+str(TPF_SERVEUR_PORT)+"' by default)")
    parser.add_argument("-c", "--client", default=TPF_CLIENT, dest="tpfClient", help="TPF Client ('...' by default)")
    parser.add_argument("-t", "--time", default='', dest="now", help="Time reference (now by default)")
    parser.add_argument("-v", "--valid", default='', dest="valid", action="store_true", help="Do precision/recall")

    args = parser.parse_args()
    ctx.setLDQPServer(args.host,args.port)
    # http://localhost:5000/lift : serveur TPF LIFT (exemple du papier)
    # http://localhost:5001/dbpedia_3_9 server dppedia si : ssh -L 5001:172.16.9.3:5001 desmontils@172.16.9.15

    XMLparser = etree.XMLParser(recover=True, strip_cdata=True)
    ctx.tree = etree.parse('config.xml', XMLparser)
    #---
    dtd = etree.DTD('config.dtd')
    assert dtd.validate(ctx.tree), '%s non valide au chargement : %s' % (
        file, dtd.error_log.filter_from_errors()[0])
    #---
    lb = ctx.tree.getroot().findall('listeBases/base_de_donnee')
    for l in lb :
        f = l.find('fichier')
        ref = l.find('référence')
        if ref.text is None: ref.text=''
        print('Configure ',l.get('nom'), ' in ',args.tpfServer+'/'+f.get('nom'))
        sp = TPFEP(service = args.tpfServer, dataset= f.get('nom') )#, clientParams= '-s '+args.host+':'+str(args.port) )
        sp.setEngine(args.tpfClient )
        ctx.listeBases[l.get('nom')] = {'fichier':f.get('nom'),'prefixe':f.get('prefixe'),'référence':ref.text,
                                        'description':etree.tostring(l.find('description'), encoding='utf8').decode('utf8'),
                                        'tables':[]}
        ctx.listeSP[l.get('nom')] = sp
    ctx.listeNoms = list(ctx.listeBases.keys())
    ctx.version = ctx.tree.getroot().get('version')
    ctx.name = ctx.tree.getroot().get('name')
    if ctx.tree.getroot().get('debug') == 'false': ctx.debug = False
    else: ctx.debug = True

    try:
        app.run(
            host="0.0.0.0",
            port=int("8090"),
            debug=True
        )
    except KeyboardInterrupt: 
        pass
    finally:   
        pass
    print('Fin')

