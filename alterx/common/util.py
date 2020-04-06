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

from alterx.common.compat import *
import time
import contextlib

__all__ = [
	"sys",
	"Logging",
	"printDebug",
	"printVerbose",
	"printInfo",
	"printWarning",
	"printError",
]


class Logging(object):
	LOG_NONE	= 0
	LOG_ERROR	= 1
	LOG_WARNING	= 2
	LOG_INFO	= 3
	LOG_VERBOSE	= 4
	LOG_DEBUG	= 5


	loglevel = LOG_INFO
	prefix = ""

	_getNow = getattr(time, "monotonic", time.time)
	_startupTime = _getNow()

	@classmethod
	def _getUptime(cls):
		return cls._getNow() - cls._startupTime

	@classmethod
	def setLoglevel(cls, loglevel):
		if loglevel not in (cls.LOG_NONE,
				    cls.LOG_ERROR,
				    cls.LOG_WARNING,
				    cls.LOG_INFO,
				    cls.LOG_VERBOSE,
				    cls.LOG_DEBUG):
			raise AlterXError("Invalid log level '%d'" % loglevel)
		cls.loglevel = loglevel

	@classmethod
	def getLogLevel(cls):
		return cls.loglevel

	@classmethod
	def setPrefix(cls, prefix):
		cls.prefix = prefix

	@classmethod
	def __print(cls, stream, text):
		with contextlib.suppress(RuntimeError):
			if stream:
				if cls.prefix:
					stream.write(cls.prefix)
				stream.write("[%.3f] " % cls._getUptime())
				stream.write(text)
				stream.write("\n")


	@classmethod
	def printDebug(cls, text):
		if cls.loglevel >= cls.LOG_DEBUG:
			cls.__print(sys.stdout, text)

	@classmethod
	def printVerbose(cls, text):
		if cls.loglevel >= cls.LOG_VERBOSE:
			cls.__print(sys.stdout, text)

	@classmethod
	def printInfo(cls, text):
		if cls.loglevel >= cls.LOG_INFO:
			cls.__print(sys.stdout, text)

	@classmethod
	def printWarning(cls, text):
		if cls.loglevel >= cls.LOG_WARNING:
			cls.__print(sys.stderr, text)

	@classmethod
	def printError(cls, text):
		if cls.loglevel >= cls.LOG_ERROR:
			cls.__print(sys.stderr, text)

def printDebug(text):
	Logging.printDebug(text)

def printVerbose(text):
	Logging.printVerbose(text)

def printInfo(text):
	Logging.printInfo(text)

def printWarning(text):
	Logging.printWarning(text)

def printError(text):
	Logging.printError(text)