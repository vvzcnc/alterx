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
from alterx.core.ascope import AScope as osc
from alterx.core.remote import RemoteControl as remote

from functools import partial

import pyqtgraph
import re

option_list = [
    "SCALE_GAIN",
    "SCALE_OFFSET",
    "P",
    "I",
    "D",
    "BIAS",
    "FF0",
    "FF1",
    "FF2",
    "DEADBAND",
    "MAX_OUTPUT",
    "SCALE_MAX",
    "OUTPUT_MIN_LIMIT",
    "OUTPUT_MAX_LIMIT",
    "ENCODER_SCALE",
]

class ReceiveThread(QThread):
    message = pyqtSignal(str)
    
    def __init__(self,cmds):
        QThread.__init__(self, parent=None)
        self.cmds = cmds
        
    def run(self):
        for cmd in self.cmds:
            try:
                data = remote.send_packet("halcmd "+cmd)
            except Exception as e:
                data = u"#:"

            self.message.emit(data)


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
        self.control = 0
        hlay = QHBoxLayout()

        self.tree = QTreeWidget()
        self.tree.setObjectName("tree_halpin_widget")
        self.tree.setHeaderLabels( [ _("Name"), _("Type"), _("Dir."), 
                                    _("Addr."), _("HAL type") ] )
        self.tree.hideColumn(3)
        self.tree.hideColumn(4)
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
        self.watched_list.setColumnCount(9)
        self.watched_list.setHorizontalHeaderLabels( [ _("Osc."), _("Pin"), 
                _("Type"), _("Value"), _("Addr."), _("Dir."), _("HAL type"), _("Min"), _("Max")  ] )
        self.watched_list.hideColumn(4)
        self.watched_list.hideColumn(5)
        self.watched_list.hideColumn(6)
        self.watched_list.hideColumn(7)
        self.watched_list.hideColumn(8)
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
        self.set_focus = self.item_value.setFocus

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
        self.vLine = pyqtgraph.InfiniteLine( angle=90, movable=False ) 
        self.hLine = pyqtgraph.InfiniteLine( angle=0, movable=False ) 
        self.tLine = pyqtgraph.InfiniteLine( angle=0, movable=False,
                                                pen={'color':'r'} ) 
                            
        plot.vb.addItem(self.vLine)
        self.graphWidget.setMouseTracking(True)
        self.graphWidget.viewport().installEventFilter(self)  

        self.axis_x = self.graphWidget.getAxis('bottom')
        font=QFont()
        font.setPixelSize(16)
        self.axis_x.tickFont = font
        self.axis_x.setStyle(tickTextOffset = 10)

        oscilloscope = QWidget()
        oscilloscope.setLayout(osclay)
        
        controllay = QVBoxLayout()
        
        rslay = QHBoxLayout()
        osc_run = QPushButton()
        osc_run.setText(_("Run"))
        osc_run.clicked.connect(self.on_oscrun_clicked)
        rslay.addWidget(osc_run,1)
        osc_stop = QPushButton()
        osc_stop.setText(_("Stop"))
        osc_stop.clicked.connect(self.on_oscstop_clicked)
        rslay.addWidget(osc_stop,1)
        self.osc_status = QLabel()
        rslay.addWidget(self.osc_status,1)
        controllay.addLayout(rslay)
        
        controllay.addWidget(HSeparator())
        
        self.shot_mode = 0
        oswidget = QWidget()
        oslay = QHBoxLayout()
        self.osc_auto = QRadioButton()
        self.osc_auto.mode = 0
        self.osc_auto.setText(_("Auto"))
        self.osc_auto.setChecked(True)
        self.osc_auto.toggled.connect(self.osc_mode_changed)
        oslay.addWidget(self.osc_auto)
        self.osc_shot = QRadioButton()
        self.osc_shot.mode = 1
        self.osc_shot.setText(_("One Shot"))
        self.osc_shot.toggled.connect(self.osc_mode_changed)
        oslay.addWidget(self.osc_shot)
        oswidget.setLayout(oslay)
        controllay.addWidget(oswidget)
        
        controllay.addWidget(HSeparator())
        
        self.trigger_mode = osc.SAMPLE_RUN
        trigwidget = QWidget()
        triglay = QVBoxLayout()
        self.trig_none = QRadioButton()
        self.trig_none.trig = osc.SAMPLE_RUN
        self.trig_none.setText(_("None"))
        self.trig_none.setChecked(True)
        self.trig_none.toggled.connect(self.osc_trig_changed)
        triglay.addWidget(self.trig_none)
        self.trig_change = QRadioButton()
        self.trig_change.trig = osc.SAMPLE_CHANGE
        self.trig_change.setText(_("Change"))
        self.trig_change.toggled.connect(self.osc_trig_changed)
        triglay.addWidget(self.trig_change)
        self.trig_high = QRadioButton()
        self.trig_high.trig = osc.SAMPLE_HIGH
        self.trig_high.setText(_("High"))
        self.trig_high.toggled.connect(self.osc_trig_changed)
        triglay.addWidget(self.trig_high)
        self.trig_low = QRadioButton()
        self.trig_low.setText(_("Low"))
        self.trig_low.trig = osc.SAMPLE_LOW
        self.trig_low.toggled.connect(self.osc_trig_changed)
        triglay.addWidget(self.trig_low)
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
        self.trig_edit.editingFinished.connect(self.trigger_value_changed)
        controllay.addWidget(self.trig_edit)

        controllay.addWidget(HSeparator())
        
        controllay.addWidget(QLabel(_("Divider value:")))
        self.div_edit = QSpinBox()
        self.div_edit.setMaximum(250)
        self.div_edit.setMinimum(1)
        self.div_edit.setValue(1)
        self.div_edit.valueChanged.connect(self.divider_value_changed)
        controllay.addWidget(self.div_edit)
        
        controllay.addWidget(HSeparator())

        self.info_label = QLabel()
        controllay.addWidget(self.info_label)

        controllay.addWidget(HSeparator())
        
        self.value_label = QLabel()
        self.value_label.setWordWrap(True)
        controllay.addWidget(self.value_label)

        controllay.addStretch()
        osclay.addLayout(controllay,2)
        tabs.addTab(oscilloscope,_("Oscilloscope"))
        
        presets = QWidget()
        preset_vlay = QVBoxLayout()
        preset_btns = QHBoxLayout()
        
        preset_load = QPushButton()
        preset_load.setText(_("Load"))
        preset_load.clicked.connect(self.on_preset_load_clicked)
        preset_btns.addWidget(preset_load)
        
        preset_save = QPushButton()
        preset_save.setText(_("Save"))
        preset_save.clicked.connect(self.on_preset_save_clicked)
        preset_btns.addWidget(preset_save)
        
        preset_delete = QPushButton()
        preset_delete.setText(_("Delete"))
        preset_delete.clicked.connect(self.on_preset_delete_clicked)
        preset_btns.addWidget(preset_delete)
    
        preset_vlay.addLayout(preset_btns)

        self.preset_name = QLineEdit()
        preset_vlay.addWidget(self.preset_name)
        
        self.preset_list = QListWidget()
        self.preset_list.currentRowChanged.connect(self.preset_selected_changed)
        preset_vlay.addWidget(self.preset_list)
       
        #preset_vlay.addStretch()
        presets.setLayout(preset_vlay)
        tabs.addTab(presets,_("Presets"))
       
        pid_tuning = QWidget()
        pid_vlay = QVBoxLayout()
        
        pid_btn_lay = QHBoxLayout()
        pid_test = QPushButton(_("Test"))
        pid_test.clicked.connect(self.on_pid_test_clicked)
        pid_btn_lay.addWidget(pid_test)
        
        pid_cancel = QPushButton(_("Cancel"))
        pid_cancel.clicked.connect(self.on_pid_cancel_clicked)
        pid_btn_lay.addWidget(pid_cancel)
        
        pid_save = QPushButton(_("Save"))
        pid_save.clicked.connect(self.on_pid_save_clicked)
        pid_btn_lay.addWidget(pid_save)
        
        pid_vlay.addLayout(pid_btn_lay)
        self.pid_joint_tabs = QTabWidget()
        pid_vlay.addWidget(self.pid_joint_tabs)
        
        try:
            self.ini = os.environ['INI_FILE_NAME']
        except Exception as e:
            self.ini = None
            printError(_("AlterX: Config file not found"))

        self.config = ConfigParser.ConfigParser(dict_type=MultiOrderedDict,
            allow_no_value=True)
        self.config.optionxform = str

        self.new_config = ConfigParser.ConfigParser(dict_type=MultiOrderedDict,
            allow_no_value=True)
        self.new_config.optionxform = str

        if self.ini:
            self.config.read(self.ini)

        self.load_pid_config()

        pid_tuning.setLayout(pid_vlay)
        tabs.addTab(pid_tuning,_("PID"))

        try:
            self.preset_dir = self.config.get("DISPLAY","OSC_PRESET_DIR")
        except:
            self.preset_dir = None

        try:
            for f in os.listdir(self.preset_dir):
                if f.lower().endswith('.ops'):
                    self.preset_list.addItem(f)
        except:
            pass
       
        self.clear_plot()
        self.load_data()
        
        timer_viewer = QTimer(self)
        timer_viewer.timeout.connect(self.update_watched_list)
        timer_viewer.start(1000)
        
        timer_osc = QTimer(self)
        timer_osc.timeout.connect(self.plot_update_data)
        timer_osc.start(1000)

    def load_pid_config(self):
        if self.pid_joint_tabs.count() > 0:
            for i in reversed(range(self.pid_joint_tabs.count())):
                try:
                    self.pid_joint_tabs.widget(i).deleteLater()
                    self.pid_joint_tabs.removeTab(i)
                except Exception as e:
                    printDebug(_("Delete pid tab exception: {}",e))

        for s in sorted(filter(lambda x: "JOINT_" in x,
                self.config.sections())):

            if s not in self.new_config.sections():
                self.new_config.add_section(s)

            jscroll = QScrollArea()
            jscroll.setWidgetResizable(True)
            jwidget = QWidget()
            jscroll.setWidget(jwidget)

            jvlay = QVBoxLayout()
            jwidget.setLayout(jvlay)
            
            for o in sorted(filter(lambda x: x in option_list,
                    self.config.options(s))):
                jhlay = QHBoxLayout()
                jlabel = QLabel(o)
                jlabel.setObjectName("lbl_pid_editor_{}_{}".format(s,o))
                jhlay.addWidget(jlabel,2)
                jedit = QLineEdit()
                jedit.setText(self.config.get(s,o))
                jedit.setObjectName("edit_pid_editor_{}_{}".format(s,o))
                jedit.textChanged.connect(partial(self.pid_editing_finished,
                    s,o,jedit))
                jhlay.addWidget(jedit,4)
                jvlay.addLayout(jhlay)
                
            jvlay.addStretch()
            self.pid_joint_tabs.addTab(jscroll,s)

    def pid_editing_finished(self,section,option,widget):
        self.new_config.set(section,option,widget.text())
        #printDebug(_("PID Option changed: {} {} {}",section,option,widget.text()))

    def on_pid_save_clicked(self):
        for s in self.new_config.sections():
            for o in self.new_config.options(s):
                printDebug(_("PID Option [{}]{} changed: {} => {}", s, o, 
                    self.config.get(s,o), self.new_config.get(s,o)))
                self.config.set(s,o,self.new_config.get(s,o))

        with open(self.ini, "w") as fp:
            if self.config._defaults:
                fp.write("[%s]\n" % DEFAULTSECT)
                for (key, value) in self.config._defaults.items():
                    value = toUnicode(value)
                    key = toUnicode(key)
                    if '\n' in value:
                        value = value.split('\n')
                    else:
                        value = [value]
                    for v in value:                            
                        if (v is not None) or (self.config._optcre == self.config.OPTCRE):
                            data = "{} = {}\n".format(key, v)
                            fp.write(data.encode('utf-8'))
                fp.write("\n")

            for section in self.config._sections:
                fp.write("[%s]\n" % section)
                for (key, value) in self.config._sections[section].items():
                    value = toUnicode(value)
                    key = toUnicode(key)
                    if key == "__name__":
                        continue
                    if '\n' in value:
                        value = value.split('\n')
                    else:
                        value = [value]
                    for v in value:    
                        if (v is not None) or (self.config._optcre == self.config.OPTCRE):
                            data = "{} = {}\n".format(key, v)
                            fp.write(data.encode('utf-8'))
                fp.write("\n")
            printInfo(_("Config file saved."))


    def on_pid_cancel_clicked(self):
        self.load_pid_config()

    def on_pid_test_clicked(self):
        try:
            hal_files = self.config.get("HAL","HALFILE")
        except:
            hal_files = []

        if hal_files:
            hal_files = hal_files.split('\n')

        cmds = []
        for hal in hal_files:
            with open(hal) as f:
                for line in f:
                    for s in filter(lambda x: "JOINT_" in x,
                            self.new_config.sections()):
                        for o in filter(lambda x: x in option_list,
                                self.new_config.options(s)):
                            sstr = "[{}]{}".format(s,o)
                            pos = line.find(sstr)

                            if ( pos >= 0 and
                                    len(line) > pos+len(sstr) and
                                    not line[pos+len(sstr)].isalpha() ):

                                msg = line.replace("[{}]{}".format(s,o),self.config.get(s,o))
                                msg = re.sub(r"[\n\t]*","", msg)
                                msg = re.sub(r" +"," ", msg)
                                cmds.append(msg)

        if cmds:
            self.thread = ReceiveThread(cmds)
            self.thread.message.connect(lambda s: printInfo(s if s else "PID CMD OK"))
            self.thread.start()
        
                                
    def preset_selected_changed(self):
        item = self.preset_list.currentItem()
        if item:
            fname = item.text()
            self.preset_name.setText(fname)

    def on_preset_delete_clicked(self):
        item = self.preset_list.currentItem()
        if item:
            fname = item.text()
            if fname:
                if os.path.exists(os.path.join(self.preset_dir,fname)):
                    os.remove(os.path.join(self.preset_dir,fname))
                    self.preset_name.setText('')
                    self.preset_list.takeItem(self.preset_list.row(item))
                
    def clear_watched_list(self):
        for r in reversed(range(self.watched_list.rowCount())):
            self.watched_list.removeRow(r)
                
    def on_preset_load_clicked(self):
        item = self.preset_list.currentItem()
        if not item:
            return

        fname = item.text()
        with open(os.path.join(self.preset_dir,fname)) as fin:
            self.clear_watched_list()
            try:
                index = 0
                for line in fin:
                    params = line.split(' ')
                    
                    item = self.find_item(params[1],self.tree)
                    if item:
                        self.on_tree_doubleclick(item, None, row=index)
                        
                        self.watched_list.item(index,0).setCheckState(int(params[0]))
                            
                        self.trig_edit.setText(params[2])
                        
                        self.div_edit.setValue(int(params[3]))

                        if int(params[4]) == 0:
                            self.osc_auto.setChecked(True)
                        else:
                            self.osc_shot.setChecked(True)
                        
                        if int(params[5]) == osc.SAMPLE_RUN:
                            self.trig_none.setChecked(True)
                        if int(params[5]) == osc.SAMPLE_CHANGE:
                            self.trig_change.setChecked(True)
                        if int(params[5]) == osc.SAMPLE_HIGH:
                            self.trig_high.setChecked(True)
                        if int(params[5]) == osc.SAMPLE_LOW:
                            self.trig_low.setChecked(True)
                        
                        self.trig_combo.setCurrentIndex(int(params[6]))
                        
                        if params[7]:
                            self.watched_list.setItem(index,7,QTableWidgetItem(params[7]))
                        if params[8]:
                            self.watched_list.setItem(index,8,QTableWidgetItem(params[8]))
                        
                        index += 1
                        
            except Exception as e:
                print(e)
                self.clear_watched_list()
         
    def on_preset_save_clicked(self):
        fname = self.preset_name.text()
        if fname:
            if not fname.endswith(".ops"):
                fname += ".ops"
            
            if not os.path.isdir(self.preset_dir):
                os.mkdir(self.preset_dir)
            
            with open(os.path.join(self.preset_dir,fname),"w+") as fout:
                for r in range(self.watched_list.rowCount()):
                    min = self.watched_list.item(r,7)
                    max = self.watched_list.item(r,8)
                    min = min.text() if min else ''
                    max = max.text() if max else ''
                    line = ' '.join(
                        (str(self.watched_list.item(r,0).checkState()),
                         self.watched_list.item(r,1).text(), 
                         self.trig_edit.text(),self.div_edit.text(),
                         str(self.shot_mode),
                         str(self.trigger_mode),
                         str(self.trig_combo.currentIndex()),
                         min, max,'\n'))
                    fout.write(line)

            if os.path.exists(os.path.join(self.preset_dir,fname)):
                presets = self.preset_list.findItems(fname,Qt.MatchExactly)
                if len(presets) == 0:
                    self.preset_list.addItem(fname)

    def divider_value_changed(self):
        try:
            div = self.div_edit.value()-1
            osc.send_packet(self.control,osc.OSC_DIV,div,0)
        except:
            pass
		
    def trigger_value_changed(self):
        try:
            self.tLine.setPos(float(self.trig_edit.text()))
        except:
            pass

    def trigger_changed(self,i):
        name = self.trig_combo.itemData(i, role=Qt.DisplayRole)
        if name:
            stype = self.trig_combo.itemData(i, role=Qt.UserRole + 1)
            addr = self.trig_combo.itemData(i, role=Qt.UserRole + 2)
            
            osc.send_packet(self.control,osc.OSC_TRIG,stype,addr)
            if len(self.plots) > i+1 and i>=0:
                self.plots[i+1].addItem(self.hLine)
                self.plots[i+1].addItem(self.tLine)

    def on_oscrun_clicked(self):
        try:
            t = self.trig_edit.text()
            osc.send_packet(self.control,osc.OSC_RUN,self.trigger_mode, float(t) if t else 0 )
        except Exception as e:
            printInfo(_("Failed to send run cmd: {}",e))
        
    def on_oscstop_clicked(self):
        osc.send_packet(self.control,osc.OSC_STOP,0,0)

    def osc_trig_changed(self):
        rb = self.sender()
        if rb.isChecked():
            self.trigger_mode = rb.trig
        
    def osc_mode_changed(self):
        rb = self.sender()
        if rb.isChecked():
            self.shot_mode = rb.mode

    def eventFilter(self, source, event):
        if ( event.type() == QEvent.KeyPress and
                source is self.item_value ):

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

        elif ( event.type() == QEvent.MouseMove and
                source is self.graphWidget.viewport() ):
            pos = event.pos()
            text = ""
            if self.graphWidget.sceneBoundingRect().contains(pos):
                mousePoint = self.plots[0].vb.mapSceneToView(pos)
                
                trigger = self.trig_combo.currentIndex()
                    
                for i,key in enumerate(self.data):
                    if trigger >= 0 and len(self.plots) > trigger+1 and i == trigger:
                        mousePointY = self.plots[trigger+1].mapSceneToView(pos)
                        rangeX = (0,len(self.data[key][1]))
                        rangeY = self.plots[trigger+1].viewRange()[1]
                        if ( mousePointY.y() > rangeY[0]+rangeY[0]*0.1 and 
                            mousePointY.y() < rangeY[1]-rangeY[0]*0.1 and
                            mousePointY.x() > rangeX[0] and 
                            mousePointY.x() < rangeX[1] ):
                            self.hLine.setPos(mousePointY.y())
                        else:
                            self.hLine.setPos(min(self.data[key][1]))    
                    
                    num = int(mousePoint.x())
                    if num >= 0 and num < len(self.data[key][1]):
                        text += "%d:%.1f\n"%(i,self.data[key][1][num])
                        self.vLine.setPos(mousePoint.x())
                if text != "":
                    self.value_label.setText(text)     
                    
        elif ( event.type() == QEvent.MouseButtonDblClick and 
                source is self.graphWidget.viewport() ):
            self.trig_edit.setText(str(self.hLine.value()))
            self.tLine.setPos(self.hLine.value())

        elif ( event.type() == QEvent.MouseButtonRelease and 
                source is self.graphWidget.viewport() ):
            index = 0
            if len(self.plots) > 1:
                for r in range(self.watched_list.rowCount()):    
                    if self.watched_list.item(r,0).checkState():
                        view = self.plots[index+1]
                        self.watched_list.setItem(r,7,QTableWidgetItem(str(view.viewRange()[1][0])))
                        self.watched_list.setItem(r,8,QTableWidgetItem(str(view.viewRange()[1][1])))
                        index +=1
            
        elif ( event.type() == QEvent.Wheel and 
                source is self.graphWidget.viewport() ):
            self.graphWidget.wheelEvent(event)
            index = 0
            for r in range(self.watched_list.rowCount()):    
                if self.watched_list.item(r,0).checkState():
                    view = self.plots[index+1]
                    self.watched_list.setItem(r,7,QTableWidgetItem(str(view.viewRange()[1][0])))
                    self.watched_list.setItem(r,8,QTableWidgetItem(str(view.viewRange()[1][1])))
                    index +=1
            return True
            
        return QWidget.eventFilter(self, source, event)

    def plot_update_data(self):
        if not self.trig_edit.visibleRegion().isEmpty():
            #Check (Check,0,0)
            data = osc.send_packet(self.control,osc.OSC_CHECK,0,0)
            
            if not data:
                return
            
            answer = int(data[:-1])
            
            if answer  == osc.SAMPLE_COMPLETE:
                self.osc_status.setText(_("Complete"))
                data = osc.send_packet(self.control,osc.OSC_GET,0,0)
                if self.shot_mode:
                    self.on_oscstop_clicked()
                else:
                    self.on_oscrun_clicked()
            elif answer  == osc.SAMPLE_RUN:
                self.osc_status.setText(_("Reading"))
                return
            elif answer  == osc.SAMPLE_IDLE:
                self.osc_status.setText(_("Idle"))
                return
            elif answer in (osc.SAMPLE_CHANGE,osc.SAMPLE_HIGH,osc.SAMPLE_LOW):
                self.osc_status.setText(_("Waiting"))
                return
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

            data = data.split('\n')
            samples = 0
            thread = 0

            if "Samples" in data[0]:
                s = data[0].split(' ')
                samples = int(s[1])
                thread = int(s[3])

            data = data[1:]
            
            for i,d in enumerate(data):
                s = d.split(' ')
                if len(s) == 2:
                    channel = s[0]
                    value = s[1]
                else:
                    continue
                l = len(self.data[watchedlist[int(channel)]][0])
                self.data[watchedlist[int(channel)]][0].append( l )
                self.data[watchedlist[int(channel)]][1].append( float( value ) ) 
                
            self.info_label.setText("S:{} T:{:.2f}ms".format(samples/len(watchedlist),   
                                                            (thread/1000000)*self.div_edit.value() ) )                  
            index_x = []
            label_x = []
            for i,l in enumerate( self.data[ watchedlist[0] ][0] ):
                index_x.append(i)
                label_x.append(l*thread/1000000 )
            label = list( zip( index_x, label_x ) )
            ticks = [ label[::100], label ]
            self.axis_x.setTicks(ticks)

            osc_list = [(self.watched_list.item(r,7),self.watched_list.item(r,8)) \
                        for r in range(self.watched_list.rowCount()) \
                            if self.watched_list.item(r,0).checkState()]

            for i,key in enumerate(self.data):
                axis = pyqtgraph.AxisItem('right')
                axis.tickFont = QFont("Helvetica",pointSize = 13,weight = 1,
                                            italic = False)
                       
                view = pyqtgraph.ViewBox()
                self.plots[0].layout.addItem(axis,2, i+3)
                self.plots[0].scene().addItem(view)
                axis.linkToView(view)
                
                if osc_list[i][0] and osc_list[i][1]:
                    min = float(osc_list[i][0].text())
                    max = float(osc_list[i][1].text())
                    view.setRange(yRange=(min,max),padding=0)
                                
                view.setXLink(self.plots[0])
                self.plots.append(view)
                axis.setLabel(key,**{'color': color[i], 'font-size': '16pt'})
                pen = pyqtgraph.mkPen(QColor(color[i]), width=2, 
                                        style=lineStyle[i])
                curve = pyqtgraph.PlotCurveItem(self.data[key][1], pen=pen)
                view.addItem(curve)        
                
                trigger = self.trig_combo.currentIndex()
                if trigger >= 0 and trigger == i:
                    self.plots[i+1].addItem(self.hLine)
                    self.plots[i+1].addItem(self.tLine)
                    
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
                watchlist.append( [ self.watched_list.item(r,4).text(),
                    self.watched_list.item(r,5).text(),
                    self.watched_list.item(r,1).text(),
                    self.watched_list.item(r,6).text() ] )

        if not watchlist:
            return 
            
        self.trig_combo.clear()
        model = self.trig_combo.model()
        
        for i,key in enumerate(watchlist):
            #Set (Channel, NChannel*10+ChannelType, Pin offset)
            osc.send_packet(self.control,osc.OSC_CHANNEL,i*10+int(key[3]),int(key[0],16))
            item = QStandardItem(key[2])
            item.setData(int(key[3]), role=Qt.UserRole + 1)
            item.setData(int(key[0],16), role=Qt.UserRole + 2)
            model.appendRow(item)

        self.trig_combo.setCurrentIndex(-1)
        
        #Clear data old data
        osc.send_packet(self.control,osc.OSC_CHANNEL,(i+1)*10,0)
           
        self.plot_update_data()

    def on_update_clicked(self):
        self.load_data()
            
    def find_item(self,pin,parent):
        if '.' in pin:
            items = pin.split('.')
            childs = parent.findItems(items[len(items)-1],Qt.MatchExactly | Qt.MatchRecursive)
            for child in childs:
                path = ""
                item = child
                while item is not None:
                    path = str(item.text(0)) + '.' + path
                    item = item.parent()
                
                if pin in path:
                    return child
        else:
            childs = parent.findItems(pin,Qt.MatchExactly)
            if len(childs)>0:
                return child[0]

    @pyqtSlot(str)
    def item_answer_set_text(self,data):
        self.item_answer.setText("#:"+data[:-1])

    def on_change_clicked(self):
        self.item_answer.setText("#:")
        self.thread = ReceiveThread([self.item_value.text()])
        self.thread.message.connect(self.item_answer_set_text)
        self.thread.start()
        
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
                htype = self.watched_list.item(r,6)
                if addr and pdir and htype:
                    data = osc.send_packet(self.control,osc.OSC_STATE,int(htype.text()),
                                            int(addr.text(),16))
                    if data:
                        data = data[:-1].replace(' ','')
                        value = self.watched_list.item(r,3)
                        if value:
                            value.setText(data)
                        else:
                            self.watched_list.setItem(r,3,QTableWidgetItem(data))

    def on_tree_doubleclick(self,item,column,row=0):
        if item.text(1):
            pin = item.text(0)
            pin_type = item.text(1)
            pin_dir = item.text(2)
            pin_addr = item.text(3)
            hal_type = item.text(4)
            while item.parent():
                item = item.parent()
                pin = item.text(0)+'.'+pin
            self.watched_list.insertRow(row)
            checkItem = QTableWidgetItem()
            checkItem.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkItem.setCheckState(Qt.Unchecked)  
            self.watched_list.setItem(row,0,checkItem)
            self.watched_list.setItem(row,1,QTableWidgetItem(pin))
            self.watched_list.setItem(row,2,QTableWidgetItem(pin_type))
            self.watched_list.setItem(row,3,QTableWidgetItem("..."))
            self.watched_list.setItem(row,4,QTableWidgetItem(pin_addr))
            self.watched_list.setItem(row,5,QTableWidgetItem(pin_dir))
            self.watched_list.setItem(row,6,QTableWidgetItem(hal_type))

    def load_data(self):
        self.tree.clear()
        
        try:
            data_pin = osc.send_packet(self.control,osc.OSC_LIST,osc.HAL_PIN,0)
            data_pin = data_pin.split('\n')
            
            if "CONTROL" in data_pin[0]:
                self.control = int(data_pin[0].split(' ')[1],16)
                data_pin = data_pin[1:]
            
            data_pin = filter(lambda a: len(a)==5,
                [[c for c in s.split(' ')+[str(osc.HAL_PIN)] if len(c)>0
                    ] for s in data_pin])
                
            data_param = osc.send_packet(self.control,
                                        osc.OSC_LIST,osc.HAL_PARAMETER,0)
            data_param = data_param.split('\n')

            if "CONTROL" in data_param[0]:
                self.control = int(data_param[0].split(' ')[1],16)
                data_param = data_param[1:]
                
            data_param = filter(lambda a: len(a)==5,
                [[c for c in s.split(' ')+[str(osc.HAL_PARAMETER)] if len(c)>0
                    ] for s in data_param])

            data = list(data_pin) + list(data_param)
        except Exception as e:
            printInfo(_("Failed to get hal pin list: {}",e))
            return
        if not data:
			data = [[' ',' ',' ',_("HAL Pin viewer works only with\n loaded hal component 'ascope'."),' '],]
        self.get_tree(data,self.tree)

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
                self.get_tree(map(lambda s: s[:3]+[s[3][len(cat)+1:]]+s[4:],
                              filter(lambda s: s[3].startswith(cat+".") and
                                '.' in s[3],pins)),child)
            else:
                child = QTreeWidgetItem(parent)
                child.setText(0,pin[3])
                child.setText(1,osc.get_type_text(pin[1]))
                child.setText(2,osc.get_dir_text(pin[2]))
                child.setText(3,pin[0])
                child.setText(4,pin[4])
