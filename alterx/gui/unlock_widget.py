# -*- coding: utf-8 -*-
#
# AlterX GUI - unlock settings widget
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

from functools import partial
from datetime import datetime

import zipfile


class DocBrowser(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent) 
        self.docs_dir = pkg_resources.resource_filename("alterx", "docs")
        vlay = QVBoxLayout()
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.addWidget(QLabel(_("Docs")))
        vlay.addWidget(HSeparator())
        
        self.browser = QWebView()
        vlay.addWidget(self.browser)
        vlay.addStretch()
        self.setLayout(vlay)
        self.load("startup")
        
        UPDATER.signal("task_state", partial(self.state_changed,"task_state"))
        UPDATER.signal("task_mode", partial(self.state_changed,"task_mode"))
        UPDATER.signal("homed", partial(self.state_changed,"homed"))
        UPDATER.signal("last_error", partial(self.state_changed,"last_error"))

    def state_changed(self, source, state):
        task_state = STAT.task_state
        task_mode = STAT.task_mode
                
        if source in "last_error":
            self.load("error")
        else:
            if task_state == LINUXCNC.STATE_ESTOP:
                self.load("estop")
            elif task_state == LINUXCNC.STATE_OFF:
                self.load("turn_on")
            elif ( task_state == LINUXCNC.STATE_ON and 
                    STAT.homed != tuple(INFO.homed_list)):
                self.load("home")
            elif task_mode == LINUXCNC.MODE_MANUAL:
                self.load("manual")
            elif task_mode == LINUXCNC.MODE_MDI:
                self.load("mdi")
            elif task_mode == LINUXCNC.MODE_AUTO:
                self.load("auto")
          
    def load(self, docname):
        filepath = ""
        if os.path.isfile(os.path.join(self.docs_dir,
            "{}{}.html".format(docname,'_'.join(_._locale[:2])))):
            filepath = os.path.join(self.docs_dir,
                "{}{}.html".format(docname,'_'.join(_._locale[:2])))
        elif os.path.isfile(os.path.join(self.docs_dir,
            "{}.html".format(docname))):
            filepath = os.path.join(self.docs_dir,
                "{}.html".format(docname))
        else:
            filepath = os.path.join(self.docs_dir,"404.html")
        self.browser.load(QUrl.fromLocalFile(filepath))


class UnlockWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        parent.blocked = PREF.getpref("blocked", True, bool)
        self.parent = parent
        hlay = QHBoxLayout()
        hlay.addWidget(DocBrowser(),2)
        
        vlay = QVBoxLayout()
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.addWidget(QLabel(_("Unlock settings")))
        vlay.addWidget(HSeparator())
        vlay.addWidget(QLabel(_("Enter password:")))
        self.pw = QLineEdit()
        self.pw.setEchoMode(QLineEdit.Password)
        vlay.addWidget(self.pw)
        
        self.set_focus = self.pw.setFocus
        
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
        hlay.addLayout(vlay,1)
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
            self.parent.blocked = False
            Notify.Info(_("Access granted"))
        else:
            Notify.Info(_("Access denied"))
            self.parent.blocked = True
            
        self.change_pw_widget.setEnabled(not self.parent.blocked)
        
