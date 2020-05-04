# -*- coding: utf-8 -*-
#
# AlterX GUI - settings widget
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

__all__ = ['SettingsWidget']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

from alterx.gui.util import *
from alterx.core.linuxcnc import *

from alterx.gui.config_editor import *

class SettingsWidget(QStackedWidget):
    def __init__(self, parent=None):
        QStackedWidget.__init__(self, parent)
        self.addWidget(ConfigEditor())
        
        UPDATER.add("settings_page_next")
        UPDATER.add("settings_page_prev")
        
        UPDATER.connect("settings_page_next",self.next_page)
        UPDATER.connect("settings_page_prev",self.prev_page)
        
    def next_page(self,state=None):
        if self.currentIndex() < 0 :
            self.setCurrentIndex(0)
        elif self.currentIndex() == self.count()-1:
            self.setCurrentIndex(0)
        else:
            self.setCurrentIndex(self.currentIndex()+1)

    def prev_page(self,state=None):
        if self.currentIndex() < 0 :
            self.setCurrentIndex(0)
        elif self.currentIndex() < 1:
            self.setCurrentIndex(self.count()-1)
        else:
            self.setCurrentIndex(self.currentIndex()-1)
