from __future__ import division, absolute_import, print_function, unicode_literals

__all__ = ['BaseBackPlot']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *
from alterx.core.linuxcnc import *

import gcode
import shutil
import os

from . import base_canon

class BaseBackPlot(object):
    def __init__(self, inifile=None, canon=base_canon.BaseCanon):
        inifile = inifile or os.getenv("INI_FILE_NAME")
        if inifile is None or not os.path.isfile(inifile):
            raise ValueError("Invalid INI file: %s", inifile)

        self.canon_class = canon
        self.canon = None

        self.stat = STAT
        self.config_dir = os.path.dirname(inifile)

        temp = INI.find("EMCIO", "RANDOM_TOOLCHANGER")
        self.random = int(temp or 0)

        temp = INI.find("DISPLAY", "GEOMETRY") or 'XYZ'
        self.geometry = temp.upper()

        temp = INI.find("DISPLAY", "LATHE") or "false"
        self.lathe_option = temp.lower() in ["1", "true", "yes"]

        temp = INI.find("RS274NGC", "PARAMETER_FILE") or "linuxcnc.var"
        self.parameter_file = os.path.join(self.config_dir, temp)
        self.temp_parameter_file = os.path.join(self.parameter_file + '.bak')

        self.last_filename = None

    def load(self, filename=None, *args, **kwargs):
        # args and kwargs are passed to the canon init method

        filename = filename or self.last_filename
        if filename is None:
            filename = STAT.file

        if filename is None or not os.path.isfile(filename):
            self.canon = None
            printDebug(_("3D plot", "Can't load backplot, invalid file: {}",filename))
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

        result, seq = gcode.parse(filename, self.canon, unitcode, initcode)

        if result > gcode.MIN_ERROR:
            msg = gcode.strerror(result)
            fname = os.path.basename(filename)
            printDebug(_("3D plot", "Error in {} line {}\n{}",fname, seq - 1, msg))
            # raise SyntaxError("Error in %s line %i: %s" % (fname, seq - 1, msg))

        # clean up temp var file and the backup
        os.unlink(self.temp_parameter_file)
        os.unlink(self.temp_parameter_file + '.bak')
