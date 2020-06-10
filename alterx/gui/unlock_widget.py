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

__all__ = ['UnlockWidget']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common.preferences import *
from alterx.common import *

from alterx.gui.util import *
from alterx.core.linuxcnc import *

class UnlockWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        parent.blocked = PREF.getpref("blocked", True, bool)
        self.parent = parent
        hlay = QHBoxLayout()
        hlay.addStretch()
        
        vlay = QVBoxLayout()
        vlay.addWidget(QLabel(_("Unlock")))
        vlay.addWidget(HSeparator())
        vlay.addWidget(QLabel(_("Enter password:")))
        self.pw = QLineEdit()
        vlay.addWidget(self.pw)
        
        unlock_button = QPushButton()
        unlock_button.setText(_("Unlock"))
        unlock_button.clicked.connect(self.unlock_clicked)
        vlay.addWidget(unlock_button)
        
        vlay.addWidget(HSeparator())
        
        self.change_pw_widget = QWidget()
        self.change_pw_widget.setEnabled(not self.parent.blocked)
        change_layout = QVBoxLayout()
        self.change_pw_widget.setLayout(change_layout)
        
        check_blocked = QCheckBox()
        check_blocked.setText(_("Lock settings"))
        check_blocked.setChecked(parent.blocked)
        check_blocked.stateChanged.connect(self.block_changed)
        change_layout.addWidget(check_blocked)
        
        change_layout.addWidget(QLabel(_("New password:")))
        self.new_pw = QLineEdit()
        change_layout.addWidget(self.new_pw)
        
        change_pw_button = QPushButton()
        change_pw_button.setText(_("Change"))
        change_pw_button.clicked.connect(self.change_clicked)
        change_layout.addWidget(change_pw_button)
        
        vlay.addWidget(self.change_pw_widget)
        vlay.addStretch()
        hlay.addLayout(vlay)
        hlay.addStretch()
        self.setLayout(hlay)
        try:
            self.password = PREF.getpref("unlock","alterx", str)
        except Exception as e:
            self.password = "alterx"
            
    def block_changed(self,block):
        PREF.putpref("blocked", block)
        
    def change_clicked(self):
        PREF.putpref("unlock", self.new_pw.text())
        self.password = self.new_pw.text()
        QMessageBox.information(None,
            _("Unlock"),
            _("Password changed\n"),
            QMessageBox.Ok,
            QMessageBox.Ok)

    def unlock_clicked(self):
        if self.pw.text() == self.password:
            QMessageBox.information(None,
                _("Unlock"),
                _("Access granted\n"),
                QMessageBox.Ok,
                QMessageBox.Ok)
            self.parent.blocked = False
        else:
            QMessageBox.information(None,
                _("Unlock"),
                _("Access denied\n"),
                QMessageBox.Ok,
                QMessageBox.Ok)
            self.parent.blocked = True
            
        self.change_pw_widget.setEnabled(not self.parent.blocked)
        