# -*- coding: utf-8 -*-
#
# AlterX GUI - linuxcnc
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

__all__ = ['STAT','COMMAND','ERROR','INI','UPDATER','LINUXCNC']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *
from alterx.gui.qt_bindings import *

import sys
import time

try:
	import linuxcnc as LINUXCNC
	STAT = LINUXCNC.stat()
	COMMAND = LINUXCNC.command()
	ERROR = LINUXCNC.error_channel()
	INI = LINUXCNC.ini(sys.argv[2])
	#POS = LINUXCNC.positionlogger()

except Exception as e:
	printError(_("Failed to import LinuxCNC module: '{}'",e))

class linuxcnc_poll(QThread):
	def run(self):
		stat_old = {}
		while self.running == True:
			time.sleep(0.1)

			try:
				STAT.poll()
				ERROR.poll()
			except LINUXCNC.error, detail:
				printError(_("Failed to poll LinuxCNC stat: '{}'",detail))
				continue

			for s in dir(STAT):
				if not s.startswith('_'):
					if s not in stat_old or stat_old[s] != getattr(STAT,s):
						stat_old[s] = getattr(STAT,s)
						if s in self._observers:
							for h in self._observers[s]:
								h(stat_old[s])

	def connect(self,name,handler):
		if name in self._observers:
			self._observers[name].append(handler)
		else:
			self._observers[name] = [handler]

	def __init__(self):
		QThread.__init__(self)
		self.running = True
		self._observers = {}
		
	def __del__(self):
		self.running = False
		self.wait()

UPDATER = linuxcnc_poll()
