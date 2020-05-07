# -*- coding: utf-8 -*-
#
# AlterX GUI - hal pin viewer
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

__all__ = ['HalPinWidget']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

from alterx.gui.util import *
from alterx.core.linuxcnc import *

import subprocess

class HalPinWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        layout = QVBoxLayout()

        label = QLabel(_("Hal Pin Viewer"))
        label.setObjectName("lbl_settings_halpin")
        layout.addWidget(label)
        hlay = QHBoxLayout()

        self.tree = QTreeWidget()
        self.tree.setObjectName("tree_halpin_widget")
        self.tree.setHeaderLabels([_("Name"),_("Type"),_("Dir."),_("Link")])
        self.tree.hideColumn(3)
        self.tree.itemDoubleClicked.connect(self.on_tree_doubleclick)
        header = self.tree.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2,QHeaderView.Stretch)
        
        hlay.addWidget(self.tree)
        vlay = QVBoxLayout()
        
        self.watched_list = QTableWidget()
        self.watched_list.setObjectName("table_halpin_widget")
        self.watched_list.setColumnCount(2)
        self.watched_list.setHorizontalHeaderLabels([_("Pin"),_("Value")])
        self.watched_list.setSelectionMode(QTableView.SingleSelection)
        self.watched_list.setSelectionBehavior(QTableView.SelectRows)
        self.watched_list.cellClicked.connect(self.on_table_click)
        self.watched_list.setEditTriggers(QTableWidget.NoEditTriggers)
        header = self.watched_list.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1,QHeaderView.Stretch)
        vlay.addWidget(self.watched_list)
        
        self.item_label = QLabel(_("Name: "))
        self.item_label.setObjectName("lbl_halpin_item")
        vlay.addWidget(self.item_label)
               
        self.item_value = QLineEdit()
        self.item_value.setObjectName("edit_halpin_value")
        vlay.addWidget(self.item_value)

        self.item_answer = QLabel("#:")
        self.item_answer.setObjectName("lbl_halpin_answer")
        vlay.addWidget(self.item_answer)
        
        item_submit = QPushButton()
        item_submit.setText(_("Run command"))
        item_submit.clicked.connect(self.on_change_clicked)
        vlay.addWidget(item_submit)
       
        hlay.addLayout(vlay)
        layout.addLayout(hlay)
        self.setLayout(layout)
        
        self.load_data()
        
        timer = QTimer(self)
        timer.timeout.connect(self.update_watched_list)
        timer.start(1000)

    def on_change_clicked(self):
        self.item_answer.setText("#:")
        try:
            data = subprocess.check_output(("halcmd "+self.item_value.text()).split(' '),stderr=subprocess.STDOUT)
        except Exception as e:
            data = e.output
        self.item_answer.setText("#:"+data[:-1])

    def on_table_click(self,row,col):
        self.item_label.setText(_("Name: {}",self.watched_list.item(row,0).text()))
        self.item_value.setText("setp "+self.watched_list.item(row,0).text()+' '+self.watched_list.item(row,1).text())

    def update_watched_list(self):
        if not self.watched_list.visibleRegion().isEmpty():
            for r in range(self.watched_list.rowCount()):
                item = self.watched_list.item(r,0)
                if item and item.text():
                    try:
                        data = subprocess.check_output(["halcmd", "getp", item.text()])
                    except:
                        data = None
                        
                    if data:
                        data = data[:-1]
                        value = self.watched_list.item(r,1)
                        if value:
                            value.setText(data)
                        else:
                            self.watched_list.setItem(r,1,QTableWidgetItem(data))

    def on_tree_doubleclick(self,item,column):
        if item.text(1):
            pin = item.text(0)
            while item.parent():
                item = item.parent()
                pin = item.text(0)+'.'+pin
            self.watched_list.insertRow(0)
            self.watched_list.setItem(0,0,QTableWidgetItem(pin))
            self.watched_list.setItem(0,1,QTableWidgetItem("..."))

    def load_data(self):
        self.tree.clear()
        
        try:
            data_pin = subprocess.check_output(["halcmd", "show", "pin"])
            data_pin = data_pin.split('\n')[2:]
            data_pin = filter(lambda a: len(a)>4,
                [[c for c in s.split(' ') if len(c)>0] for s in data_pin])

            data_param = subprocess.check_output(["halcmd", "show", "param"])
            data_param = data_param.split('\n')[2:]
            data_param = filter(lambda a: len(a)>4,
                [[c for c in s.split(' ') if len(c)>0] for s in data_param])

            data = data_pin + data_param
        except Exception as e:
            printInfo(_("Failed to get hal pin list: {}",e))
            return
        
        self.get_tree(data,self.tree)

    def get_tree(self,pins,parent):
        cat_list = []
        for pin in pins:
            if '.' in pin[4]:
                cat = pin[4].split('.')[0]
                if cat in cat_list:
                    continue
                cat_list.append(cat)
                child = QTreeWidgetItem(parent)
                child.setText(0,"{}".format(cat))
                self.get_tree(map(lambda s: s[:4]+[s[4][len(cat)+1:]]+s[5:],
                              filter(lambda s: s[4].startswith(cat+".") and
                                '.' in s[4],pins)),child)
            else:
                child = QTreeWidgetItem(parent)
                child.setText(0,pin[4])
                child.setText(1,pin[1])
                child.setText(2,pin[2])
                if len(pin) == 7:
                    child.setText(3,pin[6])
