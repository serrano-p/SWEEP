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
# import socket
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
print('origin:',q5)
# http://localhost:5000/lift : serveur TPF LIFT (exemple du papier)
sp = TPFEP(service = 'http://localhost:5000/lift') #'http://localhost:5001/dbpedia_3_9')
sp.setEngine('/Users/desmontils-e/Programmation/TPF/Client.js-master/bin/ldf-client')

q = q6

#sp.caching(True)
try:
  print(sp.query(q))
  #sp.saveCache()
except Exception as e:
  #print(e)
	pass