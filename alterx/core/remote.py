# -*- coding: utf-8 -*-
#
# AlterX GUI - remote control
#
# Copyright 2020-2020 uncle-yura uncle-yura@tuta.io
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
from __future__ import division, absolute_import, print_function, unicode_literals

__all__  =  ["RemoteControl"]

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common.util import *
from alterx.gui.qt_bindings import *

import socket
import subprocess

class RemoteControl(QObject):
    HOST = '127.0.0.1'  # The server's hostname or IP address
    PORT = 17366         # The port used by the server
    
    def __init__(self):
        QObject.__init__(self, parent=None)
        
        self.sock = QTcpServer()
        self.sock.newConnection.connect(self.on_new_connection)
        self.sock.listen(QHostAddress.LocalHost, type(self).PORT)
        
    def on_ready_read(self):
        msg = u""
        while True:
            data = self.client.readAll()
            msg += toUnicode(data)
            if not data:
                break
        
        data = u"No answer\n"
        if "halcmd" in msg:
            try:
                data = subprocess.check_output(msg.split(' '),
                                                stderr=subprocess.STDOUT)
            except Exception as e:
                printInfo(_("Failed to execute cmd: {}",e))
                data = e.output
                
        self.client.write(data)
        self.client.close()

    def on_new_connection(self):
        while self.sock.hasPendingConnections():
            self.client = self.sock.nextPendingConnection()
            self.client.readyRead.connect(self.on_ready_read)
            
    @classmethod
    def send_packet(cls,msg):
        answer = ""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.connect((cls.HOST, cls.PORT))
            s.sendall(msg.encode())
            while True:
                data = s.recv(1024)
                answer += data.decode('utf-8')
                if not data:
                    break
        except Exception as e:
            printInfo(_("Failed to send packet: {}",e))
        finally:
            s.close()

        return answer
