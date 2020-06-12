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

import zipfile
from datetime import datetime

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
        self.pw.setEchoMode(QLineEdit.Password)
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
        self.new_pw.setEchoMode(QLineEdit.Password)
        change_layout.addWidget(self.new_pw)
        
        change_pw_button = QPushButton()
        change_pw_button.setText(_("Change"))
        change_pw_button.clicked.connect(self.change_clicked)
        change_layout.addWidget(change_pw_button)
        
        change_layout.addWidget(HSeparator())
        
        load_cfg_button = QPushButton()
        load_cfg_button.setText(_("Load configuration"))
        load_cfg_button.clicked.connect(self.load_cfg_clicked)
        change_layout.addWidget(load_cfg_button)
        
        save_cfg_button = QPushButton()
        save_cfg_button.setText(_("Save configuration"))
        save_cfg_button.clicked.connect(self.save_cfg_clicked)
        change_layout.addWidget(save_cfg_button)
        
        
        vlay.addWidget(self.change_pw_widget)
        vlay.addStretch()
        hlay.addLayout(vlay)
        hlay.addStretch()
        self.setLayout(hlay)
        try:
            self.password = PREF.getpref("unlock","alterx", str)
        except Exception as e:
            self.password = "alterx"
            
    def load_cfg_clicked(self):
        dialog = QFileDialog(self)
        dialog.setDirectory(INFO.working_dir)
        dialog.setNameFilters(["ZIP (*.zip)"])
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        if dialog.exec_() == QDialog.Accepted:
            fileName = dialog.selectedFiles()[0]
            with zipfile.ZipFile(fileName, 'r', zipfile.ZIP_DEFLATED) as zipf:
                for file in zipf.namelist():
                    zipf.extract(file,INFO.working_dir)
        
    def save_cfg_clicked(self):
        dialog = QFileDialog()
        dialog.setDirectory(INFO.working_dir)
        dialog.setFilter(dialog.filter()|QDir.Hidden)
        dialog.setDefaultSuffix("zip")
        date = datetime.now()
        dialog.selectFile(os.path.basename(INFO.working_dir).replace(".","_") + 
                            date.strftime("_%Y%m%d_%H%M%S"))
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters(["ZIP (*.zip)"])

        if dialog.exec_() == QDialog.Accepted:
            fileName = dialog.selectedFiles()[0]
            with zipfile.ZipFile(fileName, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(INFO.working_dir):
                    for file in files:
                        if not os.path.samefile(os.path.join(root,file),
                                                 fileName):
                            filepath   = os.path.join(root, file)
                            parentpath = os.path.relpath(filepath,
                                                         INFO.working_dir)
                            zipf.write(os.path.join(root, file),parentpath)

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
        