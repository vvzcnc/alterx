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

__all__ = []

import time
from multiprocessing import Process, Queue
from threading import Thread

QKEY = Queue(-1)
QLED = Queue(-1)


def listener_process(log, key, led):
    while True:
        time.sleep(10)
        log.put_nowait({"name": __name__, "level": logging.INFO,
                        "msg": "Testing", "path": __file__})
        key.put_nowait({"key": "F1", "state": True})
    key.put_nowait(None)


class keyboardListener():
    def listener_thread(self, log, key, led):
        while True:
            try:
                k = key.get()
                if k is None:
                    break
                printVerbose('Key received: %s' % k["key"])
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                printError('Key listener thread error: %s' % e)

    def __init__(self):
        kt = Thread(target=self.listener_thread, args=(QLOG, QKEY, QLED,))
        kt.daemon = True
        kt.start()

        kp = Process(target=listener_process, args=(QLOG, QKEY, QLED,))
        kp.daemon = True
        kp.start()


key_listener = keyboardListener()
