# -*- coding: utf-8 -*-
#
# AlterX GUI - ascope - linuxcnc rt component for oscilloscope
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

__all__  =  ["AScope"]

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common.util import *

import socket
import struct

class AScope():
    HOST = '127.0.0.1'  # The server's hostname or IP address
    PORT = 27267     # The port used by the server

    OSC_STOP = 0
    OSC_LIST = 1
    OSC_STATE = 2
    OSC_CHANNEL = 3
    OSC_TRIG = 4
    OSC_RUN = 5
    OSC_CHECK = 6
    OSC_GET = 7

    SAMPLE_IDLE = 0
    SAMPLE_RUN = 1
    SAMPLE_COMPLETE = 2
    SAMPLE_HIGH = 3
    SAMPLE_LOW = 4
    SAMPLE_CHANGE = 5

    HAL_PIN = 0
    HAL_SIG = 1
    HAL_PARAMETER = 2
    
    @classmethod
    def send_packet(cls,control,cmd,stype,value):
        answer = u""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.connect((cls.HOST, cls.PORT))
            packet = struct.pack( "lBBd" if type(value) == float else "lBBl",
                control, cmd, stype, value )
 
            s.sendall(packet)
            s.settimeout(1.0)
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

    @classmethod
    def get_type_text(cls,stype):
        t={'-1':'NULL','1':'BIT','2':'FLOAT','3':'S32','4':'U32','5':'PORT'}
        if stype in t:
            return t[stype]   
        else:
            return stype

    @classmethod 
    def get_dir_text(cls,sdir):
        t={'-1':'None','16':'In','32':'Out','48':'IO','64':'RO','192':'RW'}
        if sdir in t:
            return t[sdir] 
        else:
            return sdir
