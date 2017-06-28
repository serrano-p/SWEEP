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
import json

from lxml import etree  # http://lxml.de/index.html#documentation

from flask import Flask, render_template, request, jsonify, session,url_for
# http://flask.pocoo.org/docs/0.12/


class Context(object):
    """docstring for Context"""
    def __init__(self):
        super(Context, self).__init__()
        self.tree = None
        self.debug = False
        self.listeNoms = None
        self.listeBases = None
        self.version = '1.0'
        self.name = 'Name'
        self.ok = True
 
ctx = Context()

#==================================================

# Initialize the Flask application
app = Flask(__name__)
 
# This route will show a form to perform an AJAX request
# jQuery is loaded to execute the request and update the
# value of the operation
@app.route('/')
def index():
    return render_template('index.html',nom_appli=ctx.name, version=ctx.version, listeNoms=ctx.listeNoms)

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
    base = request.form['base']  
    s = "<p>Pas connecté</p>"
    d = dict({'ok':True,'val':s})
    return jsonify(result=d)


@app.route('/liste/bd/<soumettre>')
def liste(soumettre):
    # liste_base(Soumettre);
    return "<p>"+soumettre+"Pas de requête ou/et de base proposée !</p>"


# @app.route('/_post_query', methods=['post'])
# def post_query():
#     param = request.form['query'] # pour POST
#     print(param)
#     return jsonify(result=...)

# @app.route('/_get_query', methods=['get'])
# def get_query():
#     param = request.args.get('query', '', type=str)
#     print(param)
#     return jsonify(result=...)


#==================================================
#==================================================
#==================================================
 
# launch : python3.6 ldqp-WS.py 
# example to request : curl -d 'query="select * where {?s :p1 ?o}"' http://127.0.0.1:8090/_add_query

if __name__ == '__main__':
    parser = etree.XMLParser(recover=True, strip_cdata=True)
    ctx.tree = etree.parse('config.xml', parser)
    #---
    dtd = etree.DTD('config.dtd')
    assert dtd.validate(ctx.tree), '%s non valide au chargement : %s' % (
        file, dtd.error_log.filter_from_errors()[0])
    #---
    ctx.listeBases = dict()
    lb = ctx.tree.getroot().findall('listeBases/base_de_donnee')
    for l in lb :
        f = l.find('fichier')
        ref = l.find('référence')
        if ref.text is None: ref.text=''
        ctx.listeBases[l.get('nom')] = {'fichier':f.get('nom'),'prefixe':f.get('prefixe'),'référence':ref.text,
                                        'description':etree.tostring(l.find('description'), encoding='utf8').decode('utf8'),
                                        'tables':[]}
    ctx.listeNoms = list(ctx.listeBases.keys())
    ctx.version = ctx.tree.getroot().get('version')
    ctx.name = ctx.tree.getroot().get('name')
    if ctx.tree.getroot().get('debug') == 'false': ctx.debug = False
    else: ctx.debug = True
    try:
        app.run(
            host="0.0.0.0",
            port=int("8093"),
            debug=True
        )
    except KeyboardInterrupt: 
        pass
    finally:   
        pass
    print('Fin')

