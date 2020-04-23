# -*- coding: utf-8 -*-
#
# AlterX GUI - version
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

from alterx.common.compat import *

from binascii import crc32


__all__ = [
    "VERSION_MAJOR",
    "VERSION_MINOR",
    "VERSION_BUGFIX",
    "VERSION_STRING",
    "VERSION_ID",
]


VERSION_MAJOR = 0
VERSION_MINOR = 1
VERSION_BUGFIX = 0
VERSION_EXTRA = "-pre"


if osIsWindows and VERSION_EXTRA:
    # pywin32 does not like non-numbers in the version string.
    # Convert the VERSION_EXTRA into a dot-number string.
    VERSION_EXTRA = ".0000%d0000" % (
        crc32(VERSION_EXTRA.encode("UTF-8")) & 0xFFFF)

# Create a string from the version information.
VERSION_STRING = "%d.%d.%d%s" % (VERSION_MAJOR, VERSION_MINOR,
                                 VERSION_BUGFIX, VERSION_EXTRA)

# Create a 31 bit ID number from the version information.
VERSION_ID = crc32(VERSION_STRING.encode("UTF-8")) & 0x7FFFFFFF
