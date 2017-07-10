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

from queue import Empty
import multiprocessing as mp
from ctypes import c_double

import iso8601 # https://pypi.python.org/pypi/iso8601/     http://pyiso8601.readthedocs.io/en/latest/
import datetime as dt
import csv
from tools.tools import *
from tools.Stat import *

from lib.QueryManager import *

from lxml import etree  # http://lxml.de/index.html#documentation
from lib.bgp import *

#==================================================

transform = etree.XSLT(etree.parse('toTrace.xsl'))

#==================================================

class BGP:
    def __init__(self, ref = False):
        self.tp_set = []
        self.input_set = set() # ens. des hash des entrées, pour ne pas mettre 2 fois la même
        self.birthTime = now()
        self.time = now()
        self.client = ''
        self.isRef = ref

    def age(self):
        return now() - self.time

    def toString(self):
        rep = ''
        for ((s,p,o),sm,pm,om) in bgp.tp_set:
                rep +=".\n".join([toStr(s,p,o)])
        return rep

    def print(self):
        #print(serializeBGP2str([ x for (x,sm,pm,om,h) in self.tp_set]))
        print('From:',self.client,' at ',self.time)
        for ((s,p,o),sm,pm,om) in self.tp_set:
            print('\t'+toStr(s,p,o) )

#==================================================

def toStr(s,p,o):
    return serialize2string(s)+' '+serialize2string(p)+' '+serialize2string(o)

#==================================================

SWEEP_IN_ENTRY = 1
SWEEP_IN_DATA = 2
SWEEP_IN_END = 3
SWEEP_IN_QUERY = 4

SWEEP_START_SESSION = -1
SWEEP_END_SESSION = -2
SWEEP_PURGE = -3

SWEEP_WAIT = 1 # in seconds

#==================================================

#==================================================

def processAgregator(in_queue,out_queue, val_queue, ctx):
    timeout = ctx.timeout
    currentTime = now()
    elist = dict()   
    try:
        inq = in_queue.get()
        while inq is not None:
            (id, x, val) = inq
            if x == SWEEP_IN_ENTRY:
                (s,p,o,t,cl) = val
                # time = fromISO(t) # prend pas en compte le 't' de l'entrée pour pouvoir gérer les serveurs TPF concurrents
                time = now()
                currentTime = time #max(currentTime,time)
                elist[id] = (s,p,o,time,cl,set(),set(),set())
            elif x == SWEEP_IN_DATA :
                if id in elist: # peut être absent car purgé
                    (s,p,o,t,c,sm,pm,om) = elist[id]
                    (xs,xp,xo) = val
                    currentTime = max(currentTime,t) + dt.timedelta(microseconds=1)
                    if isinstance(s,Variable): sm.add(xs)
                    if isinstance(p,Variable): pm.add(xp)
                    if isinstance(o,Variable): om.add(xo)
            elif x == SWEEP_IN_END :
                mss = elist.pop(id,None)
                if mss is not None: # peut être absent car purgé
                    out_queue.put( (id, mss) )
            elif x == SWEEP_START_SESSION :
                # print('Agregator - Start Session')
                elist.clear()
                out_queue.put( (id, SWEEP_START_SESSION) )
            elif x == SWEEP_END_SESSION :
                # print('Agregator - End Session')
                for v in elist:
                    out_queue.put( (v, elist.pop(v)) )
                out_queue.put( (id, SWEEP_END_SESSION) )
            elif x == SWEEP_IN_QUERY :
                val_queue.put( (id,val) )
            else: # Impossible...
                pass

            #purge les entrées trop vieilles !
            old = []
            for id in elist:
                (s,p,o,t,c,sm,pm,om) = elist[id]
                if (currentTime - t) > timeout:
                    old.append(id)
            for id in old:
                v = elist.pop(id)
                out_queue.put( (id, v) )
            inq = in_queue.get()
    except KeyboardInterrupt:
        # penser à purger les dernières entrées -> comme une fin de session
        pass        
    out_queue.put(None)
    val_queue.put(None)


