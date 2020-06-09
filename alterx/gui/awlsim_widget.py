# -*- coding: utf-8 -*-
#
# AlterX GUI - awlsim widget
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

__all__ = ["AwlsimWidget"]

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common.preferences import *
from alterx.common import *
from alterx.gui.util import *

class AwlsimWidget(QWidget):
    def __init__(self, parent=None, path=None):
        QWidget.__init__(self, parent)
        
        try:
            #GUI freeze        
            #from awlsim.gui.mainwindow import MainWindow
            #mainwnd = MainWindow.start()
            vlay = QVBoxLayout()
            vlay.addWidget(QLabel("Awlsim"))

            hlay = QHBoxLayout()
            start = QPushButton()
            start.setText(_("Start Awlsim"))
            start.clicked.connect(self.start_app)
            hlay.addWidget(start)
            hlay.addStretch()
            
            vlay.addLayout(hlay)
            vlay.addStretch()
            self.setLayout(vlay)

        except Exception as e:
            printDebug(_("Failed to import awlsim, {}",e))
            
    def start_app(self):
        self.process = QProcess(self)
        self.process.start('awlsim-gui',[])
