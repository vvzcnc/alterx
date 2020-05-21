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
import pyqtgraph

class HalPinWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        layout = QVBoxLayout()

        label = QLabel(_("HAL Pin Viewer"))
        label.setObjectName("lbl_settings_halpin")
        layout.addWidget(label)
        
        tabs = QTabWidget()
        layout.addWidget(tabs)
        self.setLayout(layout)
        
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
        
        self.cmd_history = []
        self.cmd_history_index = 0
        self.watched_list = QTableWidget()
        self.watched_list.setObjectName("table_halpin_widget")
        self.watched_list.setColumnCount(4)
        self.watched_list.setHorizontalHeaderLabels([_("Osc."),_("Pin"),_("Type"),_("Value")])
        self.watched_list.setSelectionMode(QTableView.SingleSelection)
        self.watched_list.setSelectionBehavior(QTableView.SelectRows)
        self.watched_list.cellChanged.connect(self.on_table_changed)
        self.watched_list.cellClicked.connect(self.on_table_click)
        self.watched_list.cellDoubleClicked.connect(self.on_table_doubleclick)
        self.watched_list.setEditTriggers(QTableWidget.NoEditTriggers)
        header = self.watched_list.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3,QHeaderView.Stretch)
        vlay.addWidget(self.watched_list)
        
        self.item_label = QLabel(_("Name: "))
        self.item_label.setObjectName("lbl_halpin_item")
        vlay.addWidget(self.item_label)
               
        self.item_value = QLineEdit()
        self.item_value.setObjectName("edit_halpin_value")
        self.item_value.installEventFilter(self)

        vlay.addWidget(self.item_value)

        self.item_answer = QLabel("#:")
        self.item_answer.setObjectName("lbl_halpin_answer")
        vlay.addWidget(self.item_answer)
        
        hslay = QHBoxLayout()
        item_submit = QPushButton()
        item_submit.setText(_("Run command"))
        item_submit.clicked.connect(self.on_change_clicked)
        hslay.addWidget(item_submit)
        item_update = QPushButton()
        item_update.setText(_("Update tree"))
        item_update.clicked.connect(self.on_update_clicked)
        hslay.addWidget(item_update)
        vlay.addLayout(hslay)
       
        hlay.addLayout(vlay)
        
        halpin = QWidget()
        halpin.setLayout(hlay)
        tabs.addTab(halpin,_("HAL Pin"))
        
        osclay = QHBoxLayout()
        self.graphWidget = pyqtgraph.PlotWidget()
        osclay.addWidget(self.graphWidget)
        
        plot = self.graphWidget.plotItem
        self.plots = [plot]
        self.updateViews()
        plot.vb.sigResized.connect(self.updateViews)
        plot.getAxis('left').setStyle(tickLength=0, showValues=False)
        self.graphWidget.showGrid(x=True, y=True)
        oscilloscope = QWidget()
        oscilloscope.setLayout(osclay)
        
        self.test_submit = QPushButton()
        self.test_submit.setText(_("Run command"))
        osclay.addWidget(self.test_submit)
        tabs.addTab(oscilloscope,_("Oscilloscope"))
        
        self.clear_plot()
        self.load_data()
        
        timer = QTimer(self)
        timer.timeout.connect(self.update_watched_list)
        timer.start(1000)
        
        timer2 = QTimer(self)
        timer2.timeout.connect(self.plot_update_data)
        timer2.start(1000)

    def eventFilter(self, source, event):
        if (event.type() == QEvent.KeyPress and
            source is self.item_value):

            if event.key() == Qt.Key_Up and self.cmd_history:
                if self.cmd_history_index > 0:
                    self.cmd_history_index -= 1
                self.item_value.setText(self.cmd_history[self.cmd_history_index])
            elif event.key() == Qt.Key_Down and self.cmd_history:
                if self.cmd_history_index < len(self.cmd_history)-1:
                    self.cmd_history_index += 1
                self.item_value.setText(self.cmd_history[self.cmd_history_index])
            elif event.key() == Qt.Key_Return:
                self.on_change_clicked()
        return QWidget.eventFilter(self, source, event)

    def plot_update_data(self):
        if not self.test_submit.visibleRegion().isEmpty():
            self.clear_plot()

            color =  ['blue', 'green', 'red', 'orange', 'violet', 'brown', 'gray', 'white']
            lineStyle = [Qt.SolidLine,Qt.DashLine,Qt.DotLine,Qt.DashDotLine,
                        Qt.DashDotDotLine,Qt.SolidLine,Qt.SolidLine]
                   
            for r in range(self.watched_list.rowCount()):
                if self.watched_list.item(r,0).checkState():
                    self.data[0]=[self.watched_list.item(r,1).text(),[],[]]
            
            data = None    
            try:
                data = subprocess.check_output(["halsampler", "-t", "-n" , "1000"])
            except Exception as e:
                printInfo(_("Failed to load sampler: {}",e))   
                

            if data:
                if "overrun" in data:
                    data = data[8:]
                data = data.split(' \n')
                for d in data:
                    items = d.split(' ')
                    if len(items) != len(self.data)+1:
                        continue
                    else:
                        for i,key in enumerate(items[1:]):
                            self.data[i][1].append(int(items[0]))
                            self.data[i][2].append(float(key))
                   
            for i,key in enumerate(self.data):
                axis = pyqtgraph.AxisItem('right')
                axis.tickFont = QFont("Helvetica",pointSize = 13,weight = 1,
                                            italic = False)
                view = pyqtgraph.ViewBox()
                self.plots[0].layout.addItem(axis,2, i+3)
                self.plots[0].scene().addItem(view)
                axis.linkToView(view)
                view.setXLink(self.plots[0])
                self.plots.append(view)
                axis.setLabel(self.data[key][0],**{'color': color[i], 'font-size': '16pt'})
                pen = pyqtgraph.mkPen(QColor(color[i]), width=2, 
                                        style=lineStyle[i])
                curve = pyqtgraph.PlotCurveItem(self.data[key][2], pen=pen)
                view.addItem(curve)
                
            self.updateViews()

    def updateViews(self):
        for plot in self.plots[1:]:
            plot.setGeometry(self.plots[0].vb.sceneBoundingRect())
            plot.linkedViewChanged(self.plots[0].vb, plot.XAxis)   
            
    def clear_plot(self):
        #Clear plot
        for i,p in enumerate(self.plots[1:]):
            item = self.plots[0].layout.itemAt(2, i+3)
            self.plots[0].layout.removeItem(item)
            p.clear()
            self.plots[0].scene().removeItem(p)
        
        self.plots = [self.plots[0]]

        #Clear data
        self.data = {}
        
        self.plots[0].vb.autoRange()

    def halscope_list_update(self):
        try:
            data = subprocess.check_output(["halcmd", "unloadrt", "sampler"])
        except:
            pass

        watchlist = []
        for r in range(self.watched_list.rowCount()):
            if self.watched_list.item(r,0).checkState():
                watchlist.append([self.watched_list.item(r,1).text(),
                                    self.watched_list.item(r,2).text()])

        if not watchlist:
            return 
            
        cfg = ""
        for i in watchlist:
            if i[1] == "bit":
                cfg += "b"
            elif i[1] == "float":
                cfg += "f"
            elif i[1] == "s32":
                cfg += "s"
            elif i[1] == "u32":
                cfg += "u"
        try:
            data = subprocess.check_output(["halcmd", "loadrt", "sampler",
                                            "cfg=%s"%cfg,"depth=4000"])
            data = subprocess.check_output(["halcmd", "addf", "sampler.0", 
                                            "servo-thread"])
        except Exception as e:
            printInfo(_("Failed to load sampler: {}",e))
            return                

        for i,key in enumerate(watchlist):
            try:
                data = subprocess.check_output(["halcmd", "delsig",
                                                "sampler_net_%s"%str(i)])
            except Exception as e:
                pass
                
            try:
                data = subprocess.check_output(["halcmd", "net",
                    "sampler_net_%s"%str(i), "sampler.0.pin.%s"%str(i),key[0]])
            except Exception as e:
                printInfo(_("Failed to load sampler: {}",e))
                
        self.plot_update_data()

    def on_update_clicked(self):
        self.load_data()

    def on_change_clicked(self):
        self.item_answer.setText("#:")
        try:
            data = subprocess.check_output(("halcmd "+self.item_value.text()
                                        ).split(' '),stderr=subprocess.STDOUT)
        except Exception as e:
            data = e.output
        self.item_answer.setText("#:"+data[:-1])
        self.cmd_history.append(self.item_value.text())
        self.cmd_history_index = len(self.cmd_history)-1

    def on_table_changed(self,row,col):
        if col == 0:
            self.halscope_list_update()

    def on_table_doubleclick(self,row,col):
        self.watched_list.removeRow(row)
        self.halscope_list_update()

    def on_table_click(self,row,col):
        self.item_label.setText(_("Name: {}",self.watched_list.item(row,1).text()))
        self.item_value.setText("setp "+self.watched_list.item(row,1).text()+
                                        ' '+self.watched_list.item(row,3).text())

    def update_watched_list(self):
        if not self.watched_list.visibleRegion().isEmpty():
            for r in range(self.watched_list.rowCount()):
                item = self.watched_list.item(r,1)
                if item and item.text():
                    try:
                        data = subprocess.check_output(["halcmd", "getp", item.text()])
                    except:
                        data = None
                        
                    if data:
                        data = data[:-1]
                        value = self.watched_list.item(r,3)
                        if value:
                            value.setText(data)
                        else:
                            self.watched_list.setItem(r,3,QTableWidgetItem(data))

    def on_tree_doubleclick(self,item,column):
        if item.text(1):
            pin = item.text(0)
            pin_type = item.text(1)
            while item.parent():
                item = item.parent()
                pin = item.text(0)+'.'+pin
            self.watched_list.insertRow(0)
            checkItem = QTableWidgetItem()
            checkItem.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkItem.setCheckState(Qt.Unchecked)  
            self.watched_list.setItem(0,0,checkItem)
            self.watched_list.setItem(0,1,QTableWidgetItem(pin))
            self.watched_list.setItem(0,2,QTableWidgetItem(pin_type))
            self.watched_list.setItem(0,3,QTableWidgetItem("..."))

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