#==================================================
#appel chercher( (s,p,o),{bs:bsm,bp:bpm,bo:bom}, dict, set )
def chercher(tab,ref,tp,d,res):
    #print(tab,'===> Ref:',ref); print(tab,'---> tp:',tp); print(tab,'---> d:',d); print(tab,'---> res:',res)
    if len(ref)==0:
        #print(tab,'|--> réponse !')
        ok = 0
        for (i,j) in d.items():
            if i!=j: ok += 1 
        if ok>0: 
            d2 = d.copy()
            d2['nb']=ok
            res.append(d2)
    else:
        i = ref[0]
        reste = ref[1:]
        if isinstance(i,Variable):
            #print(tab,'|--> Variable !')
            d[i]=i
            chercher(tab+'\t',reste, tp, d, res)
            d.pop(i)
        else:
            for (j,bj) in tp.copy().items() :
                if i in bj:
                    #print(tab,'|--> choix =>',i,j)
                    d[i] = j
                    tp.pop(j)
                    chercher(tab+'\t',reste,tp,d,res)
                    tp[j]=bj
                    d.pop(i) 
                else: 
                    #print(tab,'|--> pas bon =>',i,j)
                    pass
            d[i]=i
            #print(tab,'|--> i==i:',i)
            chercher(tab+'\t',reste, tp, d, res) 
            d.pop(i)               

def processBGPDiscover(in_queue, out_queue, val_queue, ctx):
    gap = ctx.gap
    BGP_list = []
    currentTime = now()
    try:
        entry = in_queue.get()
        while entry != None:
            (id, val) = entry
            if val==SWEEP_PURGE:
                pass
            elif val == SWEEP_START_SESSION:
                # print('BGPDiscover - Start Session')
                BGP_list.clear()
                out_queue.put(SWEEP_START_SESSION)
            elif val == SWEEP_END_SESSION:
                # print('BGPDiscover - End Session')
                for bgp in BGP_list:
                    out_queue.put(bgp)
                    val_queue.put((0,bgp))
                BGP_list.clear()
                out_queue.put(SWEEP_END_SESSION)
            else :
                (s,p,o,time,client,sm,pm,om) = val
                currentTime = time
                print('Etude de :',toStr(s,p,o))
                if not(isinstance(s,Variable) and isinstance(p,Variable) and isinstance(o,Variable) ):
                    h = hash(toStr(s,p,o))
                    #print(currentTime)
                    trouve = False
                    for (i,bgp) in enumerate(BGP_list):
                        # Si c'est le même client, dans le gap et un TP identique n'a pas déjà été utilisé pour ce BGP
                        print('\t Etude avec BGP ',i)
                        if (client == bgp.client) and (currentTime - bgp.time <= gap) and (h not in bgp.input_set): 
                            ref_couv = 0
                            # on regarde si une constante du sujet et ou de l'objet est une injection
                            for tp in  bgp.tp_set:
                                ( (bs, bp, bo), bsm, bpm, bom) = tp
                                print('\t\t Comparaison avec :',toStr(bs,bp,bo))
                                print('\t\tbsm:',bsm) ; print('\t\tbpm:',bpm); print('\t\tbom:',bom)

                                #On recherche les mappings possibles : s-s, s-p, s-o, etc.
                                d = None
                                res = list()
                                chercher('',(s,p,o), dict({bs:bsm,bp:bpm,bo:bom}), dict(),res)
                                # print('==='); pprint(res); print('===')
                                couv = 0
                                for x in res:
                                    c = x['nb']
                                    if c > couv:
                                        couv = c
                                        d = x

                                nb_map = 0
                                nb_eq = 0
                                if d is not None:# on cherche à éviter d'avoir le même TP
                                    for (i,j) in ( (s,bs) , (p,bp) , (o,bo)) :
                                        if (d[i] != i) and isinstance(j,Variable):
                                            nb_map +=1
                                        else:
                                            if (i == j) or (isinstance(i,Variable) and isinstance(j,Variable)):
                                                # le second opérande pose pb car interdit : ?s1 p ?o1 . ?s1 p ?o2 . :-(
                                                nb_eq +=1
                                            else:
                                                pass

                                if (couv > ref_couv) and (nb_map+nb_eq !=3) : 
                                    trouve = True
                                    ref_couv = couv
                                    ref_d = d
                                    break

                            if trouve:
                                print('\t\t ok avec :',toStr(bs,bp,bo) )
                                (s2, p2, o2) = (ref_d[s],ref_d[p],ref_d[o])
                                print('\t\t |-> ',toStr(s2,p2,o2) )
                                inTP = False
                                # peut-être que un TP similaire a déjà été utilisé pour une autre valeur... alors pas la peine de le doubler
                                for  ( (b2s, b2p, b2o), b2sm, b2pm, b2om) in  bgp.tp_set:
                                    (inTP,m) = egal((s2, p2, o2) ,(b2s, b2p, b2o)) 
                                    if inTP: break
                                if not(inTP):
                                    if (s==ref_d[s]) and isinstance(s,Variable): s2 = Variable("s"+str(id).replace("-","_"))
                                    if (p==ref_d[p]) and isinstance(p,Variable): p2 = Variable("p"+str(id).replace("-","_"))
                                    if (o==ref_d[o]) and isinstance(o,Variable): o2 = Variable("o"+str(id).replace("-","_"))
                                    bgp.tp_set.append( ((s2,p2,o2),sm,pm,om) )
                                    print('\t\t Ajout de ',toStr(s2,p2,o2))
                                    bgp.input_set.add(h)
                                else: 
                                    print('\t Déjà présent avec ',toStr(b2s, b2p, b2o))
                                    pass
                                if ctx.optimistic: bgp.time = currentTime
                                break
                        else: 
                            if (client == bgp.client) and (currentTime - bgp.time <= gap):
                                print('\t\t Déjà ajouté')
                                pass

                    # pas trouvé => nouveau BGP ?
                    if not(trouve):
                        bgp = BGP()     
                        if isinstance(s,Variable):
                            s = Variable("s"+str(id).replace("-","_"))
                        if isinstance(p,Variable):
                            p = Variable("p"+str(id).replace("-","_"))
                        if isinstance(o,Variable):
                            o = Variable("o"+str(id).replace("-","_"))
                        print('\t Création de ',toStr(s,p,o),'-> BGP ',len(BGP_list))
                        bgp.tp_set.append( ((s,p,o), sm,pm,om) )
                        bgp.input_set.add(h)
                        bgp.time = currentTime
                        bgp.birthTime = currentTime
                        bgp.client = client
                        BGP_list.append(bgp)

            # envoyer les trop vieux !
            old = []
            recent = []
            for bgp in BGP_list:
                # print(currentTime,bgp.time)
                if (currentTime - bgp.time > gap): old.append(bgp)
                else: recent.append(bgp)
            for bgp in old :  
                out_queue.put(bgp)
                val_queue.put((0,bgp))
            BGP_list = recent

            try:
                entry = in_queue.get(timeout=gap.total_seconds())#SWEEP_WAIT)
            except Empty as e:
                # print('purge')
                currentTime = currentTime + gap #dt.timedelta(seconds= SWEEP_WAIT)
                entry = (0,SWEEP_PURGE)
    except KeyboardInterrupt:
        # penser à purger les derniers BGP ou uniquement autoutr du get pour gérer fin de session
        pass
    out_queue.put(None)

