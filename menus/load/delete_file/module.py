#!/usr/bin/env python
# -*- coding:UTF-8 -*-# -*- coding: utf-8 -*-
#
# AlterX GUI - filemanager delete
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
from alterx.core.linuxcnc import UPDATER

class func:
	def __init__(self,button):
		self.button = button
		self.delete_confirm = False
		self.update_image()

	def update_image(self):
		dir_path = os.path.dirname(os.path.realpath(__file__))
		if os.path.isfile("%s/icon.png"%dir_path):
			self.button.setIcon(QIcon("%s/icon.png"%dir_path))
			self.button.setIconSize(QSize(90,90))
			self.button.setText("")
		else:
			self.button.setStyleSheet("color:black")

	def update(self):
		if not self.button.hasFocus() and self.delete_confirm:
			self.delete_confirm = False
			self.update_image()

	def execute(self):
		printVerbose( _("Button filemanager delete clicked") )

		if self.delete_confirm:
			self.delete_confirm = False
			self.update_image()
			UPDATER.emit("fileman_delete")
		else:
			self.button.setFocus()
			self.button.setIcon(QIcon())
			self.button.setText(_("Are you sure?\nClick to delete."))
			self.delete_confirm = True