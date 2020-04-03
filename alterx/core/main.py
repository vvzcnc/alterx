# -*- coding: utf-8 -*-
#
# AlterX GUI - core main
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

__all__ = ['MAIN']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *
from alterx.core.linuxcnc import *

class Main():
#------ Initialize ------#
	def setup(self, parent):
		self.p = parent
		UPDATER.connect("task_state", self.task_state_handler)

#------ Global handlers ------#
	def task_state_handler(self,data):
		printVerbose(_("LinuxCNC state {}",data))
	
#------ Button callbacks ------#
	def btn_abort_callback(self):
		print("abort")

	def btn_equipment_callback(self):
		print("abort")

	def btn_load_callback(self):
		print("abort")

	def btn_homing_callback(self):
		print("abort")

	def btn_offset_callback(self):
		print("abort")

	def btn_tools_callback(self):
		print("abort")

	def btn_manual_callback(self):
		self.p.centralWidgets.setCurrentIndex(0)

	def btn_mdi_callback(self):
		self.p.centralWidgets.setCurrentIndex(1)

	def btn_auto_callback(self):
		self.p.centralWidgets.setCurrentIndex(2)

	def btn_settings_callback(self):
		print("abort")

	def btn_tabs_callback(self):
		print("abort")

	def btn_machine_callback(self):
		COMMAND.state(LINUXCNC.STATE_ESTOP_RESET)
		COMMAND.state(LINUXCNC.STATE_ON)

MAIN = Main()
