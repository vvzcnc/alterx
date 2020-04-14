# -*- coding: utf-8 -*-
#
# AlterX GUI - flood widget
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
from alterx.core.linuxcnc import *

class func:
    def __init__(self,button):
        self.button = button
        self.update()

    def update_image(self,state):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if state:
            if os.path.isfile("%s/icon_on.png"%dir_path):
		self.button.setIcon(QIcon("%s/icon_on.png"%dir_path))
		self.button.setIconSize(QSize(90,90))
		self.button.setText("")
            else:
                self.button.setStyleSheet("color:black")
        else:
            if os.path.isfile("%s/icon.png"%dir_path):
		self.button.setIcon(QIcon("%s/icon.png"%dir_path))
		self.button.setIconSize(QSize(90,90))
		self.button.setText("")
            else:
                self.button.setStyleSheet("color:black")

    def execute(self):
        if STAT.flood:
            printInfo( _("Button flood clicked, flood disactivated" ))
            COMMAND.flood( LINUXCNC.FLOOD_OFF )
        else:
            printInfo( _("Button flood clicked, flood activated" ))
            COMMAND.flood( LINUXCNC.FLOOD_ON )

    def update(self):
        self.update_image(STAT.flood)