#==================================================

def testPrecisionRecallBGP(queryList, bgp):
    best = 0
    test = [ tp for (tp, sm,pm,om) in bgp.tp_set ]
    # print(test)
    for i in queryList:
        ( (time,ip,query,qbgp),old_bgp,precision,recall) = queryList[i]
        # print(qbgp)
        if ip == bgp.client:
            (precision2, recall2, inter, mapping) = calcPrecisionRecall(qbgp,test)
            if  precision2*recall2 > precision*recall:
                best = i
                best_precision = precision2
                best_recall = recall2
    if best > 0:
        ( (time,ip,query,qbgp),old_bgp,precision,recall) = queryList[best]
        queryList[best] = ( (time,ip,query,qbgp),bgp,best_precision,best_recall)
        # essayer de replacer le vieux...
        if old_bgp is not None: 
            return testPrecisionRecallBGP(queryList,old_bgp)
        else: return None
    else:
        return bgp

def addBGP2Rank(bgp, nquery, line, ranking):
    ok = False
    for (i, (d, n, query, ll)) in enumerate(ranking):
        if bgp == d:
            ok = True
            break
    if ok:
        ll.add(line)
        if query == '': query = nquery
        ranking[i] = (d, n+1, query, ll)
    else:
        ranking.append( (bgp, 1 , nquery, {line}) )

