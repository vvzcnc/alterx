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

__all__ = ['PREF','Config']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

import base64
import io
import codecs

class Config(ConfigParser.ConfigParser):
    def __init__(self,inifile):
        ConfigParser.ConfigParser.__init__(self)
        try:
            self.read(inifile)
        except Exception as e:
            printError(_("Read ini-file error: {} ", e))

    def find(self,*args):
        try:
            return self.get(*args)
        except:
            return

class Preferences(ConfigParser.ConfigParser):
    def __init__(self):
        ConfigParser.ConfigParser.__init__(self)
        self.types = {
            bool: self.getboolean,
            float: self.getfloat,
            int: self.getint,
            str: self.get,
            repr: lambda section, option: eval(self.get(section, option)),
        }

        inifile = None
        try:
            inifile = os.environ['INI_FILE_NAME']
        except:
            pass

        self.ini = Config(inifile)
        path = self.ini.find("DISPLAY", "PREFERENCE_FILE_PATH") or 'preferences.var'

        self.fn = os.path.expanduser(path)
        if os.path.exists(self.fn):
            decoded_file = io.BytesIO()
            with open(self.fn,'r') as encoded_file:
                for line in encoded_file:
                    decoded_file.write(base64.b64decode(line))
            decoded_file.seek(0)
            self.readfp(decoded_file)
        else:
            printDebug(_("Preferences file is not exist."))

    def getpref(self, option, default=False, type=bool):
        m = self.types.get(type)
        try:
            o = m("DEFAULT", option)
        except Exception as e:
            printDebug(_("Failed to get preference: {} ", e))

            #self.putpref(option, default)

            if type in(bool, float, int):
                o = type(default)
            else:
                o = default
        return o

    def putpref(self, option, value):
        self.set("DEFAULT", option, str(value))
        with codecs.open(self.fn, "w", "base64") as config_file:
            self.write(config_file)

PREF = Preferences()
