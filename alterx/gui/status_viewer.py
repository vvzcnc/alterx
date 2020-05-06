# -*- coding: utf-8 -*-
#
# AlterX GUI - status widget
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

__all__ = ['StatusWidget']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

from alterx.gui.util import *
from alterx.core.linuxcnc import *

class StatusWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        layout = QVBoxLayout()
        
        label = QLabel("Status Viewer")
        label.setObjectName("lbl_settings_statusviewer")
        layout.addWidget(label)
        
        self.tree = QTreeWidget()
        self.tree.setObjectName("tree_status_widget")
        self.tree.setHeaderLabels([_("Name"),_("Value")])
        self.stat_old = {}

        header = self.tree.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1,QHeaderView.Stretch)
        layout.addWidget(self.tree)
        
        self.setLayout(layout)
        
        timer = QTimer(self)
        timer.timeout.connect(self.update_tree)
        timer.start(1000)

    def update_tree(self):
        if not self.tree.visibleRegion().isEmpty():
            dict_items = {k: getattr(STAT, k) for k in filter(
                lambda s: not s.startswith('_') and not callable(s),dir(STAT))}
            
            self.get_children(dict_items,self.tree.invisibleRootItem())
                
    def get_children(self,values,parent):
        lenght = parent.childCount()
        if len(values) != lenght:
            for i in reversed(range(lenght)):
                parent.removeChild(parent.child(i))
        
        for i,item in enumerate(values):
            child = parent.child(i)

            if type(values) in (list,tuple):
                if not child:
                    child = QTreeWidgetItem(parent)
                    child.setText(0,str(i))
                val = item
            else:
                if not child:
                    child = QTreeWidgetItem(parent)
                    child.setText(0,str(item))
                val = values[item]
            
            if type(val) in (list,tuple,dict):
                self.get_children(val,child)
            else:
                if isinstance(val,float):
                    v = "{:.3f}".format(val)
                else:
                    v = "{}".format(val)
                    
                if v != child.text(1):
                    child.setText(1,v)
                    child.setBackground(1,QBrush(QColor(255,255,0)))
                else:
                    child.setBackground(1,QBrush(Qt.NoBrush))       
