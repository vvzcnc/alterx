#!/usr/bin/env python3

import socket
import struct

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 5000     # The port used by the server

STOP=0
LIST=1
STATE=2
CHANNEL=3
TRIG=4
RUN=5
CHECK=6
GET=7

HAL_PIN=0
HAL_SIG=1
HAL_PARAMETER=2

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    #packet = struct.pack("BBl",LIST,HAL_PARAMETER,0)
    packet = struct.pack('hhl',GET,HAL_SIG,int('45580',16))
    s.sendall(packet)
    while True:
        data = s.recv(1024)
        if not data:
            break

        print('Received\n%s'%data.decode('utf-8'))
