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

__all__ = ['MainWindow']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

from alterx.core.main import MAIN
from alterx.core.linuxcnc import *

from alterx.gui.util import *
from alterx.gui.main_screen import *
from alterx.gui.path_viewer_qt import *
from alterx.gui.mdi_history import *
from alterx.gui.gcode_editor import *
from alterx.gui.file_manager import *
from alterx.gui.offset_viewer import *
from alterx.gui.tool_viewer import *
from alterx.gui.dro_viewer import *
from alterx.gui.tabs_viewer import *
from alterx.gui.settings_viewer import *

class MainWindow(QWidget):
	TITLE = _("AlterX v{}",VERSION_STRING)

	@classmethod
	def start(cls):
		QApplication.setOrganizationName("alterx")
		QApplication.setOrganizationDomain(ALTERX_HOME_DOMAIN)
		QApplication.setApplicationName("AlterX")
		QApplication.setApplicationVersion(VERSION_STRING)

		mainwnd = cls()
		mainwnd.show()

		mainwnd.setWindowState(Qt.WindowMaximized)

		return mainwnd

	def __init__(self, parent=None):
		QWidget.__init__(self, parent)

		#Main layout
		self.mainLayout = MainLayout(self)

		MAIN.setup(self.mainLayout)

		ON_STATE = [LINUXCNC.STATE_ON]
		HOMED_STATE = ON_STATE + [(1,)*len(INFO.coordinates)+(0,)*(9-len(INFO.coordinates))]
		MDI_STATE = HOMED_STATE + [LINUXCNC.MODE_MDI]
		AUTO_STATE = HOMED_STATE + [LINUXCNC.MODE_AUTO]

		#Page 0 - Manual
		manualWidget = DROWidget()
		self.mainLayout.centralWidgets.addWidget(manualWidget)
		manualButtons = BottomWidget("manual")
		self.mainLayout.bottomWidgets.addWidget(manualButtons)
		self.mainLayout.rightLayout.addWidget(SideButton("manual",manualWidget,manualButtons,ON_STATE,[LINUXCNC.MODE_MANUAL]))
		MAIN.manual_screen = [manualWidget,manualButtons]

		#Page 1 - MDI
		mdiWidget = MDIHistory()
		self.mainLayout.centralWidgets.addWidget(mdiWidget)
		mdiButtons = BottomWidget("mdi")
		self.mainLayout.bottomWidgets.addWidget(mdiButtons)
		self.mainLayout.rightLayout.addWidget(SideButton("mdi",mdiWidget,mdiButtons,HOMED_STATE,[LINUXCNC.MODE_MDI]))
		MAIN.mdi_screen = [mdiWidget,mdiButtons]

		#Page 2 - Auto
		autoWidget = GcodeWidget()
		self.mainLayout.centralWidgets.addWidget(autoWidget)
		autoButtons = BottomWidget("auto")
		self.mainLayout.bottomWidgets.addWidget(autoButtons)
		self.mainLayout.rightLayout.addWidget(SideButton("auto",autoWidget,autoButtons,HOMED_STATE,[LINUXCNC.MODE_AUTO]))
		MAIN.auto_screen = [autoWidget,autoButtons]

		#Page 3 - Settings
		settingsWidget = SettingsWidget()
		self.mainLayout.centralWidgets.addWidget(settingsWidget)
		settingsButtons = BottomWidget("settings")
		i=self.mainLayout.bottomWidgets.addWidget(settingsButtons)
		self.mainLayout.rightLayout.addWidget(SideButton("settings",settingsWidget,settingsButtons,[],[None,i]))

		#Page 4 - Tabs
		tabsWidget = TabsWidget()
		self.mainLayout.centralWidgets.addWidget(tabsWidget)
		tabsButtons = BottomWidget("tabs")
		i=self.mainLayout.bottomWidgets.addWidget(tabsButtons)
		self.mainLayout.rightLayout.addWidget(SideButton("tabs",tabsWidget,tabsButtons,ON_STATE,[None,i]))

		#Button MACHINE
		self.mainLayout.rightLayout.addWidget(SideButton("machine",manualWidget,manualButtons,[],[None,None,LINUXCNC.STATE_ON]))

		#Page 5 - Display
		displayWidget = PathViewer()
		self.mainLayout.centralWidgets.addWidget(displayWidget)
		displayButtons = BottomWidget("display")
		i=self.mainLayout.bottomWidgets.addWidget(displayButtons)
		self.mainLayout.leftLayout.addWidget(SideButton("abort",displayWidget,displayButtons,ON_STATE,[None,i]))

		#Button EQUIPMENT
		equipmentButtons = BottomWidget("equipment")
		i=self.mainLayout.bottomWidgets.addWidget(equipmentButtons)
		self.mainLayout.leftLayout.addWidget(SideButton("equipment",None,equipmentButtons,ON_STATE,[None,i]))

		#Page 6 - Load
		loadWidget = FileManager()
		self.mainLayout.centralWidgets.addWidget(loadWidget)
		loadButtons = BottomWidget("load")
		i=self.mainLayout.bottomWidgets.addWidget(loadButtons)
		self.mainLayout.leftLayout.addWidget(SideButton("load",loadWidget,loadButtons,AUTO_STATE,[None,i]))

		#Page 7 - Edit
		editWidget = GcodeEditor()
		self.mainLayout.centralWidgets.addWidget(editWidget)
		editButtons = BottomWidget("edit")
		i=self.mainLayout.bottomWidgets.addWidget(editButtons)
		UPDATER.connect("edit_page",lambda s: MAIN.btn_edit_callback(editWidget,editButtons,[],[None,i]))

		#Button HOMING
		homingButtons = BottomWidget("homing")
		i=self.mainLayout.bottomWidgets.addWidget(homingButtons)
		self.mainLayout.leftLayout.addWidget(SideButton("homing",None,homingButtons,ON_STATE+[None,LINUXCNC.MODE_MANUAL],[None,i]))

		#Page 8 - Offset
		offsetWidget = OriginOffsetView()
		self.mainLayout.centralWidgets.addWidget(offsetWidget)
		offsetButtons = BottomWidget("offset")
		i=self.mainLayout.bottomWidgets.addWidget(offsetButtons)
		self.mainLayout.leftLayout.addWidget(SideButton("offset",offsetWidget,offsetButtons,MDI_STATE,[None,i]))

		#Page 9 - Tool
		toolWidget = ToolOffsetView()
		self.mainLayout.centralWidgets.addWidget(toolWidget)
		toolButtons = BottomWidget("tool")
		i=self.mainLayout.bottomWidgets.addWidget(toolButtons)
		self.mainLayout.leftLayout.addWidget(SideButton("tool",toolWidget,toolButtons,MDI_STATE,[None,i]))

		UPDATER.start(100)
