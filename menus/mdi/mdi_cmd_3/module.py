# -*- coding: utf-8 -*-
#
# AlterX GUI - macro command 3 widget
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
    def __init__(self, button):
        dir_path = os.path.dirname(os.path.realpath(__file__))

        UPDATER.signal("dout", self.update_status)

        if os.path.isfile("%s/icon.png" % dir_path):
            button.setIcon(QIcon("%s/icon.png" % dir_path))
            button.setIconSize(QSize(90, 90))
            button.setText("")
        else:
            button.setStyleSheet("color:black")
            button.setText("Laser\nOFF")

        self.button = button

    def update_status(self, status):
        if status[0]:
            self.button.setStyleSheet("color:green")
            self.button.setText("Laser\nON")
        else:
            self.button.setStyleSheet("color:red")
            self.button.setText("Laser\nOFF")

    def execute(self):
        printVerbose(_("Button macro command {} clicked",3))
        if not STAT.dout[0]:
            COMMAND.set_digital_output(0,1)
        else:
            COMMAND.set_digital_output(0,0)

