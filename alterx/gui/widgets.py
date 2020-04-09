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
from alterx.core.callback import CALLBACK as c
from alterx.core.linuxcnc import *

from menus import *

from functools import partial

class BottomButton(QPushButton):
	def __init__(self,label):
		QPushButton.__init__(self,label)
		self.setObjectName(label)
		self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

	def setup(self,menu):
		if hasattr(menu,"execute"):
			self.clicked.connect(partial(menu.execute))

		if hasattr(menu,"update"):
			timer = QTimer(self)
			timer.timeout.connect(menu.update)
			timer.start(1000)

class BottomWidget(QWidget):
	def __init__(self, layout_name):
		QWidget.__init__(self)
		layout = QHBoxLayout()
		layout.setContentsMargins(0,0,0,0)
		layout.setSpacing(2)
		self.setLayout(layout)
		
		menu_names=[]
		try:
			menu_names=getattr(globals()[layout_name],'buttons_order')
			if not isinstance(menu_names, list):
				menu_names=[]
				raise Exception("'buttons_order' is not a list")
		except Exception as e:
			printError(_('Invalid buttons order list for menu {}, {}',layout_name,e))

		last_btn = 0
		for btn_number, name in enumerate(menu_names):
			btn = BottomButton("btn_%s_%d"%(layout_name,btn_number))

			if "menus.%s.%s"%(layout_name,name) in sys.modules.keys():
				menu = getattr(globals()[layout_name],name).module.func(btn)
			elif name != None:
				menu = None
				printError(_("No menu module with name: menus.{}.{}",layout_name,name))
			else:
				return

			btn.setup(menu)
			layout.addWidget(btn)
			last_btn = btn_number+1

		for btn_number in range(last_btn,11):
			btn = BottomButton("btn_%s_%d"%(layout_name,btn_number))
			btn.setText("")
			layout.addWidget(btn)

class SideButton(QPushButton):
	def __init__(self, label, centralWidget=None, bottomWidget=None, parent=None):
		QPushButton.__init__(self, "btn_%s"%(label), parent)
		self.centralWidget = centralWidget
		self.botttomWidget = bottomWidget
		self.label = label

		self.setObjectName("btn_%s"%(label))
		icon = os.path.join(IMAGE_DIR,"mainmenu","%s.png"%label)
		if os.path.isfile(icon):
			self.setIcon(QIcon(icon))
			self.setIconSize(QSize(90,90))
			self.setText("")

		self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
		self.clicked.connect(partial(c.side_button_callback,self))

class BottomLayout(QHBoxLayout):
	def __init__(self, parent=None, ):
		QHBoxLayout.__init__(self, parent)

class DROLayout(QHBoxLayout):
	def __init__(self, num, name, parent=None):
		QHBoxLayout.__init__(self, parent)

		drolabel_name = QLabel(name)
		self.addWidget(drolabel_name,1)

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

	def update_position(self, stat):
		self.drolabel_act.setText('{:10.4f}'.format(stat['input'])) #set 'output' to see commanded position
		self.drolabel_dtg.setText('{:10.4f}'.format(stat['output']-stat['input'])) 
		self.drolabel_ferror.setText('{:10.4f}'.format(stat['ferror_current'])) 

class HSeparator(QFrame):
	def __init__(self, parent=None):
		QFrame.__init__(self, parent)
		self.setFrameShape( QFrame.HLine )
		self.setFrameShadow( QFrame.Raised )
		sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
		sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
		self.setSizePolicy(sizePolicy)
		self.setStyleSheet("font: 9pt;")
		self.setLineWidth(0)
		self.setMidLineWidth(10)

class ToolWidget(QGroupBox):
	def __init__(self, parent=None):
		QGroupBox.__init__(self, parent)
		self.setTitle(_("Tool"))
		h1 = QHBoxLayout()
		self.tool_number = QLabel("O")
		self.tool_diameter = QLabel("O")
		self.tool_offset = QLabel("O")
		h1.addWidget(self.tool_number,1)
		h1.addWidget(self.tool_diameter,2)
		h1.addWidget(self.tool_offset,3)
		self.setLayout(h1)

