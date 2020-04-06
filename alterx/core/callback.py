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

	def side_button_callback(self, button):
		if self.parent:
			if button.label == "abort":
				self.parent.btn_abort_callback(button)
			elif button.label == "equipment":
				self.parent.btn_equipment_callback(button)
			elif button.label == "load":
				self.parent.btn_load_callback(button)
			elif button.label == "homing":
				self.parent.btn_homing_callback(button)
			elif button.label == "offset":
				self.parent.btn_offset_callback(button)
			elif button.label == "tool":
				self.parent.btn_tools_callback(button)
			elif button.label == "manual":
				self.parent.btn_manual_callback(button)
			elif button.label == "mdi":
				self.parent.btn_mdi_callback(button)
			elif button.label == "auto":
				self.parent.btn_auto_callback(button)
			elif button.label == "settings":
				self.parent.btn_settings_callback(button)
			elif button.label == "tabs":
				self.parent.btn_tabs_callback(button)
			elif button.label == "machine":
				self.parent.btn_machine_callback(button)
			else:
				printError(_("Unknown button"))
		else:
			printError(_("No parent"))

CALLBACK = Callback()
