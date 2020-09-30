#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# AlterX GUI - keyboard listener
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

import logging
from alterx.common.compat import *
from alterx.common.util import *
from alterx.core.linuxcnc import *

__all__ = []

import time
import pyudev
import serial
import crcmod.predefined
import struct

from multiprocessing import Process, Queue
from threading import Thread

QKEY = Queue(-1)
QLED = Queue(-1)
QOUTPUT = Queue(-1)

def listener_process(log, key, led, board):
    if not board:
        log.put_nowait({"name": __name__, "level": logging.INFO,
                        "msg": "Serial error: Serial board not found", 
                        "path": __file__})
        key.put_nowait(None)
        return

    while True:
        keys = {}
        try:
            l = led.get()
            if l is None:
                break
        
            hash = crcmod.predefined.mkPredefinedCrcFun('crc-8-maxim')
            ser = serial.Serial(port=board,timeout=0.01,write_timeout=0.01)

            def bool_list_to_byte(list):
                num=0
                for idx,bit in enumerate(list):
                    num+=bit*2**idx

                num=str(struct.pack("B",num))
                return num
          
            cmd = bool_list_to_byte(l)

            cmd=b"\xAB\xCD"+cmd+struct.pack("B",hash(cmd))+b"\xDC\xBA"
            ser.write(cmd)
            answer = bytearray(ser.read_until("\x0D\x0A"))

            if len(answer) == 11:
                crc_r = struct.unpack("B",answer[8:9])[0]
                crc = hash(str(answer[:8]))
                if crc == crc_r:
                    spindle = struct.unpack("<H",answer[:2])[0]
                    feedrate = struct.unpack("<H",answer[2:4])[0]
                    encoder = struct.unpack("<H",answer[4:6])[0]
                    button = struct.unpack("B",answer[6:7])[0]
                    inputs = struct.unpack("B",answer[7:8])[0]
                    
                    keys["spindlerate"] = spindle/4096.0*130.0
                    keys["feedrate"] = feedrate/4096.0*130.0
                    keys["encoder"] = encoder
                    
                    def int_to_bool_list(num):
                        return [bool(num & (1<<n)) for n in range(8)]

                    list_inputs = int_to_bool_list(inputs)
                    
                    keys["fast"] = list_inputs[0]
                    keys["inputs"] = list_inputs[1:]
                    keys["button"] = button
            ser.close()
        except (KeyboardInterrupt, SystemExit):
            return
        except Exception,e:
            log.put_nowait({"name": __name__, "level": logging.INFO,
                            "msg": "Serial error: %s"%e, "path": __file__})
                            
        key.put_nowait(keys)
    key.put_nowait(None)

class keyboardListener():
    def __init__(self):
        self.init_keybindings()
    
        kt = Thread(target=self.listener_thread, args=(QLOG, QKEY, QLED, QOUTPUT))
        kt.daemon = True
        kt.start()

        kp = Process(target=listener_process, args=(QLOG, QKEY, QLED, 
                                                                self.keyboard,))
        kp.daemon = True
        kp.start()

    def update_output_state(self, number, state):
        self.keyboard_cmd_list[number] = state
        QOUTPUT.put_nowait(self.keyboard_cmd_list)

    def init_keybindings( self ):
        context=pyudev.Context()
        self.keyboard=None
        self.keyboard_cmd_list= [False,False,False,False,False,False,False,False]
        self.keyboard_answer = {}

        UPDATER.add("keyboard_set_output_state",[0,0])
        UPDATER.signal("keyboard_set_output_state",lambda s: self.update_output_state(s[0],s[1]))

        for device in context.list_devices(subsystem='tty',ID_VENDOR_ID='0483',
                                    ID_MODEL_ID='5740',ID_MODEL='BK-A05K-D'):
            self.keyboard=device['DEVNAME']

    def listener_thread(self, log, key, led, output):
        last_key = {}
        keyboard_cmd_list = [False,False,False,False,False,False,False,False]
        
        while True:
            time.sleep(0.01)
            try:
                if not output.empty():
                    keyboard_cmd_list = output.get()
                    
                led.put_nowait(keyboard_cmd_list)
            
                key_answer = key.get()
                if key_answer is None:
                    break
                    
                for k in key_answer:
                    #printVerbose('Key [%s] received: %s' % (k, key_answer[k]))
                    if k in last_key and key_answer[k] != last_key[k]:
                        if k == "button":
                            UPDATER.emit('display_button_binding', key_answer[k])
                        elif k == "spindlerate":
                            COMMAND.spindleoverride(round((key_answer[k]/1.25))/100.0)
                        elif k == "feedrate":
                            speed = round((key_answer[k]/1.25))/100.0
                            COMMAND.feedrate(speed)
                            COMMAND.rapidrate(speed)
                            UPDATER.emit('jog_speed', speed)
                        elif k == "inputs":
                            UPDATER.emit('display_inputs_binding', key_answer[k])
                        elif k == "encoder":
                            UPDATER.emit('display_encoder_binding', key_answer[k])
                        elif k == "fast":
                            UPDATER.emit('jog_fast', key_answer[k])

                    last_key[k] = key_answer[k]
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                printError('Key listener thread error: %s' % e)


key_listener = keyboardListener()