def processValidation(in_queue, ctx):
    timeout = ctx.timeout
    gap = ctx.gap
    currentTime = now()
    queryList = OrderedDict()
    try:
        inq = in_queue.get()
        while inq is not None:
            (id, val) = inq

            if id > 0:
                ctx.stat['nbQueries'] +=1 
                (time,ip,query,qbgp) = val
                currentTime = time
                # print('New query', val)
                (precision, recall, bgp) = (0,0, None)
                queryList[id] = ( (time,ip,query,qbgp),bgp,precision,recall)
            elif id == 0:
                # print('A BGP')
                ctx.stat['nbBGP'] +=1
                bgp = val
                currentTime = bgp.birthTime # or bgp.time ?
                bgp = testPrecisionRecallBGP(queryList,bgp)
                if bgp is not None:
                    ctx.memory.append( (0, bgp.birthTime, bgp.client, None, bgp, 0, 0) )
                    addBGP2Rank(canonicalize_sparql_bgp([x for (x,sm,pm,om) in bgp.tp_set]), '', id, ctx.rankingBGPs)
            else:
                pass

            # Suppress older queries
            old = []
            for id in queryList:
                ( (time,ip,query,qbgp),bgp,precision,recall) = queryList[id]
                # print(currentTime,' vs. ',time)
                if currentTime - time > timeout:
                    old.append(id)
            for id in old:
                ( (time,ip,query,qbgp),bgp,precision,recall) = queryList.pop(id)
                print('---',precision,'/',recall,'---')
                print(query)
                print('---')
                ctx.memory.append( (id, time, ip, query, bgp, precision, recall) )
                ctx.stat['sumRecall'] += recall
                ctx.stat['sumPrecision'] += precision
                ctx.stat['sumQuality'] += (recall+precision)/2
                if bgp is not None: 
                    print(".\n".join([ toStr(s,p,o) for ((s,p,o), sm,pm,om ) in bgp.tp_set ]))
                    ctx.stat['sumSelectedBGP'] += 1
                    #---
                    assert ip == bgp.client, 'Client Query différent de client BGP'
                    #---
                    addBGP2Rank(qbgp, query, id, ctx.rankingQueries)
                    addBGP2Rank(canonicalize_sparql_bgp([x for (x,sm,pm,om) in bgp.tp_set]), query, id, ctx.rankingBGPs)
                else:
                    print('Query not assigned : ', query)
                print('--- @'+ip+' ---')

            try:
                inq = in_queue.get(timeout= gap.total_seconds())#SWEEP_WAIT)
            except Empty as e:
                # print('purge')
                inq = (-1, None)
                currentTime = currentTime + gap #dt.timedelta(seconds=SWEEP_WAIT)
    except KeyboardInterrupt:
        # penser à afficher les dernières queries ou uniquement autour du get pour fin de session
        pass

#==================================================

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

def processStat(ctx, duration) :
    try:
        while True:
            time.sleep(duration)
            # print('Saving memory')
            ctx.saveMemory()
            # if ctx.stat['nbQueries']>0:
            #     ctx.avgPrecision.value = ctx.stat['sumPrecision']/ctx.stat['nbQueries']
            #     ctx.avgRecall.value = ctx.stat['sumRecall']/ctx.stat['nbQueries']
            #     ctx.avgQual.value = ctx.stat['sumQuality']/ctx.stat['nbQueries']
            #     # print('Avg Recall:%.3f ; Avg Precision:%.3f ; Avg Quality:%.3f' % (ctx.avgRecall.value, ctx.avgPrecision.value,ctx.avgQual.value))
            # if ctx.stat['nbBGP']>0 :                
            #     ctx.Acuteness.value = ctx.stat['sumSelectedBGP'] / ctx.stat['nbBGP']
            # print('Nb queries:%d ; Nb unused BGP:%d ; Acuteness:%2.3f' % (ctx.stat['nbQueries'], max(0,ctx.stat['nbBGP'] - ctx.stat['nbQueries']),ctx.Acuteness.value  ))
    except KeyboardInterrupt:
        pass

