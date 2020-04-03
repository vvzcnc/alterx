# -*- coding: utf-8 -*-
#
# AlterX GUI - callbacks
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

__all__ = ['CALLBACK']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

class Callback():

	def setup(self, parent):
		self.parent = parent

	def bottom_button_callback(self, item):
		print("bottom")

	def side_button_callback(self, item):
		if self.parent:
			if item == "abort":
				self.parent.btn_abort_callback()
			elif item == "equipment":
				self.parent.btn_equipment_callback()
			elif item == "load":
				self.parent.btn_load_callback()
			elif item == "homing":
				self.parent.btn_homing_callback()
			elif item == "offset":
				self.parent.btn_offset_callback()
			elif item == "tools":
				self.parent.btn_tools_callback()
			elif item == "manual":
				self.parent.btn_manual_callback()
			elif item == "mdi":
				self.parent.btn_mdi_callback()
			elif item == "auto":
				self.parent.btn_auto_callback()
			elif item == "settings":
				self.parent.btn_settings_callback()
			elif item == "tabs":
				self.parent.btn_tabs_callback()
			elif item == "machine":
				self.parent.btn_machine_callback()
			else:
				printError(_("Unknown button"))
		else:
			printError(_("No parent"))

CALLBACK = Callback()
