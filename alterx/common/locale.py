# -*- coding: utf-8 -*-
#
# AlterX GUI - localization support
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

__all__ = ['_']

from alterx.common.compat import *
from alterx.common.util import *
import locale
import gettext
import pkg_resources


class translate():
    def __init__(self):
        self._locale, _encoding = locale.getdefaultlocale()
        self._ = lambda s: s

    def __call__(self, source, *args):
        if len(args) > 0:
            args_decoded = []
            for a in args:
                if type(a) not in (int,float) and a:
                    a = toUnicode(a)
                args_decoded.append(a)

            try:
                t = self._(source).format(*args_decoded)
            except Exception as e:
                printVerbose(
                    "Bad translation for ({}), error ({})".format(source, e))
                t = source.format(*args_decoded)
        else:
            t = self._(source)
        return t

    def get_text(self, s):
        text = self.lang.lgettext(s)
        if hasattr(text, "decode"):
            return text.decode('utf-8')
        else:
            printVerbose("No translation for ({})".format(s))
            return s

    def setup(self, val):
        locale_dir = pkg_resources.resource_filename("alterx", "locales")

        if not val:
            printVerbose("Using default locale: {}".format(self._locale))
            val = self._locale

        try:
            self.lang = gettext.translation("base", locale_dir, [val])
            self.lang.install()
            self._ = self.get_text
            printVerbose("Setup locale: {}".format(val))
        except Exception as e:
            printWarning("Unsupported locale ({}) or translation error ({})\
            ".format(val, e))
            self._ = lambda s: s

_ = translate()
