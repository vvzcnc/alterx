# -*- coding: utf-8 -*-
#
# AlterX GUI - dro widget
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

__all__ = ['DROWidget']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

from alterx.gui.util import *
from alterx.core.linuxcnc import *

class DROLayout(QHBoxLayout):
	def __init__(self, num, name, parent=None):
		QHBoxLayout.__init__(self, parent)
		self.num = num
		self.name = name

		self.drolabel_name = QLabel(name)
		self.addWidget(self.drolabel_name,1)

		v1 = QVBoxLayout()

		self.drolabel_act = QLabel(name)
		self.drolabel_act.setObjectName("lbl_dro_act_%s"%(name))
		self.drolabel_act.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		v1.addWidget(self.drolabel_act)
		
		h1 = QHBoxLayout()
		self.drolabel_dtg = QLabel(name)
		self.drolabel_dtg.setObjectName("lbl_dro_dtg_%s"%(name))
		self.drolabel_ferror = QLabel(name)
		self.drolabel_ferror.setObjectName("lbl_dro_ferror_%s"%(name))
		self.drolabel_ferror.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		h1.addWidget(self.drolabel_dtg)
		h1.addWidget(self.drolabel_ferror)
		v1.addLayout(h1)

		self.addLayout(v1,12)
		UPDATER.connect("axis", lambda axis: self.update_position(axis[num]))
		if name=='X' and INFO.machine_is_lathe:
			UPDATER.connect("diameter_multiplier",lambda m: self.diameter_mode(m,num,name))

	def diameter_mode(self,data):
		self.update_position(STAT.axis[self.num])
		self.drolabel_name.setText("{}{}".format(self.name,['','R','D'][UPDATER.diameter_multiplier]))

	def update_position(self, stat):
		if self.name == 'X' and INFO.machine_is_lathe:
			self.drolabel_act.setText(INFO.dro_format.format(stat['input']*UPDATER.diameter_multiplier))	
		else:
			self.drolabel_act.setText(INFO.dro_format.format(stat['input'])) #set 'output' to see commanded position
		self.drolabel_dtg.setText('DTG '+INFO.dro_format.format(stat['output']-stat['input'])) 
		self.drolabel_ferror.setText('FE '+INFO.dro_format.format(stat['ferror_current'])) 

class DROWidget(QWidget):
	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		dro_layout = QVBoxLayout()
		for i, axis in enumerate("xyza"):
			dro_layout.addLayout(DROLayout(i,axis))
		dro_layout.addStretch()
		self.setLayout(dro_layout)
