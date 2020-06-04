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
import socket
import struct

class HSeparator(QFrame):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

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
        self.tree.setHeaderLabels([_("Name"),_("Type"),_("Dir."),_("Addr.")])
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
        self.watched_list.setColumnCount(6)
        self.watched_list.setHorizontalHeaderLabels([_("Osc."),_("Pin"),_("Type"),_("Value"),_("Addr."),_("Dir.")])
        self.watched_list.hideColumn(4)
        self.watched_list.hideColumn(5)
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
        osclay.addWidget(self.graphWidget,9)
        
        plot = self.graphWidget.plotItem
        self.plots = [plot]
        self.updateViews()
        plot.vb.sigResized.connect(self.updateViews)
        plot.getAxis('left').setStyle(tickLength=0, showValues=False)
        self.graphWidget.showGrid(x=True, y=True)
        oscilloscope = QWidget()
        oscilloscope.setLayout(osclay)
        
        controllay = QVBoxLayout()
        
        rslay = QHBoxLayout()
        osc_run = QPushButton()
        osc_run.setText(_("Run"))
        osc_run.clicked.connect(self.on_oscrun_clicked)
        rslay.addWidget(osc_run)
        osc_stop = QPushButton()
        osc_stop.setText(_("Stop"))
        osc_stop.clicked.connect(self.on_oscstop_clicked)
        rslay.addWidget(osc_stop)
        controllay.addLayout(rslay)
        
        controllay.addWidget(HSeparator())
        
        oswidget = QWidget()
        oslay = QHBoxLayout()
        osc_auto = QRadioButton()
        osc_auto.mode = 0
        osc_auto.setText(_("Auto"))
        osc_auto.setChecked(True)
        osc_auto.toggled.connect(self.osc_mode_changed)
        oslay.addWidget(osc_auto)
        osc_shot = QRadioButton()
        osc_shot.mode = 1
        osc_shot.setText(_("One Shot"))
        osc_shot.toggled.connect(self.osc_mode_changed)
        oslay.addWidget(osc_shot)
        oswidget.setLayout(oslay)
        controllay.addWidget(oswidget)
        
        controllay.addWidget(HSeparator())
        
        trigwidget = QWidget()
        triglay = QVBoxLayout()
        trig_none = QRadioButton()
        trig_none.trig = 1
        trig_none.setText(_("None"))
        trig_none.setChecked(True)
        trig_none.toggled.connect(self.osc_trig_changed)
        triglay.addWidget(trig_none)
        trig_change = QRadioButton()
        trig_change.trig = 5
        trig_change.setText(_("Change"))
        trig_change.toggled.connect(self.osc_trig_changed)
        triglay.addWidget(trig_change)
        trig_high = QRadioButton()
        trig_high.trig = 3
        trig_high.setText(_("High"))
        trig_high.toggled.connect(self.osc_trig_changed)
        triglay.addWidget(trig_high)
        trig_low = QRadioButton()
        trig_low.setText(_("Low"))
        trig_low.trig = 4
        trig_low.toggled.connect(self.osc_trig_changed)
        triglay.addWidget(trig_low)
        trigwidget.setLayout(triglay)
        controllay.addWidget(trigwidget)
        
        controllay.addWidget(HSeparator())

        controllay.addWidget(QLabel(_("Trigger signal:")))
        self.trig_combo = QComboBox()
        self.trig_combo.setCurrentIndex(-1)
        self.trig_combo.currentIndexChanged.connect(self.trigger_changed)
        controllay.addWidget(self.trig_combo)
        
        controllay.addWidget(HSeparator())
        
        controllay.addWidget(QLabel(_("Trigger value:")))
        self.trig_edit = QLineEdit()
        controllay.addWidget(self.trig_edit)

        controllay.addStretch()
        osclay.addLayout(controllay,1)
        tabs.addTab(oscilloscope,_("Oscilloscope"))
        
        self.trigger_mode = 1
        self.shot_mode = 0
        
        self.clear_plot()
        self.load_data()
        
        timer_viewer = QTimer(self)
        timer_viewer.timeout.connect(self.update_watched_list)
        timer_viewer.start(1000)
        
        timer_osc = QTimer(self)
        timer_osc.timeout.connect(self.plot_update_data)
        timer_osc.start(1000)

    def trigger_changed(self,i):
        name = self.trig_combo.itemData(i, role=Qt.DisplayRole)
        if name:
            stype = self.trig_combo.itemData(i, role=Qt.UserRole + 1)
            addr = self.trig_combo.itemData(i, role=Qt.UserRole + 2)
            
            self.send_packet(4,stype,addr)

    def on_oscrun_clicked(self):
        try:
            t = self.trig_edit.text()
            if t:
                t = float(t)
            else:
                t = 0
            self.send_packet(5,self.trigger_mode,t)
        except Exception as e:
            printInfo(_("Failed to send run cmd: {}",e))
        
    def on_oscstop_clicked(self):
        self.send_packet(0,0,0)

    def osc_trig_changed(self):
        rb = self.sender()
        if rb.isChecked():
            self.trigger_mode = rb.trig
        
    def osc_mode_changed(self):
        rb = self.sender()
        if rb.isChecked():
            self.shot_mode = rb.mode

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
        if not self.trig_edit.visibleRegion().isEmpty():
            #Check (Check,0,0)
            data = self.send_packet(6,0,0)
            if data[:-1] in "2":
                #Get (Get,0,0)
                data = self.send_packet(7,0,0)
                if self.shot_mode:
                    self.on_oscstop_clicked()
                else:
                    self.on_oscrun_clicked()
            else:
                return
                
            if not data:
                return

            self.clear_plot()

            color =  ['blue', 'green', 'red', 'orange', 'violet', 'brown',
                        'gray', 'white']
            lineStyle = [Qt.SolidLine,Qt.DashLine,Qt.DotLine,Qt.DashDotLine,
                        Qt.DashDotDotLine,Qt.SolidLine,Qt.SolidLine]
                   
            watchedlist = []
            for r in range(self.watched_list.rowCount()):
                if self.watched_list.item(r,0).checkState():
                    name = self.watched_list.item(r,1).text()
                    watchedlist.append(name)
                    self.data[name]=[[],[]]

            if "overrun" in data:
                data = data[8:]
            data = data.split('\n')
            for i,d in enumerate(data):
                s = d.split(' ')
                if len(s) == 2:
                    channel = s[0]
                    value = s[1]
                
                self.data[watchedlist[int(channel)]][0].append(int(i))
                self.data[watchedlist[int(channel)]][1].append(float(value))               

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
                axis.setLabel(key,**{'color': color[i], 'font-size': '16pt'})
                pen = pyqtgraph.mkPen(QColor(color[i]), width=2, 
                                        style=lineStyle[i])
                curve = pyqtgraph.PlotCurveItem(self.data[key][1], pen=pen)
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
        watchlist = []
        for r in range(self.watched_list.rowCount()):
            if self.watched_list.item(r,0).checkState():
                watchlist.append([self.watched_list.item(r,4).text(),
                    self.watched_list.item(r,5).text(),
                    self.watched_list.item(r,1).text()])

        if not watchlist:
            return 
            
        self.trig_combo.clear()
        model = self.trig_combo.model()
        
        for i,key in enumerate(watchlist):
            #Set (Channel, NChannel*10+ChannelType, Pin offset)
            if key[1] in ("RO","RW"):
                stype = 2
            elif key[1] in ("In","Out","IO"):
                stype = 0
            else:
                continue
            self.send_packet(3,i*10+stype,int(key[0],16))
            item = QStandardItem(key[2])
            item.setData(stype, role=Qt.UserRole + 1)
            item.setData(int(key[0],16), role=Qt.UserRole + 2)
            model.appendRow(item)

        self.trig_combo.setCurrentIndex(-1)
        
        #Clear data old data
        self.send_packet(3,(i+1)*10,0)
           
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
                addr = self.watched_list.item(r,4)
                pdir = self.watched_list.item(r,5)
                if addr and addr.text() and pdir and pdir.text():
                    try:
                        if pdir.text() in ("RO","RW"):
                            stype = 2
                        elif pdir.text() in ("In","Out","IO"):
                            stype = 0
                        else:
                            continue
                        data = self.send_packet(2,stype,int(addr.text(),16))
                    except:
                        continue

                    if data:
                        data = data[:-1].replace(' ','')
                        value = self.watched_list.item(r,3)
                        if value:
                            value.setText(data)
                        else:
                            self.watched_list.setItem(r,3,QTableWidgetItem(data))

    def on_tree_doubleclick(self,item,column):
        if item.text(1):
            pin = item.text(0)
            pin_type = item.text(1)
            pin_dir = item.text(2)
            pin_addr = item.text(3)
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
            self.watched_list.setItem(0,4,QTableWidgetItem(pin_addr))
            self.watched_list.setItem(0,5,QTableWidgetItem(pin_dir))

    def send_packet(self,cmd,stype,value):
        answer = ""
        HOST = '127.0.0.1'  # The server's hostname or IP address
        PORT = 5000     # The port used by the server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #print("> ",cmd,stype,value)
        try:
            s.connect((HOST, PORT))
            packet = struct.pack("BBd" if type(value) == float else "BBl",
                                    cmd,stype,value)
            s.sendall(packet)
            while True:
                data = s.recv(1024)
                answer += data
                if not data:
                    break
                    
        except Exception as e:
            printInfo(_("Failed to send packet: {}",e))
        finally:
            s.close()
        #print("< ",answer)
        return answer

    def load_data(self):
        self.tree.clear()
        
        try:
            #Get (Hal list, Hal pin, 0)
            data_pin = self.send_packet(1,0,0)
            data_pin = data_pin.split('\n')
            data_pin = filter(lambda a: len(a)==4,
                [[c for c in s.split(' ') if len(c)>0] for s in data_pin])
                
            #Get (Hal list, Hal param, 0) 
            data_param = self.send_packet(1,2,0)
            data_param = data_param.split('\n')
            data_param = filter(lambda a: len(a)==4,
                [[c for c in s.split(' ') if len(c)>0] for s in data_param])

            data = data_pin + data_param
        except Exception as e:
            printInfo(_("Failed to get hal pin list: {}",e))
            return
        
        self.get_tree(data,self.tree)

    def get_type_text(self,stype):
        t={'-1':'NULL','1':'BIT','2':'FLOAT','3':'S32','4':'U32','5':'PORT'}
        if stype in t:
            return t[stype]   
        else:
            return stype
 
    def get_dir_text(self,sdir):
        t={'-1':'None','16':'In','32':'Out','48':'IO','64':'RO','192':'RW'}
        if sdir in t:
            return t[sdir] 
        else:
            return sdir

    def get_tree(self,pins,parent):
        cat_list = []
        for pin in pins:
            if '.' in pin[3]:
                cat = pin[3].split('.')[0]
                if cat in cat_list:
                    continue
                cat_list.append(cat)
                child = QTreeWidgetItem(parent)
                child.setText(0,"{}".format(cat))
                self.get_tree(map(lambda s: s[:3]+[s[3][len(cat)+1:]],
                              filter(lambda s: s[3].startswith(cat+".") and
                                '.' in s[3],pins)),child)
            else:
                child = QTreeWidgetItem(parent)
                child.setText(0,pin[3])
                child.setText(1,self.get_type_text(pin[1]))
                child.setText(2,self.get_dir_text(pin[2]))
                child.setText(3,pin[0])