class GCodeWidget(QGroupBox):
	def __init__(self, parent=None):
		QGroupBox.__init__(self, parent)
		self.setTitle(_("Codes"))
		v1 = QVBoxLayout()
		h1 = QHBoxLayout()
		self.feed = QLabel("FO")
		self.spindle = QLabel("SO")
		h1.addWidget(self.feed)
		h1.addWidget(self.spindle)
		v1.addLayout(h1)
		self.g_codes = QLabel("G")
		v1.addWidget(self.g_codes)
		v1.addStretch()
		#v1.addItem(QSpacerItem(0,0,QSizePolicy.Expanding,QSizePolicy.Expanding))
		v1.addWidget(HSeparator())
		self.m_codes = QLabel("M")
		v1.addWidget(self.m_codes)
		self.setLayout(v1)

class SpindleWidget(QGroupBox):
	def __init__(self, parent=None):
		QGroupBox.__init__(self, parent)
		self.setTitle(_("Spindlerate"))
		v1 = QVBoxLayout()
		self.actual_spindlerate = QLabel("Actual: 0")
		self.spindlerate_override = QLabel("SO: 0")
		v1.addWidget(self.actual_spindlerate)
		v1.addWidget(self.spindlerate_override)
		self.setLayout(v1)

class FeedWidget(QGroupBox):
	def __init__(self, parent=None):
		QGroupBox.__init__(self, parent)
		self.setTitle(_("Feedrate"))
		v1 = QVBoxLayout()
		self.actual_feedrate = QLabel("Actual: 0")
		self.feed_override = QLabel("FO: 0")
		self.rapid_override = QLabel("RO: 0")
		v1.addWidget(self.actual_feedrate)
		v1.addWidget(self.feed_override)
		v1.addWidget(self.rapid_override)
		self.setLayout(v1)

class JOGWidget(QGroupBox):
	def __init__(self, parent=None):
		QGroupBox.__init__(self, parent)
		self.setTitle(_("JOG"))
		v1 = QVBoxLayout()
		self.jog_linear = QLabel("JOG linear: 0")
		self.linear_increment = QLabel("Increment: 0")
		self.jog_angular = QLabel("JOG angular: 0")
		self.angular_increment = QLabel("Increment: 0")
		v1.addWidget(self.jog_linear)
		v1.addWidget(self.linear_increment)
		v1.addWidget(HSeparator())
		v1.addWidget(self.jog_angular)
		v1.addWidget(self.angular_increment)
		self.setLayout(v1)

class AxisWidget(QGroupBox):
	def __init__(self, parent=None):
		QGroupBox.__init__(self, parent)
		self.setTitle(_("Axis"))
		self.coordinates = INI.find('TRAJ','COORDINATES') or []
		h1 = QHBoxLayout()
		self.drolabel = QLabel(self.coordinates)
		self.drolabel.setObjectName("lbl_dro_all")
		h1.addWidget(self.drolabel)
		self.setLayout(h1)		
		UPDATER.connect("axis", lambda axis: self.update_position(axis))

	def update_position(self, stat):
		text = ""
		for i,axis in enumerate(self.coordinates.split(' ')):
			text += '{}:{:10.4f}  '.format(axis,stat[i]['input'])
			
		self.drolabel.setText(text) 

class MainLayout(QVBoxLayout):
	def __init__(self, parent=None):
		QVBoxLayout.__init__(self, parent)

		h1 = QHBoxLayout()

		self.leftLayout = QVBoxLayout()
		self.leftLayout.setContentsMargins(0,0,0,0)
		self.leftLayout.setSpacing(2)

		self.rightLayout = QVBoxLayout()
		self.rightLayout.setContentsMargins(0,0,0,0)
		self.rightLayout.setSpacing(2)

		h2 = QHBoxLayout()
		h2.setContentsMargins(5,0,5,5)

		self.centralWidgets = QStackedWidget()
		h2.addWidget(self.centralWidgets,3)

		infoLayout = QVBoxLayout()

		axis_widget = AxisWidget()
		infoLayout.addWidget(axis_widget)

		jog_widget = JOGWidget()
		infoLayout.addWidget(jog_widget)

		feedrate_widget = FeedWidget()
		infoLayout.addWidget(feedrate_widget)

		spindle_widget = SpindleWidget()
		infoLayout.addWidget(spindle_widget)

		active_codes_widget = GCodeWidget()
		infoLayout.addWidget(active_codes_widget)

		tool_widget = ToolWidget()
		infoLayout.addWidget(tool_widget)

		infoLayout.addStretch()

		h2.addLayout(infoLayout,2)
		
		h1.addLayout(self.leftLayout,1)
		h1.addLayout(h2,9)
		h1.addLayout(self.rightLayout,1)
		self.addLayout(h1,6)
		
		self.bottomWidgets = QStackedWidget()
		self.addWidget(self.bottomWidgets,1)
