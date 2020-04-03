# -*- coding: utf-8 -*-
#
# AlterX GUI - mainwindow
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
from alterx.gui.widgets import *
from alterx.core.callback import CALLBACK
from alterx.core.main import MAIN

class ManualWidget(QWidget):
	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		dro_layout = QVBoxLayout()
		for i, axis in enumerate("xyza"):
			dro_layout.addLayout(DROLayout(i,axis))
		dro_layout.addStretch()
		self.setLayout(dro_layout)

class MDIWidget(QWidget):
	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		v1 = QVBoxLayout()
		mdiList = QListWidget()
		v1.addWidget(mdiList)
		g1 = QGroupBox()
		g1.setTitle(_("Program"))
		v2 = QVBoxLayout()
		filename = QLabel("Filename: ")
		v2.addWidget(filename)
		h1 = QHBoxLayout()
		lines = QLabel("Lines: ")
		progress = QLabel("Progress: ")
		h1.addWidget(lines)
		h1.addWidget(progress)
		v2.addLayout(h1)
		g1.setLayout(v2)
		v1.addWidget(g1)
		self.setLayout(v1)

class MainWindow(QWidget):
	TITLE = _("Alterx v{}",VERSION_STRING)

	@classmethod
	def start(cls):
		QApplication.setOrganizationName("alterx")
		QApplication.setOrganizationDomain(ALTERX_HOME_DOMAIN)
		QApplication.setApplicationName("alterx-gui")
		QApplication.setApplicationVersion(VERSION_STRING)

		mainwnd = cls()
		mainwnd.show()

		mainwnd.setWindowState(Qt.WindowMaximized)

		return mainwnd

	def __init__(self, parent=None):
		QWidget.__init__(self, parent)

		#Main layout
		self.mainLayout = MainLayout(self)

		CALLBACK.setup(MAIN)
		MAIN.setup(self.mainLayout)

		#Page 0 - Manual
		manualWidget = ManualWidget()
		self.mainLayout.centralWidgets.addWidget(manualWidget)
		manualButtons = BottomWidget(0,"manual",['exit','space'])
		self.mainLayout.bottomWidgets.addWidget(manualButtons)

		#Page 1 - MDI
		mdiWidget = MDIWidget()
		self.mainLayout.centralWidgets.addWidget(mdiWidget)

		#Page 2 - Auto
		#self.mainLayout.centralWidgets.addWidget(autoWidget)

		#Page 3 - Settings
		#self.mainLayout.centralWidgets.addWidget(settingsWidget)

		#Page 4 - Tabs
		#self.mainLayout.centralWidgets.addWidget(tabsWidget)

		#Page 5 - Display
		#self.mainLayout.centralWidgets.addWidget(displayWidget)

		#Page 6 - Load
		#self.mainLayout.centralWidgets.addWidget(loadWidget)

		#Page 7 - Edit
		#self.mainLayout.centralWidgets.addWidget(editWidget)

		#Page 8 - Offset
		#self.mainLayout.centralWidgets.addWidget(offsetWidget)

		#Page 9 - Tool
		#self.mainLayout.centralWidgets.addWidget(toolWidget)
       	