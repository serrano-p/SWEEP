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
# from threading import *

# import multiprocessing as mp

# import datetime as dt
# import iso8601 # https://pypi.python.org/pypi/iso8601/     http://pyiso8601.readthedocs.io/en/latest/

# import re
import argparse

from tools.tools import *
from tools.Endpoint import *

# from lxml import etree  # http://lxml.de/index.html#documentation
# from lib.bgp import *

# from io import StringIO


#==================================================
#==================================================
#==================================================

q5 = """
prefix : <http://www.example.org/lift2#> 
select ?s ?o 
where {
	?s :p3 "titi" . 
	?s :p1 ?o . 
	?s :p4 "tata"
}
"""

q6 = """
prefix : <http://www.example.org/lift2#>  
select ?s ?o where {
  ?s :p2 "toto" . 
  ?s :p1 ?o .
}
"""

q = q6

print('origin:',q)
# http://localhost:5000/lift : serveur TPF LIFT (exemple du papier)
# http://localhost:5001/dbpedia_3_9 server dppedia si : ssh -L 5001:172.16.9.3:5001 desmontils@172.16.9.15


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", 5002))

print("Envoie test:")
mess = '<query time="'+date2str(now())+'"><![CDATA['+q+']]></query>'
s.send(mess.encode('utf8'))

sp = TPFEP(service = 'http://localhost:5000/lift') 
sp.setEngine('/Users/desmontils-e/Programmation/TPF/Client.js-master/bin/ldf-client')
try:
  print(sp.query(q))
except Exception as e:
	print('Exception',e)

