# -*- coding: utf-8 -*-
#
# AlterX GUI - environment variables
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
from alterx.common.util import *

__all__ = [
    "AlterxEnv",
]


class AlterxEnv(object):
    """Central environment variable handler.
    """

    @classmethod
    def getEnv(cls):
        """Get a copy of the environment dict.
        """
        return dict(os.environ)

    @classmethod
    def clearLang(cls, env, lang="C"):
        """Reset the language settings of an environment dict
        to some expected value and return the result.
        """
        env = dict(env)
        env["LANG"] = lang
        for i in {"LANGUAGE", "LC_CTYPE", "LC_NUMERIC",
                  "LC_TIME", "LC_COLLATE", "LC_MONETARY",
                  "LC_MESSAGES", "LC_PAPER", "LC_NAME",
                  "LC_ADDRESS", "LC_TELEPHONE", "LC_MEASUREMENT",
                  "LC_IDENTIFICATION", }:
            env.pop(i, None)
        return env

    @classmethod
    def __getVar(cls, name, default=None):
        return cls.getEnv().get("ALTERX_" + name, default)

    @classmethod
    def getGuiFramework(cls):
        """Get ALTERX_GUI.
        """
        return cls.__getVar("GUI", "auto").lower()
