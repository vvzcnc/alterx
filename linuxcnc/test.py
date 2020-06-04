#!/usr/bin/env python3

import socket
import struct

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 5000     # The port used by the server

OSC_STOP=0
OSC_LIST=1
OSC_STATE=2
OSC_CHANNEL=3
OSC_TRIG=4
OSC_RUN=5
OSC_CHECK=6
OSC_GET=7

HAL_PIN=0
HAL_SIG=1
HAL_PARAMETER=2

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect((HOST, PORT))
    packet = struct.pack("BBl",OSC_LIST,HAL_PARAMETER,0)
    #packet = struct.pack('hhl',OSC_GET,HAL_SIG,int('45580',16))
    s.sendall(packet)
    while True:
        data = s.recv(1024)
        if not data:
            break

        print('Received\n%s'%data.decode('utf-8'))
except Exception as e:
    print(e)
finally:
    s.close()
