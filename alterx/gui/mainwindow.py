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

class BottomLayout(QHBoxLayout):
	def __init__(self, parent=None, ):
		QHBoxLayout.__init__(self, parent)

class DROLayout(QHBoxLayout):
	def __init__(self, num, name, parent=None):
		QHBoxLayout.__init__(self, parent)

		drolabel_name = QLabel(name)
		self.addWidget(drolabel_name,1)

		v1 = QVBoxLayout()

		drolabel_act = QLabel(name)
		drolabel_act.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		v1.addWidget(drolabel_act)
		
		h1 = QHBoxLayout()
		drolabel_dtg = QLabel(name)
		drolabel_sec = QLabel(name)
		drolabel_sec.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		h1.addWidget(drolabel_dtg)
		h1.addWidget(drolabel_sec)
		v1.addLayout(h1)

		self.addLayout(v1,12)

class ToolWidget(QGroupBox):
	def __init__(self, parent=None):
		QGroupBox.__init__(self, parent)

class GCodeWidget(QGroupBox):
	def __init__(self, parent=None):
		QGroupBox.__init__(self, parent)

class SpindleWidget(QGroupBox):
	def __init__(self, parent=None):
		QGroupBox.__init__(self, parent)

class FeedWidget(QGroupBox):
	def __init__(self, parent=None):
		QGroupBox.__init__(self, parent)

class JOGWidget(QGroupBox):
	def __init__(self, parent=None):
		QGroupBox.__init__(self, parent)

class AxisWidget(QGroupBox):
	def __init__(self, parent=None):
		QGroupBox.__init__(self, parent)


class MainWindow(QWidget):
	TITLE = _("Awlsim PLC v{}",VERSION_STRING)

	@classmethod
	def start(cls):
		# Set basic qapp-details.
		# This is important for QSettings.
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

		self.mainLayout = MainLayout(self)

		dro_layout = QVBoxLayout()
		for i, axis in enumerate("xyza"):
			dro_layout.addLayout(DROLayout(i,axis))
		dro_layout.addStretch()

		droWidget = QWidget()
		droWidget.setLayout(dro_layout)
		self.mainLayout.centralWidgets.addWidget(droWidget)

		tool_widget = ToolWidget()
		active_codes_widget = GCodeWidget()
		spindle_widget = SpindleWidget()
		feedrate_widget = FeedWidget()
		jog_widget = JOGWidget()
		axis_widget = AxisWidget()

		self.mainLayout.infoLayout.addWidget(axis_widget)
		self.mainLayout.infoLayout.addWidget(jog_widget)
		self.mainLayout.infoLayout.addWidget(feedrate_widget)
		self.mainLayout.infoLayout.addWidget(spindle_widget)
		self.mainLayout.infoLayout.addWidget(active_codes_widget)
		self.mainLayout.infoLayout.addWidget(tool_widget)
		self.mainLayout.infoLayout.addStretch()

		self.mainLayout.leftLayout.load(("Abort","Equipment","Load","Homing","Offset","Tools"))
		self.mainLayout.rightLayout.load(("Manual","MDI","Auto","Settings","Tabs","Machine"))
        	
		bbtn = QWidget()
		bbtnlay = QHBoxLayout()
		bbtnlay.setContentsMargins(0,0,0,0)
		bbtnlay.setSpacing(2)
		bbtn.setLayout(bbtnlay)
		self.mainLayout.bottomWidgets.addWidget(bbtn)
		for i in range(11):
			btn = QPushButton("test %d"%i)
			btn.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
			bbtn.layout().addWidget(btn)
