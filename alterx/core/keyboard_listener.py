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
            ser = serial.Serial(port=board,timeout=0.03,write_timeout=0.03)

            def bool_list_to_byte(list):
                num=0
                for idx,bit in enumerate(list):
                    num+=bit*2**idx

                num=str(struct.pack("B",num))
                return num
          
            cmd = bool_list_to_byte(l)

            cmd=b"\xAB\xCD"+cmd+struct.pack("B",hash(cmd))+b"\xDC\xBA"
            ser.write(cmd)
            answer = bytearray(ser.read_until(b"\x0D\x0A"))

            if len(answer) == 15:
                crc_r = struct.unpack("B",answer[12:13])[0]
                crc = hash(str(answer[:12]))
                if crc == crc_r:
                    spindle = struct.unpack("<H",answer[:2])[0]
                    feedrate = struct.unpack("<H",answer[2:4])[0]
                    rapidrate = struct.unpack("<H",answer[4:6])[0]
                    temperature = struct.unpack("<H",answer[6:8])[0]
                    encoder = struct.unpack("<H",answer[8:10])[0]
                    button = struct.unpack("B",answer[10:11])[0]
                    inputs = struct.unpack("B",answer[11:12])[0]
                    
                    keys["spindlerate"] = spindle/40.0
                    keys["feedrate"] = feedrate/40.0
                    keys["rapidrate"] = rapidrate/40.0
                    keys["temperature"] = temperature/40.0
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

    def set_outputs(self, signal):
        result = [True if c == '1' else False for c in signal]
        QOUTPUT.put_nowait(result)
        
    def init_keybindings( self ):
        context=pyudev.Context()
        self.keyboard=None

        UPDATER.add("keyboard_set_output_state")
        UPDATER.signal("keyboard_set_output_state", self.set_outputs)

        for device in context.list_devices(subsystem='tty',ID_VENDOR_ID='0483',
                                    ID_MODEL_ID='5740',ID_MODEL='BK-A05K-D'):
            self.keyboard=device['DEVNAME']

    def listener_thread(self, log, key, led, output):
        last_key = {}
        keyboard_cmd_list = [False,False,False,False,False,False,False,False]
        
        while True:
            time.sleep(0.05)
            try:
                if not output.empty():
                    keyboard_cmd_list = output.get()
                    
                led.put_nowait(keyboard_cmd_list)
            
                key_answer = key.get()
                if key_answer is None:
                    break
                    
                for k in key_answer:
                    #printVerbose('Key [%s] received: %s' % (k, key_answer[k]))
                    if k not in last_key or key_answer[k] != last_key[k]:
                        if k == "button":
                            UPDATER.emit('display_button_binding', key_answer[k])
                        elif k == "spindlerate":
                            speed = key_answer[k]
                            if speed > 100:
                                speed = 100
                            UPDATER.emit('display_spindlerate', round(speed))
                        elif k == "feedrate":
                            speed = key_answer[k]
                            if speed > 100:
                                speed = 100
                            UPDATER.emit('display_feedrate', round(speed))
                        elif k == "rapidrate":
                            speed = key_answer[k]
                            if speed > 100:
                                speed = 100
                            UPDATER.emit('display_rapidrate', round(speed))
                        elif k == "temperature":
                            speed = key_answer[k]
                            if speed > 100:
                                speed = 100
                            UPDATER.emit('display_temperature', round(speed))
                        elif k == "inputs":
                            UPDATER.emit('display_inputs_binding', key_answer[k])
                        elif k == "encoder":
                            UPDATER.emit('display_encoder_binding', key_answer[k])
                        elif k == "fast":
                            UPDATER.emit('display_jog_fast', key_answer[k])

                    last_key[k] = key_answer[k]
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                printError('Key listener thread error: %s' % e)


key_listener = keyboardListener()
