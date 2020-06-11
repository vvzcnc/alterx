# -*- coding: utf-8 -*-
#
# AlterX GUI - python compatibility
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

import contextlib
import os
import sys

__all__ = [
    "sys",
    "os",
    "contextlib",
    "osIsWindows",
    "osIsPosix",
    "osIsLinux",
    "ConfigParser",
    "toUnicode",
]

# Convenient operating system identifiers
if os.name == "java":
    import java.lang.System
    __osName = java.lang.System.getProperty("os.name").lower()
    osIsWindows = __osName.startswith("windows")
    osIsPosix = not osIsWindows
else:
    osIsWindows = os.name == "nt" or os.name == "ce"
    osIsPosix = os.name == "posix"
osIsLinux = osIsPosix and "linux" in sys.platform.lower()

# contextlib.suppress compatibility
if not hasattr(contextlib, "suppress"):
    class _suppress(object):
        def __init__(self, *excs):
            self._excs = excs

        def __enter__(self):
            pass

        def __exit__(self, exctype, excinst, exctb):
            return exctype is not None and issubclass(exctype, self._excs)
    contextlib.suppress = _suppress

# contextlib.nullcontext compatibility
if not hasattr(contextlib, "nullcontext"):
    class _nullcontext(object):
        def __init__(self, enter_result=None):
            self.enter_result = enter_result

        def __enter__(self):
            return self.enter_result

        def __exit__(self, *unused):
            pass
    contextlib.nullcontext = _nullcontext

# isPy3Compat is True, if the interpreter is Python 3 compatible.
isPy3Compat = sys.version_info[0] == 3

# isPy2Compat is True, if the interpreter is Python 2 compatible.
isPy2Compat = sys.version_info[0] == 2

# Python 2/3 helper selection
def py23(py2, py3):
    if isPy3Compat:
        return py3
    if isPy2Compat:
        return py2
    raise Exception("Failed to detect Python version")

if isPy2Compat:
    import ConfigParser
else:
    import configparser as ConfigParser


def toUnicode(string):
    try:
        string = unicode(string, encoding='utf-8')
    except NameError:
        string = str(string)
    except TypeError:
        pass
    except Exception as e:
        #print(e)
        pass
    return string    
