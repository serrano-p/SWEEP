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

#==================================================

transform = etree.XSLT(etree.parse('toTrace.xsl'))

def fromISO(u): 
    try:
        return iso8601.parse_date(u)
    except iso8601.ParseError:
        return iso8601.parse_date(date.today().isoformat()+'T'+u)
    #return time.strptime(u.attrib['t'], "%Y-%m-%dT%H:%M:%S")

class BGP:
    def __init__(self):
        self.tp_set = []
        self.input_set = set() # ens. des hash des entrées, pour ne pas mettre 2 fois la même
        self.time = ''
        self.client = ''

def toStr(s,p,o):
    return serialize2string(s)+' '+serialize2string(p)+' '+serialize2string(o)

LIFT2_IN_ENTRY = 1
LIFT2_IN_DATA = 2
LIFT2_IN_END = 3

LIFT2_START_SESSION = -1
LIFT2_END_SESSION = -2

def processXMLEntry(x):
    id = x.attrib['id']
    if x[0].attrib['type']=='var' : x[0].set('val','s')
    if x[1].attrib['type']=='var' : x[1].set('val','p')
    if x[2].attrib['type']=='var' : x[2].set('val','o')
    s = unSerialize(x[0])
    p = unSerialize(x[1])
    o = unSerialize(x[2])
    return (id, LIFT2_IN_ENTRY, (s,p,o,x.attrib['time'],x.attrib['client'],set(),set(),set()) )

def processXMLEndEntry(x):
    id = x.attrib['id']
    return (id, LIFT2_IN_END, () )

def processXMLData(x):
    id = x.attrib['id']
    xs = unSerialize(x[0])
    xp = unSerialize(x[1])
    xo = unSerialize(x[2])
    return (id, LIFT2_IN_DATA, (xs, xp, xo))

def processAgregator(in_queue,out_queue):
    elist = dict()
    inq = in_queue.get()
    while inq is not None:
        (id, x, val) = inq
        if x == LIFT2_IN_ENTRY:
            elist[id] = val
        elif x == LIFT2_IN_DATA :
            (s,p,o,t,c,sm,pm,om) = elist[id]
            (xs,xp,xo) = val
            if isinstance(s,Variable): sm.add(xs)
            if isinstance(p,Variable): pm.add(xp)
            if isinstance(o,Variable): om.add(xo)
        elif x == LIFT2_IN_END :
            out_queue.put((id, elist.pop(id)))
        elif x == LIFT2_START_SESSION :
            print('Agregator - Start Session')
            elist.clear()
            out_queue.put( (id, LIFT2_START_SESSION) )
        elif x == LIFT2_END_SESSION :
            print('Agregator - End Session')
            for v in elist:
                out_queue.put( (v, elist.pop(v)) )
            out_queue.put( (id, LIFT2_END_SESSION) )
        else: # Impossible...
            pass
        inq = in_queue.get()
    out_queue.put(None)

