#!/usr/bin/env python3.6
# coding: utf8
"""
Class to process statistics in a parallel context
"""
#    Copyright (C) 2017 by
#    Emmanuel Desmontils <emmanuel.desmontils@univ-nantes.fr>
#    Patricia Serrano-Alvarado <patricia.serrano-alvarado@univ-nantes.fr>
#    All rights reserved.
#    GPL v 2.0 license.

import sys
import socket

#==================================================

class Socket(object):
    """docstring for Socket"""
    def __init__(self, s=None, port='5002', host = '127.0.0.1'):
        super(Socket, self).__init__()
        if s is None:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            (self.cl_ip, self.cl_port) = ('',0)
            (self.loc_ip,self.loc_port) = (host, port)
        else:
            self.s = s
            (self.cl_ip, self.cl_port) = self.s.getpeername()
            (self.loc_ip,self.loc_port) = self.s.getsockname()
        print ('Socket created')

    def bind(self):
        #Bind socket to local host and port
        try:
            self.s.bind((self.loc_ip, self.loc_port))
        except socket.error as msg:
            print ('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
            sys.exit()   
        print ('Socket bind complete')
        #Start listening on socket
        self.s.listen(10)
        print ('Socket now listening') 

    def accept(self):
        conn, addr = self.s.accept()
        return Socket(conn)

    def connect(self):
        self.s.connect( (self.loc_ip,self.loc_port) )
        (self.cl_ip, self.cl_port) = self.s.getpeername()
        (self.loc_ip,self.loc_port) = self.s.getsockname()

    def close(self):
        self.s.close()

    def send(self,cdc):
        #---
        assert type(cdc) == 'string', 's must be a string'
        self.s.send(cdc)

    def recv(self):
        return self.s.recv(2048)

    def locAddr(self):
        return self.loc_ip + str(self.loc_port)

    def clAddr(self):
        return self.cl_ip + str(self.cl_port)

#==================================================
#==================================================
#==================================================

if __name__ == "__main__":
    print("main ldqp")


