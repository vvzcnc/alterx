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
from alterx.gui.path_viewer import *
from alterx.gui.mdi_history import *
from alterx.gui.gcode_editor import *
from alterx.gui.file_manager import *
from alterx.gui.offset_viewer import *
from alterx.gui.tool_viewer import *
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

class SettingsWidget(QWidget):
	def __init__(self, parent=None):
		QWidget.__init__(self, parent)

class TabsWidget(QWidget):
	def __init__(self, parent=None):
		QWidget.__init__(self, parent)

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
		manualButtons = BottomWidget("manual")
		self.mainLayout.bottomWidgets.addWidget(manualButtons)
		self.mainLayout.rightLayout.addWidget(SideButton("manual",manualWidget,manualButtons))

		#Page 1 - MDI
		mdiWidget = MDIHistory()
		self.mainLayout.centralWidgets.addWidget(mdiWidget)
		mdiButtons = BottomWidget("mdi")
		self.mainLayout.bottomWidgets.addWidget(mdiButtons)
		self.mainLayout.rightLayout.addWidget(SideButton("mdi",mdiWidget,mdiButtons))

		#Page 2 - Auto
		autoWidget = GcodeWidget()
		self.mainLayout.centralWidgets.addWidget(autoWidget)
		autoButtons = BottomWidget("auto")
		self.mainLayout.bottomWidgets.addWidget(autoButtons)
		self.mainLayout.rightLayout.addWidget(SideButton("auto",autoWidget,autoButtons))

		#Page 3 - Settings
		settingsWidget = SettingsWidget()
		self.mainLayout.centralWidgets.addWidget(settingsWidget)
		settingsButtons = BottomWidget("settings")
		self.mainLayout.bottomWidgets.addWidget(settingsButtons)
		self.mainLayout.rightLayout.addWidget(SideButton("settings",settingsWidget,settingsButtons))

		#Page 4 - Tabs
		tabsWidget = TabsWidget()
		self.mainLayout.centralWidgets.addWidget(tabsWidget)
		tabsButtons = BottomWidget("tabs")
		self.mainLayout.bottomWidgets.addWidget(tabsButtons)
		self.mainLayout.rightLayout.addWidget(SideButton("tabs",tabsWidget,tabsButtons))

		#Button MACHINE
		self.mainLayout.rightLayout.addWidget(SideButton("machine",manualWidget,manualButtons))

		#Page 5 - Display
		displayWidget = PathViewer()
		self.mainLayout.centralWidgets.addWidget(displayWidget)
		displayButtons = BottomWidget("display")
		self.mainLayout.bottomWidgets.addWidget(displayButtons)
		self.mainLayout.leftLayout.addWidget(SideButton("abort",displayWidget,displayButtons))

		#Button EQUIPMENT
		equipmentButtons = BottomWidget("equipment")
		self.mainLayout.bottomWidgets.addWidget(equipmentButtons)
		self.mainLayout.leftLayout.addWidget(SideButton("equipment",None,equipmentButtons))

		#Page 6 - Load
		loadWidget = FileManager()
		self.mainLayout.centralWidgets.addWidget(loadWidget)
		loadButtons = BottomWidget("load")
		self.mainLayout.bottomWidgets.addWidget(loadButtons)
		self.mainLayout.leftLayout.addWidget(SideButton("load",loadWidget,loadButtons))

		#Page 7 - Edit
		editWidget = GcodeEditor()
		self.mainLayout.centralWidgets.addWidget(editWidget)
		editButtons = BottomWidget("edit")
		self.mainLayout.bottomWidgets.addWidget(editButtons)

		#Button HOMING
		homingButtons = BottomWidget("homing")
		self.mainLayout.bottomWidgets.addWidget(homingButtons)
		self.mainLayout.leftLayout.addWidget(SideButton("homing",None,homingButtons))

		#Page 8 - Offset
		offsetWidget = OriginOffsetView()
		self.mainLayout.centralWidgets.addWidget(offsetWidget)
		offsetButtons = BottomWidget("offset")
		self.mainLayout.bottomWidgets.addWidget(offsetButtons)
		self.mainLayout.leftLayout.addWidget(SideButton("offset",offsetWidget,offsetButtons))

		#Page 9 - Tool
		toolWidget = ToolOffsetView()
		self.mainLayout.centralWidgets.addWidget(toolWidget)
		toolButtons = BottomWidget("tool")
		self.mainLayout.bottomWidgets.addWidget(toolButtons)
		self.mainLayout.leftLayout.addWidget(SideButton("tool",toolWidget,toolButtons))
       	