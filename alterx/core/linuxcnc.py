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

__all__ = ['STAT','COMMAND','ERROR','INI','UPDATER','LINUXCNC','INFO','PREF']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common.preferences import *
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

PREF = Preferences(INI.find("DISPLAY", "PREFERENCE_FILE_PATH"))

class linuxcnc_info():
	def __init__(self):
		if INI.find('TRAJ','LINEAR_UNITS') in ('mm','metric'):
			self.machine_is_metric = True
		else:
			self.machine_is_metric = False

		self.coordinates = INI.find('TRAJ','COORDINATES').split(' ')

		self.machine_is_lathe = True if INI.find('DISPLAY','LATHE') else False

		self.get_metric = lambda: False if STAT.program_units == 1 else True

INFO = linuxcnc_info()

class linuxcnc_poll(QTimer):
	#'One to many' item check
	def run(self):
		#while self.running == True:
		#	time.sleep(0.1)

		try:
			STAT.poll()
			ERROR.poll()
		except LINUXCNC.error, detail:
			printError(_("Failed to poll LinuxCNC stat: '{}'",detail))
			#continue
			return

		for s in dir(STAT):
			if not s.startswith('_'):
				if s not in self.stat_old or self.stat_old[s] != getattr(STAT,s):
					self.stat_old[s] = getattr(STAT,s)
					if s in self._observers:
						for h in self._observers[s]:
							try:
								h(self.stat_old[s])
							except Exception as e:
								printError(_("Failed to execute '{}' handler {}: '{}'",s,h,e))

		for name in self.custom_signals:
			if self.custom_signals[name] != self.custom_signals_old[name] and name in self._observers:
				self.custom_signals_old[name] = self.custom_signals[name]

				for h in self._observers[name]:
					try:
						h(self.custom_signals_old[name])
					except Exception as e:
						printError(_("Failed to execute '{}' handler {}: '{}'",name,h,e))

	#'Many to one' item check
	def check(self,name): 
		if name in self.custom_signals and self.custom_signals[name] != self.custom_signals_old[name]:
			self.custom_signals_old[name] = self.custom_signals[name]
			return True
		return False
				
	#Emit custom signal		
	def emit(self, name, value=None):
		if name in self.custom_signals:
			if value is None and self.custom_signals[name] == self.custom_signals_old[name]:
				value = not self.custom_signals[name]
			
			self.custom_signals[name] = value
		else:
			printError(_("Failed emit signal. Signal '{}' no exist",name))

	#Create custom signal in database
	def add(self,name,value=False):
		if name not in self.custom_signals:
			self.custom_signals[name] = value
			self.custom_signals_old[name] = value
		else:
			printError(_("Failed add signal. Signal '{}' already exist",name))

	#Add signal to 'one to many' database
	def connect(self,name,handler):
		if name in self._observers:
			self._observers[name].append(handler)
		else:
			self._observers[name] = [handler]

	def __getattr__(self, name):
		try:
			return self.custom_signals[name]
		except Exception as e:
			printError(_("Failed get atribute {}: {}",name,e))
		return None

	def __init__(self):
		QTimer.__init__(self)
		self.timeout.connect(self.run)
		#self.running = True
		self.stat_old = {}
		self._observers = {}
		self.custom_signals = {}
		self.custom_signals_old = {}
		
	def __del__(self):
		#self.running = False
		self.wait()

UPDATER = linuxcnc_poll()
