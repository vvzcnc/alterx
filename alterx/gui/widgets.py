# -*- coding: utf-8 -*-
#
# AlterX GUI - widgets
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

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *
from alterx.gui.util import *

class SideLayout(QVBoxLayout):
	def __init__(self, parent=None, ):
		QVBoxLayout.__init__(self, parent)
		self.setContentsMargins(0,0,0,0)
		self.setSpacing(2)

	def load(self, data):
		for i, item in enumerate(data):
			btn = QPushButton("%s"%(item))
			btn.setObjectName("btn_%s_%d"%(item.lower(),i))
			btn.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
			self.addWidget(btn)

class MainLayout(QVBoxLayout):
	def __init__(self, parent=None):
		QVBoxLayout.__init__(self, parent)

		h1 = QHBoxLayout()

		self.leftLayout = SideLayout()
		self.rightLayout = SideLayout()

		h2 = QHBoxLayout()
		h2.setContentsMargins(5,0,5,5)

		self.centralWidgets = QStackedWidget()
		h2.addWidget(self.centralWidgets,3)

		self.infoLayout = QVBoxLayout()
		h2.addLayout(self.infoLayout,2)
		
		h1.addLayout(self.leftLayout,1)
		h1.addLayout(h2,9)
		h1.addLayout(self.rightLayout,1)
		self.addLayout(h1,6)
		
		self.bottomWidgets = QStackedWidget()
		self.addWidget(self.bottomWidgets,1)