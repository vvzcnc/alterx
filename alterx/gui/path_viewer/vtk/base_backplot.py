# -*- coding: utf-8 -*-
#
# AlterX GUI - base backplot
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

__all__ = ['BaseBackPlot']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *
from alterx.core.linuxcnc import *

from alterx.core.linuxcnc import GCODE 
import shutil
import os

from . import base_canon

class BaseBackPlot(object):
    def __init__(self, canon=base_canon.BaseCanon):
        self.canon_class = canon
        self.canon = None
        self.stat = STAT
        self.random = int(INI.find("EMCIO", "RANDOM_TOOLCHANGER") or 0)
        self.geometry = (INI.find("DISPLAY", "GEOMETRY") or 'XYZ').upper()
        self.lathe_option = INFO.machine_is_lathe
        self.parameter_file = INFO.parameter_file
        self.temp_parameter_file = os.path.join(self.parameter_file + '.bak')
        self.last_filename = None

    def load(self, filename=None, *args, **kwargs):
        # args and kwargs are passed to the canon init method

        filename = filename or self.last_filename
        if filename is None:
            filename = STAT.file

        if filename is None or not os.path.isfile(filename):
            self.canon = None
            printDebug(_("3D plot, Can't load backplot, invalid file: {}",filename))
            # raise ValueError("Can't load backplot, invalid file: {}".format(filename))

        self.last_filename = filename

        # create the object which handles the canonical motion callbacks
        # (straight_feed, straight_traverse, arc_feed, rigid_tap, etc.)
        self.canon = self.canon_class(*args, **kwargs)

        if os.path.exists(self.parameter_file):
            shutil.copy(self.parameter_file, self.temp_parameter_file)

        self.canon.parameter_file = self.temp_parameter_file

        # Some initialization g-code to set the units and optional user code
        unitcode = "G%d" % (20 + (STAT.linear_units == 1))
        initcode = INI.find("RS274NGC", "RS274NGC_STARTUP_CODE") or ""

        # THIS IS WHERE IT ALL HAPPENS: load_preview will execute the code,
        # call back to the canon with motion commands, and record a history
        # of all the movements.

        result, seq = GCODE.parse(filename, self.canon, unitcode, initcode)

        if result > GCODE.MIN_ERROR:
            msg = GCODE.strerror(result)
            fname = os.path.basename(filename)
            printDebug(_("3D plot, Error in {} line {}\n{}",fname, seq - 1, msg))
            # raise SyntaxError("Error in %s line %i: %s" % (fname, seq - 1, msg))

        # clean up temp var file and the backup
        os.unlink(self.temp_parameter_file)
        os.unlink(self.temp_parameter_file + '.bak')