#==================================================
class SWEEP:
    def __init__(self,gap):
        #---
        assert isinstance(gap,dt.timedelta)
        #---
        self.gap = gap
        self.timeout = gap # + dt.timedelta(seconds=SWEEP_WAIT)
        self.optimistic = False # màj de la date du BGP avec le dernier TP reçu ?

        manager = mp.Manager()
        self.memory = manager.list()
        self.rankingBGPs = manager.list()
        self.rankingQueries = manager.list()
        self.avgPrecision = manager.Value('f',0.0)
        self.avgRecall = manager.Value('f',0.0)
        self.avgQual = manager.Value('f',0.0)
        self.Acuteness = manager.Value('f',0.0)
        self.stat = manager.dict({'sumRecall':0, 'sumPrecision':0, 'sumQuality':0, 'nbQueries':0, 'nbBGP':0, 'sumSelectedBGP':0})

        self.dataQueue = mp.Queue()
        self.entryQueue = mp.Queue()
        self.validationQueue = mp.Queue()
        self.resQueue = mp.Queue()

        self.dataProcess = mp.Process(target=processAgregator, args=(self.dataQueue, self.entryQueue, self.validationQueue,self))
        self.entryProcess = mp.Process(target=processBGPDiscover, args=(self.entryQueue, self.resQueue, self.validationQueue, self))
        self.validationProcess = mp.Process(target=processValidation, args=(self.validationQueue, self))
        self.statProcess = mp.Process(target=processStat, args=(self, SWEEP_WAIT*3))

        self.dataProcess.start()
        self.entryProcess.start()
        self.validationProcess.start()
        self.statProcess.start()

    def setTimeout(self,to):
        self.timeout = to

    def swapOptimistic(self) :
        self.optimistic = not(self.optimistic)

    def startSession(self):
        self.dataQueue.put(  (0,SWEEP_START_SESSION,() ) )

    def endSession(self):
        self.dataQueue.put( (0,SWEEP_END_SESSION,()  ) )

    def put(self,v):
        self.dataQueue.put(v)

    def get(self):
        try:
            r = self.resQueue.get()
            if r == SWEEP_START_SESSION:
                return self.get()
            if r == SWEEP_END_SESSION :
                return None
            else: return r
        except KeyboardInterrupt:
            return None

    def stop(self):
        self.dataQueue.put(None)
        self.dataProcess.join()
        self.entryProcess.join()
        self.validationProcess.join()
        self.statProcess.join()
        # self.saveMemory()

    def saveMemory(self):
        file = 'sweep.csv' # (id, time, ip, query, bgp, precision, recall) 
        sep='\t'
        with open(file,"w", encoding='utf-8') as f:
            fn=['id','time', 'ip', 'query', 'bgp', 'precision', 'recall']
            writer = csv.DictWriter(f,fieldnames=fn,delimiter=sep)
            writer.writeheader()
            for (id, time, ip, query, bgp, precision, recall) in self.memory:
                if bgp is not None :
                    bgp_txt = ".\n".join([ toStr(s,p,o) for ((s,p,o), sm,pm,om ) in bgp.tp_set ])
                else:
                    bgp_txt = "..."
                s = { 'id':id, 'time':time, 'ip':ip, 'query':query, 'bgp':bgp_txt, 'precision':precision, 'recall':recall }
                writer.writerow(s)

class SWEEP_XML(SWEEP):
    """docstring for SWEEP_XML"""
    def __init__(self, gap):
        super(SWEEP_XML, self).__init__(gap)
        self.qm = QueryManager(modeStat = False)
        self.qId = 0

    def processXMLEntry(self,x):
        id = x.attrib['id']
        if x[0].attrib['type']=='var' : x[0].set('val','s')
        if x[1].attrib['type']=='var' : x[1].set('val','p')
        if x[2].attrib['type']=='var' : x[2].set('val','o')
        s = unSerialize(x[0])
        p = unSerialize(x[1])
        o = unSerialize(x[2])
        return (id, SWEEP_IN_ENTRY, (s,p,o,x.attrib['time'],x.attrib['client']) )

    def processXMLEndEntry(self,x):
        id = x.attrib['id']
        return (id, SWEEP_IN_END, () )

    def processXMLData(self, x):
        id = x.attrib['id']
        xs = unSerialize(x[0])
        xp = unSerialize(x[1])
        xo = unSerialize(x[2])
        return (id, SWEEP_IN_DATA, (xs, xp, xo))  

    def processXMLQuery(self,x):
        # print(etree.tostring(x))
        query = x.text
        time = now()# fromISO(x.attrib['time']) 
        (bgp,nquery) = self.qm.extractBGP(query)
        ip = x.attrib['client']
        self.qId +=1
        return (self.qId, SWEEP_IN_QUERY, (time,ip,nquery,bgp) )


    def put(self,x):
        if x.tag == 'entry': self.dataQueue.put( self.processXMLEntry(x) )
        elif x.tag == 'data-triple-N3' : self.dataQueue.put( self.processXMLData(x) )
        elif x.tag == 'end' : self.dataQueue.put( self.processXMLEndEntry(x) )
        elif x.tag == 'query': self.dataQueue.put( self.processXMLQuery(x) )
        else:
            pass
       
#==================================================
#==================================================
#==================================================
if __name__ == "__main__":
    print("main sweep")


