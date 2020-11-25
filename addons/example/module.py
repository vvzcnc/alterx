# -*- coding: utf-8 -*-
#
# AlterX GUI - example addon
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

from alterx.core.linuxcnc import *

class func:
    def __init__(self):
        UPDATER.signal("task_state", self.task_state_handler)

    def task_state_handler(self, data):
        if data == LINUXCNC.STATE_ESTOP_RESET or data == LINUXCNC.STATE_OFF:
            printVerbose(_("Addon digital output set false"))
            COMMAND.set_digital_output(0,0)

