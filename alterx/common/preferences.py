# -*- coding: utf-8 -*-
#
# AlterX GUI - preferences
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

__all__ = ['PREF']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

from alterx.core.linuxcnc import INI


class Preferences(ConfigParser):
    def __init__(self, path=None):
        ConfigParser.__init__(self)
        self.types = {
            bool: self.getboolean,
            float: self.getfloat,
            int: self.getint,
            str: self.get,
            repr: lambda section, option: eval(self.get(section, option)),
        }

        if not path:
            path = "preferences.var"

        self.fn = os.path.expanduser(path)
        if not os.path.exists(self.fn):
            self.create_config()

        self.read(self.fn)

    def create_config(self):
        self.addSetion("DEFAULT")
        with open(self.fn, "w") as config_file:
            self.write(config_file)

    def getpref(self, option, default=False, type=bool):
        m = self.types.get(type)
        try:
            o = m("DEFAULT", option)
        except Exception, detail:
            printError(_("Get preference error: {} ", detail))

            self.putpref(option, default)

            if type in(bool, float, int):
                o = type(default)
            else:
                o = default
        return o

    def putpref(self, option, value):
        self.set("DEFAULT", option, str(value))
        with open(self.fn, "w") as config_file:
            self.write(config_file)


PREF = Preferences(INI.find("DISPLAY", "PREFERENCE_FILE_PATH"))
