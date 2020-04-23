# -*- coding: utf-8 -*-
#
# AlterX GUI - utils
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

__all__ = [
	"printDebug",
	"printVerbose",
	"printInfo",
	"printWarning",
	"printError",
	"logListener",
	"QLOG",
	]

from alterx.common.compat import *
import contextlib

import logging
import logging.handlers
from threading import Thread
from multiprocessing import Queue

QLOG = Queue(-1)

def singleton(class_):
	class class_w(class_):
		_instance = None
		def __new__(class_, *args, **kwargs):
			if class_w._instance is None:
				class_w._instance = super(class_w,class_).__new__(class_,*args,**kwargs)
				class_w._instance._sealed = False
			return class_w._instance
		def __init__(self, *args, **kwargs):
			if self._sealed:
				return
			super(class_w, self).__init__(*args, **kwargs)
			self._sealed = True
			class_w.__name__ = class_.__name__
	return class_w

@singleton
class logListener(object):
	LOG_NONE	= 0
	LOG_DEBUG	= 10
	LOG_INFO	= 20
	LOG_WARNING	= 30
	LOG_ERROR	= 40
	LOG_CRITICAL	= 50

	verbose = False
	loglevel = LOG_WARNING

	def __init__(self,path=None,loglevel=LOG_WARNING):
		self.loglevel=loglevel
		FORMAT = '%(asctime)s %(levelname)-8s %(name)s: %(message)s'

		logging.basicConfig(level=self.loglevel,format=FORMAT,datefmt="%Y-%m-%d %H:%M:%S")
		root = logging.getLogger()

		try:
			handler = logging.handlers.RotatingFileHandler(path, 'a', 1000000, 10)
			formatter = logging.Formatter(FORMAT)
			handler.setFormatter(formatter)
			root.addHandler(handler)
		except Exception as e:
			print("Log file handler creating failed")

		listener = Thread(target=self.listener_thread,args=(QLOG,))
		listener.daemon = True
		listener.start()

	def listener_thread(self,queue):
		while True:
			try:
				record = queue.get()
				if record is None:
					break
				record = logging.LogRecord(record["name"],record["level"],record["path"],0,record["msg"],(),None)
				logger = logging.getLogger(record.name)
				logger.handle(record)
			except (KeyboardInterrupt, SystemExit):
				raise
			except Exception as e:
				printError('Log listener thread error: %s'%e)

	def printLog(self,level,text):
		if self.log is not None:
			self.log.log(level,text)
		else:
			print("Logging is not configured yet!\n Message: \n%s"%text)
	@classmethod
	def getVerbose(cls):
		return cls.verbose

	@classmethod
	def setVerbose(cls,state):
		cls.verbose = state
	
	def setLoglevel(self,level):
		if level in (0,1,2,3,4,5):
			self.loglevel = level*10
		else:
			printError("Invalid log level")

	def getLoglevel(self):
		return self.loglevel 
	
def printDebug(text):
	logging.getLogger("alterx").debug(text)

def printVerbose(text):
	if logListener.getVerbose():
		logging.getLogger("alterx").debug(text)

def printInfo(text):
	logging.getLogger("alterx").info(text)

def printWarning(text):
	logging.getLogger("alterx").warning(text)

def printError(text):
	logging.getLogger("alterx").error(text)
