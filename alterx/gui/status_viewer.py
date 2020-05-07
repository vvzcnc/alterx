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

        layout = QHBoxLayout()
        
        vlay1 = QVBoxLayout()
        label = QLabel(_("Status Viewer"))
        label.setObjectName("lbl_settings_statusviewer")
        vlay1.addWidget(label)
        
        self.tree = QTreeWidget()
        self.tree.setObjectName("tree_status_widget")
        self.tree.setHeaderLabels([_("Name"),_("Value")])

        header = self.tree.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1,QHeaderView.Stretch)
        vlay1.addWidget(self.tree)
        
        vlay2 = QVBoxLayout()
        label = QLabel(_("Parameters Editor"))
        label.setObjectName("lbl_settings_parameditor")
        vlay2.addWidget(label)
        
        self.param = QTreeWidget()
        self.param.setObjectName("tree_status_widget")
        self.param.setHeaderLabels([_("Name"),_("Value")])
        self.param.itemDoubleClicked.connect(self.param_double_clicked)
        self.param.currentItemChanged.connect(self.param_changed)

        header = self.param.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1,QHeaderView.Stretch)
        vlay2.addWidget(self.param)
        
        layout.addLayout(vlay1)
        layout.addLayout(vlay2)
        self.setLayout(layout)
        
        timer = QTimer(self)
        timer.timeout.connect(self.update_tree)
        timer.start(1000)

        self.update_parameters()

    def update_parameters(self):
        try:            
            with open(INFO.parameter_file, "r") as paramfile:
                parameters = {}
                for line in paramfile:
                    item = line.split()
                    parameters[int(item[0])] = item[1]
                self.get_children(parameters,self.param.invisibleRootItem())
        except Exception as e:
            printWarning(_("Failed to load parameter file: {}",e))

    def param_changed(self, current, previous):
        if previous:
            try:
                number=int(previous.text(0))
                if number > 5000 or number < 31 or previous.text(1):
                    if not previous.text(1):
                        self.param.invisibleRootItem().removeChild(previous)
                    return
                    
                self.param.closePersistentEditor(previous,0)
                
                parent = self.param.invisibleRootItem()
                parent.removeChild(previous)

                for i in range(parent.childCount()):
                    num = int(parent.child(i).text(0))
                    if number<num:
                        parent.insertChild(i,previous)
                        previous.setText(1,"0.000000")
                        #self.param.setCurrentItem(previous)
                        break

                with open(INFO.parameter_file,"w") as bak:
                    for i in range(parent.childCount()):
                        num = parent.child(i).text(0)
                        val = parent.child(i).text(1)
                        bak.write("{}\t{}\n".format(num,val))
            
            except Exception as e:
                self.param.invisibleRootItem().removeChild(previous)
        
    def param_double_clicked(self, item, col):
        parent = self.param.invisibleRootItem()
        if col == 1:
            child = QTreeWidgetItem()
            child.setText(0,_("New"))
            parent.insertChild(0,child)
            self.param.openPersistentEditor(child,0)   
            self.param.setCurrentItem(child)
        else:
            try:
                number=int(item.text(0))
                if number > 5000 or number < 31 or not item.text(1):
                    return

                parent.removeChild(item)
                with open(INFO.parameter_file,"w") as bak:
                    for i in range(parent.childCount()):
                        num = parent.child(i).text(0)
                        val = parent.child(i).text(1)
                        bak.write("{}\t{}\n".format(num,val))
            except Exception as e:
                printWarning(_("Failed to delete parameter: {}",e))
                
    def update_tree(self):
        if not self.tree.visibleRegion().isEmpty():
            dict_items = {k: getattr(STAT, k) for k in filter(
                lambda s: not s.startswith('_') and not callable(getattr(STAT, s)),dir(STAT))}
            self.get_children(dict_items,self.tree.invisibleRootItem())
            
    def get_children(self,values,parent):
        lenght = parent.childCount()
        if len(values) != lenght:
            for i in reversed(range(lenght)):
                parent.removeChild(parent.child(i))

        if isinstance(values,dict):
            list_items = sorted(values)
        else:
            list_items = values
            
        for i,item in enumerate(list_items):
            child = parent.child(i)
            val = item if type(values) in (list,tuple) else values[item]
 
            if isinstance(val,float):
                v = "{:.3f}".format(val)
            elif type(val) not in (list,tuple,dict):
                v = "{}".format(val)
            else:
                v = ""
            
            if not child:
                child = QTreeWidgetItem(parent)
                child.setText(0,str(i) if type(values) in (list,tuple) else str(item))
                child.setText(1,v)
            
            if type(val) in (list,tuple,dict):
                self.get_children(val,child)
            else:
                if v != child.text(1):
                    child.setText(1,v)
                    child.setBackground(1,QBrush(QColor(255,255,0)))
                else:
                    child.setBackground(1,QBrush(Qt.NoBrush))       
