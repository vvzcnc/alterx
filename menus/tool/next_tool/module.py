# -*- coding: utf-8 -*-
#
# AlterX GUI - tool viewer next
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
    def __init__(self, button):
        dir_path = os.path.dirname(os.path.realpath(__file__))

        if os.path.isfile("%s/icon.png" % dir_path):
            button.setIcon(QIcon("%s/icon.png" % dir_path))
            button.setIconSize(QSize(90, 90))
            button.setText("")
        else:
            button.setStyleSheet("color:black")

    def execute(self):
        printVerbose(_("Tool viewer next button clicked"))
        UPDATER.emit("toolviewer_next")
