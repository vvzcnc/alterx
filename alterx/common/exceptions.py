# -*- coding: utf-8 -*-
#
# AlterX GUI - exceptions
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

__all__ = [
	"ExitCodes",
	"suppressAllExc",
]

class ExitCodes(object):
	# Success.
	EXIT_OK			= 0
	# Command line option error.
	EXIT_ERR_CMDLINE	= 10
	# Python interpreter error.
	EXIT_ERR_INTERP		= 20
	# Other error.
	EXIT_ERR_OTHER		= 100

class __suppressAllExc(object):
	"""Context manager to suppress almost all exceptions.
	Only really fatal coding exceptions will be re-raised.
	The usage is similar to that of contextlib.suppress().
	"""

	import re as _re

	def __enter__(self):
		pass

	def __exit__(self, exctype, excinst, exctb): 
		if exctype is None:
			return False # no exception
		if issubclass(exctype, (SyntaxError, NameError, AttributeError)):
			return False # raise fatal exception
		if issubclass(exctype, ValueError):
			re, text = self._re, str(excinst)
			if re.match(r'.*takes exactly \d+ argument \(\d+ given\).*', text) or\
			   re.match(r'.*missing \d+ required positional argument.*', text) or\
			   re.match(r'.*takes \d+ positional argument but \d+ were given.*', text):
				return False # raise fatal exception
		return True # suppress exception

suppressAllExc = __suppressAllExc()
