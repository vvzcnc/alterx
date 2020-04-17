# -*- coding: utf-8 -*-
#
# AlterX GUI - tabs widget
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

__all__ = ['TabsWidget']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

from alterx.gui.util import *
from alterx.core.linuxcnc import *

from tabs import *

class TabsWidget(QTabWidget):
	def __init__(self, parent=None):
		QTabWidget.__init__(self, parent)

		tab_names=[]
		try:
			tab_names=globals()['tabs_order']
			if not isinstance(tab_names, list):
				tab_names=[]
				raise Exception("'tabs_order' is not a list")
		except Exception as e:
			printError(_('Invalid tabs order list, {}',e))

		for tab_number, name in enumerate(tab_names):
			if "tabs.%s"%name in sys.modules.keys():
				tab = getattr(globals()[name],"module").func()
				self.addTab(tab,name)
			else:
				printError(_("No menu tab with name: tabs.{}",name))