def processBGPDiscover(in_queue, out_queue, gap):
    BGP_list = []
    entry = in_queue.get()
    while entry != None:
        (id, val) = entry
        if val == LIFT2_START_SESSION:
            print('BGPDiscover - Start Session')
            BGP_list.clear()
            out_queue.put(LIFT2_START_SESSION)
        elif val == LIFT2_END_SESSION:
            print('BGPDiscover - End Session')
            for (i,bgp) in enumerate(BGP_list):
                out_queue.put(bgp)
            BGP_list.clear()
            out_queue.put(LIFT2_END_SESSION)
        else :
            (s,p,o,time,client,sm,pm,om) = val
            currentTime = fromISO(time)
            #print('Etude de :',toStr(s,p,o))
            if not(isinstance(s,Variable) and isinstance(p,Variable) and isinstance(o,Variable) ):
                h = hash(toStr(s,p,o))
                #print(currentTime)
                trouve = False
                for (i,bgp) in enumerate(BGP_list):
                    # Si c'est le même client, dans le gap et un TP identique n'a pas été utilisé
                    #print('\t Etude avec BGP ',i)
                    if (client == bgp.client) and (currentTime - bgp.time <= gap) and (h not in bgp.input_set): 
                        trouveSM = False
                        trouvePM = False
                        trouveOM = False
                        ref_tp = None
                        ref_couv = 0
                        # on regarde si un constante du sujet et ou de l'objet est une injection
                        for tp in  bgp.tp_set:
                            ( (bs, bp, bo), bsm, bpm, bom, bh ) = tp
                            #print('\t\t Comparaison avec :',toStr(bs,bp,bo))
                            couv = 0
                            #print('\t\tbsm:',bsm) ; print('\t\tbpm:',bpm); print('\t\tbom:',bom)

                            trouveSM = (not(isinstance(s,Variable))) and (s in bsm)
                            if trouveSM: couv += 1

                            trouvePM = (not(isinstance(p,Variable))) and (p in bpm)
                            if trouvePM: couv += 1

                            trouveOM = (not(isinstance(o,Variable))) and (o in bom)
                            if trouveOM: couv += 1

                            if (trouveSM or trouvePM or trouveOM) and (couv > ref_couv) :
                                trouve = True
                                ref_tp = tp
                                ref_couv = couv
                                ref_trouveSM = trouveSM
                                ref_trouvePM = trouvePM
                                ref_trouveOM = trouveOM
                                #print('\t\t',trouveSM , trouvePM , trouveOM)
                                break

                        if trouve:
                            ( (bs, bp, bo), bsm, bpm, bom, bh ) = ref_tp
                            #print('\t\t ok avec :',toStr(bs,bp,bo) )
                            if ref_trouveOM: o2 = bo
                            else: o2 = o
                            if ref_trouvePM: p2 = bp
                            else: p2 = p
                            if ref_trouveSM: s2 = bs
                            else: s2 = s
                            h2 = hash(toStr(s2,p2,o2))
                            #print('\t\t |-> ',toStr(s2,p2,o2) )
                            inTP = False
                            # peut-être que un TP similaire a déjà été utilisé pour une autre valeur... alors pas la peine de le doubler
                            for  ( (b2s, b2p, b2o), b2sm, b2pm, b2om, b2h ) in  bgp.tp_set:
                                inTP = h2 == b2h
                                if inTP: break

                            if not(inTP):
                                if not(ref_trouveSM) and isinstance(s,Variable): s2 = Variable("s"+str(id).replace("-","_"))
                                if not(ref_trouvePM) and isinstance(p,Variable): p2 = Variable("p"+str(id).replace("-","_"))
                                if not(ref_trouveOM) and isinstance(o,Variable): o2 = Variable("o"+str(id).replace("-","_"))
                                bgp.tp_set.append( ((s2,p2,o2),sm,pm,om, h2) )
                                #print('\t\t Ajout de ',toStr(s2,p2,o2))
                                bgp.input_set.add(h)
                            else: 
                                #print('\t Déjà présent avec ',toStr(b2s, b2p, b2o))
                                pass
                            break
                    else:
                        if (client == bgp.client) and (currentTime - bgp.time <= gap):
                            #print('\t\t Déjà ajouté')
                            pass
                            # trouve = True

                if not(trouve):
                    bgp = BGP()     
                    h2 = hash(toStr(s,p,o))
                    if isinstance(s,Variable):
                        s = Variable("s"+str(id).replace("-","_"))
                    if isinstance(p,Variable):
                        p = Variable("p"+str(id).replace("-","_"))
                    if isinstance(o,Variable):
                        o = Variable("o"+str(id).replace("-","_"))
                    #print('\t Création de ',toStr(s,p,o),'-> BGP ',len(BGP_list))
                    bgp.tp_set.append(( (s,p,o), sm,pm,om, h2))
                    bgp.input_set.add(h)
                    bgp.time = currentTime
                    bgp.client = client
                    BGP_list.append(bgp)

            # envoyer les trop vieux !
            old = []
            recent = []
            for bgp in BGP_list:
                if (currentTime - bgp.time > gap): old.append(bgp)
                else: recent.append(bgp)
            for bgp in old :  
                out_queue.put(bgp)
            BGP_list = recent

        entry = in_queue.get()
    out_queue.put(None)

def makeLog(ip):
    #print('Finding bgp')
    node_log = etree.Element('log')
    node_log.set('ip',ip)
    return node_log

def addBGP(n,bgp, node_log):
    #print(serializeBGP2str([ x for (x,sm,pm,om,h) in bgp.tp_set]))
    entry_node = etree.SubElement(node_log, 'entry')
    entry_node.set('datetime', '%s' % bgp.time)
    entry_node.set('logline', '%s' % n)
    request_node = etree.SubElement(entry_node, 'request')
    try:
        bgp_node = serializeBGP([ x for (x,sm,pm,om,h) in bgp.tp_set])
        entry_node.insert(1, bgp_node)
        query = 'select * where{ \n'
        for ( (s,p,o) ,sm,pm,om,h) in bgp.tp_set :
            query += serialize2string(s) + ' ' + serialize2string(p) + ' ' + serialize2string(o) + ' .\n'
        query += ' }'
        request_node.text = query
    except Exception as e:
        logging.error('(%s) PB serialize BGP : %s\n%s\n%s', host, e.__str__(), nquery, bgp)
    return node_log

def save(node_log, lift2):
    try:
        print('Ecriture de "%s"' % lift2)
        tosave = etree.tostring(
            node_log,
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=True,
            doctype='<!DOCTYPE log SYSTEM "http://documents.ls2n.fr/be4dbp/log.dtd">')
        try:
            f = open(lift2, 'w')
            f.write(tosave.decode('utf-8'))
        except Exception as e:
            print(
                'PB Test Analysis saving %s : %s',
                file,
                e.__str__())
        finally:
            f.close()
    except etree.DocumentInvalid as e:
        print('PB Test Analysis, %s not validated : %s' % (file, e))

#==================================================

parser = argparse.ArgumentParser(description='Etude des requêtes')
parser.add_argument('files', metavar='file', nargs='+',
                    help='files to analyse')
parser.add_argument("-p", "--proc", type=int, default=mp.cpu_count(), dest="nb_processes",
                    help="Number of processes used (%d by default)" % mp.cpu_count())

parser.add_argument("-l", "--log", help="Do log from GN",action="store_true",dest="doGN")

parser.add_argument("-g", "--gap", type=int, default=60, dest="gap", help="Gap in minutes (60 by default)")

args = parser.parse_args()
file_set = args.files
current_dir = os.getcwd()

# nb_processes = args.nb_processes
# print('Lancement des %d processus d\'analyse' % nb_processes)
# ps = ProcessSet(nb_processes, analysis)
# ps.start()

dataQueue = mp.Queue()
entryQueue = mp.Queue()
resQueue = mp.Queue()

gap = dt.timedelta(minutes= args.gap)

dataProcess = mp.Process(target=processAgregator, args=(dataQueue, entryQueue))
entryProcess = mp.Process(target=processBGPDiscover, args=(entryQueue, resQueue, gap))
dataProcess.start()
entryProcess.start()
parser = etree.XMLParser(recover=True, strip_cdata=True)

if args.doGN:
    old_rep = ''
    old_ip = ''
    no = 0
    for file in file_set:
        if existFile(file):
            no += 1
            t = file.split('/')
            n = len(t)
            m = re.search('\Atraces_(?P<ip>.*)-be4dbp-tested-TPF-ranking\Z',t[n-2])
            ip = m.group('ip')
            rep = '/'.join(t[:-2])
            name = t[n-1]

            if ip != old_ip:
                if old_ip != '': 
                    dataQueue.put( (0,LIFT2_END_SESSION,()  ) )
                    i = 1
                    res = resQueue.get()
                    while res != LIFT2_END_SESSION:
                        if res != LIFT2_START_SESSION : 
                            i += 1
                            addBGP(str(no)+str(i), res, node_log)
                        res = resQueue.get()
                    save(node_log, file_lift)
                if not (os.path.isdir(rep)):
                    os.makedirs(rep)
                old_rep = rep
                old_ip = ip
                file_lift = old_rep+'/'+old_ip+'-lift2.xml'
                node_log = makeLog(ip)
                dataQueue.put( (0,LIFT2_START_SESSION,() ) )
            print('Analyse de ',file)
            otree = etree.parse(file, parser)
            for x in otree.getroot():
                if x.tag == 'entry': 
                    x.attrib['client'] = ip
                    dataQueue.put( processXMLEntry(x) )
                elif x.tag == 'data-triple-N3' : dataQueue.put( processXMLData(x) )
                elif x.tag == 'end' : dataQueue.put( processXMLEndEntry(x) )
                else: pass

    if old_ip != '': 
        dataQueue.put( (0,LIFT2_END_SESSION,()  ) )
        i = 1
        res = resQueue.get()
        while res != LIFT2_END_SESSION:
            if res != LIFT2_START_SESSION : 
                i += 1
                addBGP(str(no)+str(i), res, node_log)
            res = resQueue.get()
        save(node_log, file_lift)

else:
    for (no,file) in enumerate(file_set):
        ip = '193.52.19.26'
        node_log = makeLog('lift2@193.52.19.26')
        dataQueue.put( (0,LIFT2_START_SESSION,() ) )
        otree = etree.parse(file, parser)
        for x in otree.getroot():
            if x.tag == 'entry': 
                x.attrib['client'] = ip
                dataQueue.put( processXMLEntry(x) )
            elif x.tag == 'data-triple-N3' : dataQueue.put( processXMLData(x) )
            elif x.tag == 'end' : dataQueue.put( processXMLEndEntry(x) )
            else: pass
        dataQueue.put( (0,LIFT2_END_SESSION,()  ) )
        i = 1
        res = resQueue.get()
        while res != LIFT2_END_SESSION:
            if res != LIFT2_START_SESSION : 
                i += 1
                addBGP(str(no)+str(i), res, node_log)
            res = resQueue.get()
        file_lift = file[:-4]+'-lift.xml'
        save(node_log, file_lift)





dataQueue.put(None)
dataProcess.join()
entryProcess.join()


# print('Arrêt des processus d' 'analyse')
# ps.stop()

print('Fin')