# -*- coding: utf-8 -*-
#
# AlterX GUI
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


############################
# **** IMPORT SECTION **** #
############################

from PyQt5 import QtCore, QtWidgets, QtGui, uic

from qtvcp.widgets.stylesheeteditor import StyleSheetEditor as SSE

#from qtvcp.widgets.origin_offsetview import OriginOffsetView as OFFVIEW_WIDGET
#from qtvcp.widgets.dialog_widget import CamViewDialog as CAMVIEW
#from qtvcp.widgets.dialog_widget import MacroTabDialog as LATHEMACRO
#from qtvcp.widgets.gcode_editor import GcodeEditor as GCODE
#from qtvcp.widgets.mdi_line import MDILine as MDI_WIDGET
#from qtvcp.widgets.overlay_widget import FocusOverlay
#from qtvcp.widgets.dialog_widget import LcncDialog

from qtvcp.core import Status, Info, Action

from qtvcp.lib.keybindings import Keylookup
from qtvcp.lib.aux_program_loader import Aux_program_loader
from qtvcp.lib.notify import Notify

#from qtvcp.lib.preferences import Access

# Set up logging
from qtvcp import logger
log = logger.getLogger(__name__)

from functools import partial

from menus import *
from tabs import *

import logging
import linuxcnc
import sys
import os
import logging
import ConfigParser

###########################################
# **** instantiate libraries section **** #
###########################################

KEYBIND = Keylookup()
STATUS = Status()
AUX_PRGM = Aux_program_loader()
NOTE = Notify()
INFO = Info()

#MSG = LcncDialog()
#PREFS = Access()
ACTION = Action()

###################################
# **** HANDLER CLASS SECTION **** #
###################################

class QtHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        record = self.format(record)
        if record: LogStream.stdout().write('%s\n'%record)

class LogStream(QtCore.QObject):
    _stdout = None
    _stderr = None
    messageWritten = QtCore.pyqtSignal(str)

    def flush( self ):
        pass

    def fileno( self ):
        return -1

    def write( self, msg ):
        if ( not self.signalsBlocked() ):
            self.messageWritten.emit(unicode(msg))

    @staticmethod
    def stdout():
        if ( not LogStream._stdout ):
            LogStream._stdout = LogStream()
            sys.stdout = LogStream._stdout
        return LogStream._stdout

    @staticmethod
    def stderr():
        if ( not LogStream._stderr ):
            LogStream._stderr = LogStream()
            sys.stderr = LogStream._stderr
        return LogStream._stderr

class HandlerClass:
    ##################################
    # **** GLOBALS HandlerClass **** #
    ##################################  

    desktop_notify = True

    display_units_mm = 0
    linear_units = ( "mm" )
    angular_units = ( "deg" )
    feed_units = linear_units + "/rev"
    fpm_mode = True

    diameter = 0

    requested_feedrate = 0
    requested_spindlerate = 0
    last_spindlerate = 0
    last_feedrate = 0

    start_line = 0
    last_line = 0
    program_length = 0

    tool_change = False

    status_update = []

    show_cursor = False

    ########################
    # **** INITIALIZE **** #
    ########################
    # widgets allows access to  widgets from the qtvcp files
    # at this point the widgets and hal pins are not instantiated
    def __init__(self, halcomp,widgets,paths):
        self.const = self.CONST()
        self.hal = halcomp
        self.widgets = widgets
        self.stat = linuxcnc.stat()
        self.command = linuxcnc.command()
        self.error = linuxcnc.error_channel()
        self.PATH = paths.CONFIGPATH
        self.IMAGE_PATH = paths.IMAGEDIR
        self.STYLE = SSE(widgets, paths)
        self.dialogs = self.dialog_model()
        self.jog = self.JOG_pref()
       
        inipath = os.environ["INI_FILE_NAME"]
        self.inifile = linuxcnc.ini(inipath)
        if not self.inifile:
            log.error( "Error, no INI File given" )
            sys.exit()

        self.prefs = self.preferences( self.inifile.find("DISPLAY", "PREFERENCE_FILE_PATH"))
        
        handler = QtHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        tlog = logging.getLogger(logger.BASE_LOGGER_NAME)
        tlog.addHandler(handler)

        STATUS.forced_update()

        # Give notify library a reference to the statusbar
        KEYBIND.add_call('Key_F11','on_keycall_F11')
        KEYBIND.add_call('Key_F12','on_keycall_F12')

        STATUS.connect("state-estop",lambda w: self.update_status('ESTOP'))
        STATUS.connect("state-estop-reset",lambda w: self.update_status('ESTOP_RESET'))

        STATUS.connect("state-on",lambda w: self.update_status('MACHINE_ON'))
        STATUS.connect("state-off",lambda w: self.update_status('MACHINE_OFF'))

        STATUS.connect("interp-paused",lambda w: self.update_status('Paused'))
        STATUS.connect("interp-run",lambda w: self.update_status('Run'))
        STATUS.connect("interp-idle",lambda w: self.update_status('Idle'))
        STATUS.connect("interp-reading",lambda w: self.update_status('Reading'))
        STATUS.connect("interp-waiting",lambda w: self.update_status('Waiting'))

        STATUS.connect("mode-manual",lambda w: self.update_status('Manual'))
        STATUS.connect("mode-mdi",lambda w: self.update_status('MDI'))
        STATUS.connect("mode-auto",lambda w: self.update_status('Auto'))

        STATUS.connect("all-homed",lambda w: self.update_status('all_homed'))
        STATUS.connect("not-all-homed",lambda w,t: self.update_status('not_all_homed'))

        STATUS.connect('error', self.error_message)
        STATUS.connect('periodic', self.periodic)

        STATUS.connect('current-position', self.update_position)
        STATUS.connect('metric-mode-changed', self.switch_units)
        STATUS.connect('diameter-mode', lambda w,t: self.switch_modes('diameter_mode',t))

        STATUS.connect('file-loaded', self.program_loaded)
        STATUS.connect('line-changed', self.program_progress)

        STATUS.connect('mdi-history-changed', self.update_requested_rate_MDI)

        STATUS.connect('current-feed-rate', lambda w,t: self.update_actual_rate('feed',t))
        STATUS.connect('feed-override-changed', self.update_feed_override)
        STATUS.connect('rapid-override-changed', self.update_rapid_override)

        STATUS.connect('actual-spindle-speed-changed', lambda w,t: self.update_actual_rate('spindle',t))
        STATUS.connect('requested-spindle-speed-changed', self.update_spindle_requested)
        STATUS.connect('spindle-override-changed', self.update_spindle_override)

        STATUS.connect('itime-mode', lambda w,t: self.switch_modes('inverse_time_mode',t))
        STATUS.connect('fpm-mode', lambda w,t: self.switch_modes('feed_per_minute_mode',t))
        STATUS.connect('fpr-mode', lambda w,t: self.switch_modes('feed_per_revolution_mode',t))
        STATUS.connect('css-mode', lambda w,t: self.switch_modes('constant_surface_feed_mode',t))
        STATUS.connect('rpm-mode', lambda w,t: self.switch_modes('constatnt_RPM_mode',t))
        
        STATUS.connect('jograte-changed', self.update_jog_linear)
        STATUS.connect('jograte-angular-changed', self.update_jog_angular)
        STATUS.connect('jogincrement-changed', self.update_jog_linear_increment)
        STATUS.connect('jogincrement-angular-changed', self.update_jog_angular_increment)

        STATUS.connect('m-code-changed', self.update_m_codes)
        STATUS.connect('g-code-changed', self.update_g_codes)


    ##########################################
    # Special Functions called from QTSCREEN #
    ##########################################

    # at this point:
    # the widgets are instantiated.
    # the HAL pins are built but HAL is not set ready

    def initialized__(self):
        #Generate buttons
        layouts = ["manual","MDI","auto","settings","tabs","display","equipment","load","edit","homing","offset","tools"]

        for l in layouts:
            layout = QtWidgets.QHBoxLayout()
            layout.setContentsMargins(1,1,1,1)
            layout.setSpacing(1)
            stack = QtWidgets.QWidget()
            stack.setLayout(layout)
            index = self.widgets.bottomWidgets.addWidget(stack)

            if "menus.%s"%l in sys.modules.keys():
                i = 0
                if l == "MDI" and self.const.useMacro:
                    btn = QtWidgets.QPushButton("BTN_%s%d"%(l,i))
                    btn.setObjectName("BTN_%s%d"%(l,i))
                    btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
                    btn.clicked.connect(self.macro_stop_clicked)

                    dir_path = os.path.dirname(os.path.realpath(__file__))
                    if os.path.isfile("%s/images/macro_stop.png"%dir_path):
                        btn.setStyleSheet("image:url('%s/images/macro_stop.png')"%dir_path)
                    else:
                        btn.setStyleSheet("color:black")

                    layout.addWidget(btn)
                    layout.setStretch(i,1)
                    i = i + 1

                    for macro in self.inifile.findall("MACROS", "MACRO"):
                        btn = QtWidgets.QPushButton("BTN_%s%d"%(l,i))
                        btn.setObjectName("MACRO_%s%d"%(l,i))
                        btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
                        btn.clicked.connect(partial(self.macro_button_clicked,macro))
                        btn.setStyleSheet("color:black")
                        btn.setText(macro.split()[0][0:10])
                        layout.addWidget(btn)
                        layout.setStretch(i,1)
                        if i < self.const.numButtons:    
                            i = i + 1
                        else:
                            break
                else:
                    for menu in self.inifile.findall("MENUS", l.upper()):
                        b = self.button_model(index,l,i,menu,self)
                        layout.addWidget(b.btn)
                        layout.setStretch(i,1)
                        if i < self.const.numButtons:    
                            i = i + 1
                        else:
                            break

                for i in range(i,self.const.numButtons):
                    b = self.button_model(index,l,i)
                    layout.addWidget(b.btn)
                    layout.setStretch(i,1)
                   
        #Load user tabs
        self.user_tabs=[]
        for tab_name in self.inifile.findall("USER_TABS", "TAB"):
            try:
                tab = getattr(globals()[tab_name],"module").func()
                self.widgets.tabUser.addTab(tab, tab_name)

                #if tab.hwid:
                #    ext_win = QtGui.QWindow.fromWinId(int(tab.hwid))
                #    widget = QtWidgets.QWidget.createWindowContainer(ext_win)
                #    widget.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.ForeignWindow)
                #    self.widgets.tabUser.addTab(widget, tab_name)
                #    self.user_tabs.append(tab)

            except Exception as e:
                log.debug('Exception loading tabs:', exc_info=e)
 
        #Disable right menu
        widgetlist = ["manual_tbtn","mdi_tbtn","auto_tbtn","settings_tbtn","tabs_tbtn","machine_tbtn"]
        self._sensitize_widgets( widgetlist, False )

        #Disable left menu
        widgetlist = ["abort_tbtn","equipment_tbtn","load_tbtn","homing_tbtn","offset_tbtn","tools_tbtn"]
        self._sensitize_widgets( widgetlist, False )

        self.widgets.filemanager.default_path = os.path.abspath(self.inifile.find("DISPLAY","PROGRAM_PREFIX"))
        self.widgets.filemanager.updateDirectoryView(self.widgets.filemanager.default_path)

        log.info( 'LinuxCNC path: %s'%self.widgets.filemanager.default_path )
    
        self.command.state( linuxcnc.STATE_ESTOP_RESET )
        self.command.wait_complete()
        self.stat.poll()

        self.widgets.stackedWidget.setCurrentIndex(0)
        self.widgets.bottomWidgets.setCurrentIndex(0)
        
        LogStream.stdout().messageWritten.connect( self.widgets.consoleLog.insertPlainText )
        LogStream.stderr().messageWritten.connect( self.widgets.consoleLog.insertPlainText )

        self.axislist = self.inifile.find("TRAJ", "COORDINATES").split(' ')

        self.jog.jog_linear=self.inifile.find("DISPLAY", "DEFAULT_LINEAR_VELOCITY")
        self.jog.jog_angular=self.inifile.find("DISPLAY", "DEFAULT_ANGULAR_VELOCITY")

        try:
            self.xterm = self.terminal()
            self.widgets.tabSettings.addTab(self.xterm, "Terminal")
        except Exception as e:
            log.debug('Exception loading terminal tab:', exc_info=e)

        self.widgets.tooloffsetview.hideColumn(0)

        for a in self.axislist:
            i = self.axislist.index(a)
            self.widgets["axis_label_%d"%i].setText(a)
            
        for i in range(len(self.axislist),4):
            self.widgets["axis_label_%d"%i].setVisible(False)
            self.widgets["drolabel_main_%d"%i].setVisible(False)
            self.widgets["drolabel_sec_%d"%i].setVisible(False)
            self.widgets["drolabel_dtg_%d"%i].setVisible(False)

        open_file = self.inifile.find("DISPLAY", "OPEN_FILE")
        if open_file != None and open_file != "" and os.path.isfile(open_file):
            ACTION.OPEN_PROGRAM(open_file)
            self.program_loaded(None,open_file)
            self.widgets.labelProgramFilename.setText(os.path.basename(open_file))

        self.hide_cursor=self.inifile.find("DISPLAY", "HIDE_CURSOR")

        if self.hide_cursor:
            QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
        else:
            QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

        QtWidgets.qApp.processEvents()


    def processed_key_event__(self,receiver,event,is_pressed,key,code,shift,cntrl):
        # when typing in MDI, we don't want keybinding to call functions
        # so we catch and process the events directly.
        # We do want ESC, F1 and F2 to call keybinding functions though
        if code not in(QtCore.Qt.Key_F11,QtCore.Qt.Key_F12,QtCore.Qt.Key_F1,QtCore.Qt.Key_F2,):
            if isinstance(receiver, OFFVIEW_WIDGET) or isinstance(receiver, MDI_WIDGET):
                if is_pressed:
                    receiver.keyPressEvent(event)
                    event.accept()
                return True
            if isinstance(receiver,QtWidgets.QDialog):
                print 'dialog'
                return True
        try:
            KEYBIND.call(self,event,is_pressed,shift,cntrl)
            return True
        except Exception as e:
            #log.debug('Exception loading Macros:', exc_info=e)
            print 'Error in, or no function for: %s in handler file for-%s'%(KEYBIND.convert(event),key)
            if e:
                print e
            #print 'from %s'% receiver
            return False

    #########################
    # callbacks from STATUS #
    #########################

    def update_m_codes(self,widget,codes):
        self.widgets.labelCodesM.setText(codes)

    def update_g_codes(self,widget,codes):
        self.widgets.labelCodesG.setText(codes)

    def update_jog_linear(self,widget,rate):
        self.widgets.labelJOG_linear.setText("Linear speed:%10.3f %s"%(rate,self.feed_units))

    def update_jog_angular(self,widget,rate):
        self.widgets.labelJOG_angular.setText("Angular speed:%10.3f %s/min"%(rate,self.angular_units))

    def update_jog_linear_increment(self,widget,data,rate):
        self.widgets.labelJOG_linear_increment.setText("Linear step:%10.3f %s"%(data,self.linear_units))

    def update_jog_angular_increment(self,widget,data,rate):
        self.widgets.labelJOG_angular_increment.setText("Angular step:%10.3f %s"%(data,self.angular_units))

    def update_requested_rate_MDI(self,widget):
        self.stat.poll()

        if self.requested_spindlerate != self.stat.settings[2]:
            self.update_spindle_requested(None,None)
            self.requested_spindlerate = self.stat.settings[2]

        if self.stat.task_mode==linuxcnc.MODE_MDI and self.requested_feedrate != self.stat.settings[1]:
            self.requested_feedrate = self.stat.settings[1]

            self.widgets.labelFeedRequested.setText("F%d"%self.stat.settings[1])
            self.widgets.labelFeedOverride.setText("FO:%10.3f %s"%(self.stat.feedrate*self.stat.settings[1],self.feed_units))

    def update_actual_rate(self,widget,rate):
        if widget == 'feed':
            self.last_feedrate = rate
        elif widget == 'spindle':
            self.last_spindlerate = rate

        self.widgets.labelFeedActual.setText("FPM: %10.3f %s/min \nFPR: %10.3f %s/rev"%(self.last_feedrate,self.linear_units,self.last_feedrate/self.last_spindlerate if self.last_spindlerate != 0 else 0, self.linear_units))
        
        self.widgets.labelSpindleActual.setText("RPM: %10.3f rpm"%(self.last_spindlerate))
 
    def update_feed_override(self,widget,feedrate):
        self.widgets.labelFeedOverride.setText("FO:%10.3f %s"%(self.stat.feedrate*self.requested_feedrate,self.feed_units))

    def update_rapid_override(self,widget,rapidrate):
        self.widgets.labelRapidOverride.setText("RO:%10.3f %s"%(self.stat.rapidrate*self.stat.max_velocity,self.feed_units))

    def update_spindle_requested(self,widget,spindlerate):
        self.stat.poll()

        self.widgets.labelSpindleRequested.setText("S%d"%self.stat.settings[2])

        self.widgets.labelSpindleOverride.setText("SO:%10.3f rpm"%(self.stat.spindle[0]['override']*self.stat.settings[2]))
 
    def update_spindle_override(self,widget,spindlerate):
        self.stat.poll()

        self.widgets.labelSpindleOverride.setText("SO:%10.3f rpm"%(self.stat.spindle[0]['override']*self.stat.settings[2]))

    def program_loaded(self,widget,program):
        if program:
            fileobject = file( program, 'r' )
            lines = fileobject.readlines()
            fileobject.close()
            self.program_length = len( lines )

            self.widgets.labelProgramLen.setText("Lines: %d"%self.program_length)
            self.widgets.labelProgramEnd.setText("Progress: %3.2f%%"%(0))
            self.widgets.labelProgramFilename.setText(os.path.basename(program))
        else:
            self.program_length = 0

            self.widgets.labelProgramLen.setText("")
            self.widgets.labelProgramEnd.setText("")
            self.widgets.labelProgramFilename.setText("")
       
    def program_progress(self,widget,line):
        if self.program_length > 0:
            for l in range(self.last_line,line):
                cmd = self.widgets.gcode_editor.editor.text(l)
                for word in cmd.split(' '):
                    if 'F' in word or 'f' in word:
                        for r in ('\n','\r','F','f'):
                            word = word.replace(r,'')

                        try:
                            self.requested_feedrate = float(word)

                            self.widgets.labelFeedRequested.setText("F%d"%self.requested_feedrate)
                            self.widgets.labelFeedOverride.setText("FO:%10.3f %s"%(self.stat.feedrate*self.requested_feedrate,self.feed_units))
                        except:
                            print "Can't convert F-cmd to number"

            self.widgets.labelProgramEnd.setText("Progress: %3.2f%%"%(100.000*line / self.program_length))
        else:
            self.widgets.labelProgramEnd.setText("")

        self.last_line = line

    def error_message(self, widget, message):
        log.error( 'LinuxCNC error: %s'%message )
        NOTE.notify('Error',message,QtWidgets.QMessageBox.Information,4)
    
    def get_stat(self, table, stat,row_pos,level):
        for value in stat:
            text=""
            last_row = table.rowCount()
            if last_row < row_pos + 1:
                table.insertRow(last_row)
                table.setItem(last_row , level, QtWidgets.QTableWidgetItem(str(value[0])))
                self.status_update.append(20)

            if isinstance(value[1], tuple):
                row_pos = self.get_stat(table,[[value[0]+"_"+str(i),t] for i,t in enumerate(value[1])],row_pos+1,level+1)
            elif isinstance(value[1], dict):
                row_pos = self.get_stat(table,value[1].items(),row_pos+1,level+1)
            else:
                if isinstance(value[1], str):
                    text = "%s"%(value[1])
                elif isinstance(value[1], int):
                    text = "%d"%(value[1])
                elif isinstance(value[1], float):
                    text = "%10.3f"%(value[1])
                else:    
                    text = "%s"%(value[1],)
                
                if not table.item(row_pos, 1+level ) or table.item(row_pos,1+level).text() != text:
                    table.setItem(row_pos, 1+level, QtWidgets.QTableWidgetItem(text))
                    self.status_update[row_pos] = 20
                elif self.status_update[row_pos] > 0:
                    self.status_update[row_pos] = self.status_update[row_pos] - 1

                if self.status_update[row_pos] > 0:
                    table.item(row_pos, 1 +level).setBackground(QtGui.QColor(150,100,100))
                else:
                    table.item(row_pos, 1 +level).setBackground(QtGui.QColor(255,255,255))

                row_pos = row_pos + 1

        return row_pos


    def periodic(self,widget):
        if self.widgets.stackedWidget.currentIndex()==3:
            self.stat.poll()
            self.widgets.tableWidget_Status.setColumnCount(4)

            stat = []
            for x in dir(self.stat):
                if not x.startswith('_'):
                    attr = getattr(self.stat,x)
                    if callable(attr):
                        continue
                    stat.append([x,attr])
                
            self.get_stat(self.widgets.tableWidget_Status,stat,0,0)
            for i in range(4):
                self.widgets.tableWidget_Status.setColumnWidth(i,self.widgets.tableWidget_Status.size().width()*0.23)
            self.widgets.tableWidget_Status.resizeRowsToContents()

        try:
            e = self.error.poll()
            if e:
                kind, text = e
                if kind in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
                    if self.desktop_notify:
                        NOTE.notify('ERROR',text,None,4,self.const.alertTime)
                        log.error( 'LinuxCNC error: %s'%text )
                elif kind in (linuxcnc.NML_TEXT, linuxcnc.OPERATOR_TEXT):
                   if self.desktop_notify:
                        NOTE.notify('OP MESSAGE',text,None,4,self.const.alertTime)
                        log.info( 'LinuxCNC message: %s'%text )
                elif kind in (linuxcnc.NML_DISPLAY, linuxcnc.OPERATOR_DISPLAY):
                   if self.desktop_notify:
                        NOTE.notify('DISPLAY',text,None,4,self.const.alertTime)
                        log.info( 'LinuxCNC display: %s'%text )
        except:
            print "Catch error while catching error"

    def switch_modes(self, mode,status):
        if mode == 'diameter_mode':
            self.diameter = status

        elif mode == 'inverse_time_mode':
            self.widgets.labelFeedOverride.setVisible(not status)
            self.widgets.labelRapidOverride.setVisible(not status)

        elif mode == 'feed_per_minute_mode':
            if status:
                self.feed_units = self.linear_units + "/min"
                self.fpm_mode = True

        elif mode == 'feed_per_revolution_mode':
            if status:
                self.feed_units = self.linear_units + "/rev"
                self.fpm_mode = False

        elif mode == 'constant_surface_feed_mode':
            self.widgets.labelSpindleOverride.setVisible(not status)

        elif mode == 'constatnt_RPM_mode':
            pass

        self.update_feed_override(None,None)
        self.update_rapid_override(None,None)
        self.update_jog_linear(None,self.jog.jog_linear)
        self.update_jog_linear_increment(None,self.jog.jog_step,None)

    def switch_units(self, widget, data):
        self.display_units_mm = data

        if self.display_units_mm != INFO.MACHINE_IS_METRIC:
            self.linear_units = ( "inch" )
        else:
            self.linear_units = ( "mm" )

        if self.fpm_mode:
            self.feed_units = self.linear_units + "/min"
        else:
            self.feed_units = self.linear_units + "/rev"

        self.update_feed_override(None,None)
        self.update_rapid_override(None,None)
        self.update_jog_linear(None,self.jog.jog_linear)
        self.update_jog_linear_increment(None,self.jog.jog_step,None)


    def update_position(self, widget, absolute, relative, dtg, joint):
        if self.display_units_mm != INFO.MACHINE_IS_METRIC:
            absolute = INFO.convert_units_9(absolute)
            relative = INFO.convert_units_9(relative)
            dtg = INFO.convert_units_9(dtg)

        self.widgets.sdrolabel_auto.setText("")

        tmpl = lambda s: "%10.3f" % s
        for a in self.axislist:
            i = "XYZABCUVW".index(a)
            d = self.axislist.index(a)

            #log.info( 'Status %10.3f %10.3f %10.3f %10.3f'%(absolute[i],relative[i],dtg[i],joint[i]) )
            if self.diameter and a=='X':
                scale=2.0
            else:
                scale=1.0

            self.widgets.sdrolabel_auto.setText(self.widgets.sdrolabel_auto.text() + ("\r\n" if d != 0 else "") + "%s: %10.3f"%(a,absolute[i]*scale))

            self.widgets["drolabel_main_%d"%d].setText(tmpl(absolute[i]*scale))
            self.widgets["drolabel_sec_%d"%d].setText(tmpl(relative[i]*scale))
            self.widgets["drolabel_dtg_%d"%d].setText(tmpl(dtg[i]*scale))
     

    def update_status(self,status,msg=None):
        if status == 'ESTOP':
            log.info( 'Status changed to ESTOP' )

            self.widgets.machine_tbtn.setChecked(False)

            widgetlist = ["manual_tbtn","mdi_tbtn","auto_tbtn","settings_tbtn","tabs_tbtn","machine_tbtn"]
            self._sensitize_widgets( widgetlist, False )

            widgetlist = ["abort_tbtn","equipment_tbtn","load_tbtn","homing_tbtn","offset_tbtn","tools_tbtn"]
            self._sensitize_widgets( widgetlist, False )

        elif status == 'ESTOP_RESET':
            log.info( 'Status changed to ESTOP_RESET' )

            widgetlist = ["settings_tbtn","tabs_tbtn","machine_tbtn"]
            self._sensitize_widgets( widgetlist, True )

            widgetlist = ["abort_tbtn"]
            self._sensitize_widgets( widgetlist, True )

        elif status == 'MACHINE_ON':
            log.info( 'Status changed to  MACHINE_ON' )

            self.widgets.machine_tbtn.setChecked(True)
            
            widgetlist = ["manual_tbtn","settings_tbtn","tabs_tbtn","machine_tbtn","abort_tbtn","equipment_tbtn"]

            if STATUS.is_all_homed():
                widgetlist.append("mdi_tbtn")
                widgetlist.append("auto_tbtn")
            self._sensitize_widgets( widgetlist, True )

        elif status == 'MACHINE_OFF':
            log.info( 'Status changed to  MACHINE_OFF' )

            self.widgets.machine_tbtn.setChecked(False)

            self.widgets.stackedWidget.setCurrentIndex(0)
            self.widgets.bottomWidgets.setCurrentIndex(0)

            self.command.mode(linuxcnc.MODE_MANUAL)
            self.command.wait_complete()
            self.stat.poll()

            self.jog.jog_activate = 0

            widgetlist = ["manual_tbtn","mdi_tbtn","auto_tbtn"]
            self._sensitize_widgets( widgetlist, False )

            widgetlist = ["load_tbtn","homing_tbtn","offset_tbtn","tools_tbtn","equipment_tbtn"]
            self._sensitize_widgets( widgetlist, False )

        elif status == 'Paused':
            log.info( 'Interp state PAUSE' )
            self.stat.poll()

        elif status == 'Run':
            log.info( 'Interp state RUN' )

            if self.stat.task_mode!=linuxcnc.MODE_MANUAL:
                widgetlist = ["manual_tbtn","mdi_tbtn","auto_tbtn"]
                self._sensitize_widgets( widgetlist, False )

            self.stat.poll()

        elif status == 'Reading':
            log.info( 'Interp state Reading' )
            self.stat.poll()

        elif status == 'Waiting':
            log.info( 'Interp state Waiting' )
            self.stat.poll()
            
        elif status == 'Idle':
            log.info( 'Interp state IDLE' )

            if STATUS.is_all_homed():
                widgetlist = ["manual_tbtn","mdi_tbtn","auto_tbtn"]
                self._sensitize_widgets( widgetlist, True )

            self.widgets.labelFeedRequested.setText("F0")
            self.widgets.labelFeedOverride.setText("FO:%10.3f %s"%(0,self.feed_units))
            self.stat.poll()
        
        elif status == 'Manual':
            log.info( 'Mode Manual enabled' )

            self.widgets.manual_tbtn.setChecked(True)

            self.widgets.stackedWidget.setCurrentIndex(0)
            self.widgets.bottomWidgets.setCurrentIndex(0)

            widgetlist = ["load_tbtn","offset_tbtn","tools_tbtn"]
            self._sensitize_widgets( widgetlist, False )

            widgetlist = ["homing_tbtn"]
            self._sensitize_widgets( widgetlist, True )

        elif status == 'MDI':
            log.info( 'Mode MDI enabled' )

            self.widgets.mdi_tbtn.setChecked(True)

            self.widgets.stackedWidget.setCurrentIndex(1)
            self.widgets.bottomWidgets.setCurrentIndex(1)

            widgetlist = ["load_tbtn","homing_tbtn"]
            self._sensitize_widgets( widgetlist, False )

            widgetlist = ["offset_tbtn","tools_tbtn"]
            self._sensitize_widgets( widgetlist, True )

            self.widgets.mdihistory.MDILine.setFocus()

        elif status == 'Auto':
            log.info( 'Mode Auto enabled' )

            self.widgets.auto_tbtn.setChecked(True)

            self.widgets.stackedWidget.setCurrentIndex(2)
            self.widgets.bottomWidgets.setCurrentIndex(2)

            widgetlist = ["offset_tbtn","tools_tbtn","homing_tbtn"]
            self._sensitize_widgets( widgetlist, False )

            widgetlist = ["load_tbtn"]
            self._sensitize_widgets( widgetlist, True )

        elif status == 'all_homed':
            log.info( 'All axis homed' )

            widgetlist = ["auto_tbtn","mdi_tbtn"]
            self._sensitize_widgets( widgetlist, True )

        elif status == 'not_all_homed':
            log.info( 'Not all axis homed' )

            widgetlist = ["auto_tbtn","mdi_tbtn"]
            self._sensitize_widgets( widgetlist, False )


    #######################
    # callbacks from form #
    #######################

    def page_settings_changed(self,page):
        log.info("Page settings changed to %d"%(page))
        if page == 0:
            self.widgets.consoleLog.setFocus()
        elif page == 1:
            self.widgets.tableWidget_Status.setFocus()            

    def page_changed(self,page):
        log.info("Page changed to %d"%(page))
        if page == 0:
            groupBoxes_hide = ['groupBox_Axis','groupBox_Feedrate','groupBox_Codes','groupBox_Program']
            groupBoxes_show = ['groupBox_JOG','groupBox_Spindlerate','groupBox_Tool']
            self.widgets.horizontalLayout_GB.show()
        elif page == 1:
            groupBoxes_hide = ['groupBox_JOG','groupBox_Program']
            groupBoxes_show = ['groupBox_Axis','groupBox_Feedrate','groupBox_Spindlerate','groupBox_Codes','groupBox_Tool']
            self.widgets.horizontalLayout_GB.show()
        elif page == 2:
            groupBoxes_hide = ['groupBox_JOG']
            groupBoxes_show = ['groupBox_Axis','groupBox_Feedrate','groupBox_Spindlerate','groupBox_Codes','groupBox_Program','groupBox_Tool']
            self.widgets.horizontalLayout_GB.show()
        elif page in [6,9]:
            groupBoxes_hide = []
            groupBoxes_show = []
        else:
            groupBoxes_hide = ['groupBox_Axis','groupBox_JOG','groupBox_Feedrate','groupBox_Spindlerate','groupBox_Codes','groupBox_Program','groupBox_Tool']
            groupBoxes_show = []
            self.widgets.horizontalLayout_GB.hide()

        for gb in groupBoxes_hide:
            try:
                self.widgets[gb].setVisible( False )
            except Exception, e:
                log.error("No widget named: %s to set unvisible"%(gb))

        for gb in groupBoxes_show:
            try:
                self.widgets[gb].setVisible( True )
            except Exception, e:
                log.error("No widget named: %s to set visible"%(gb))

        widgetlist = [("settings_tbtn",3),("tabs_tbtn",4),("abort_tbtn",5),("equipment_tbtn",6),("load_tbtn",7),("homing_tbtn",9),("offset_tbtn",10),("tools_tbtn",11)]

        for name in widgetlist:
            try:
                if page == name[1]:
                    self.widgets[name[0]].setChecked( True )
                else:
                    self.widgets[name[0]].setChecked( False )
    
            except Exception, e:
                log.error("No widget named: %s to set checked"%(name))

    def macro_stop_clicked(self):
        log.info("Button macro stop clicked")
        self.command.abort()        

    def macro_button_clicked(self, macro):
        o_codes = macro.split()
        subroutines_path = self.inifile.find("RS274NGC", "SUBROUTINE_PATH")
        if not subroutines_path:
            msg = "No subroutine folder or program prefix is given in the ini file"
            log.error(msg)
            NOTE.notify('ERROR',msg,None,10)
            return

        file = subroutines_path + "/" + o_codes[0] + ".ngc"
        if not os.path.isfile( file ):
            msg = "File %s of the macro could not be found" % file
            log.error(msg)
            NOTE.notify('ERROR',msg,None,10)
            return

        command = str( "O<" + o_codes[0] + "> call" )
        for code in o_codes[1:]:
            result = self.dialogs.getDouble(o_codes[0],code)
            
            if result != None:
                command = command + " [" + str( result ) + "] "
            else:
                return
    
        self.command.mdi( command )

    def manual_tbtn_clicked(self):
        log.info("Button manual clicked")

        if self.stat.task_mode==linuxcnc.MODE_MANUAL:
            return

        if self.stat.interp_state == linuxcnc.INTERP_READING or self.stat.interp_state == linuxcnc.INTERP_WAITING:
            self._warning_msg("Can't switch to MANUAL while interp state RUN")
            self._page_back()
        else:
            self.command.mode(linuxcnc.MODE_MANUAL)
            self.command.wait_complete()
            self.stat.poll()

    def mdi_tbtn_clicked(self):
        log.info("Button mdi clicked")
        
        if self.stat.task_mode==linuxcnc.MODE_MDI:
            return

        if self.stat.interp_state == linuxcnc.INTERP_READING or self.stat.interp_state == linuxcnc.INTERP_WAITING:
            self._warning_msg("Can't switch to MDI while interp state RUN")
            self._page_back()
        else:
            self.command.mode(linuxcnc.MODE_MDI)
            self.command.wait_complete()
            self.stat.poll()

    def auto_tbtn_clicked(self):
        log.info("Button auto clicked")

        if self.stat.task_mode==linuxcnc.MODE_AUTO:
            return

        if self.stat.interp_state == linuxcnc.INTERP_READING or self.stat.interp_state == linuxcnc.INTERP_WAITING:
            self._warning_msg("Can't switch to AUTO while interp state RUN")
            self._page_back()
        else:
            self.command.mode(linuxcnc.MODE_AUTO)
            self.command.wait_complete()
            self.stat.poll()

    def settings_tbtn_clicked(self):
        log.info("Button settings clicked")
        
        if self.widgets.bottomWidgets.currentIndex()==3:
            self._page_back()
        else:
            self.widgets.stackedWidget.setCurrentIndex(3)
            self.widgets.bottomWidgets.setCurrentIndex(3)

    def tabs_tbtn_clicked(self):
        log.info("Button tabs clicked")

        if self.widgets.bottomWidgets.currentIndex()==4:
            self._page_back()
        else:
            self.widgets.stackedWidget.setCurrentIndex(4)
            self.widgets.bottomWidgets.setCurrentIndex(4)

    def machine_tbtn_clicked(self):
        log.info("Button machine clicked")

        if self.stat.task_state == linuxcnc.STATE_ESTOP_RESET:
            self.command.state( linuxcnc.STATE_ON )
            self.command.wait_complete()
            self.stat.poll()
            if self.stat.task_state != linuxcnc.STATE_ON:
                self.error_message(None, 'Could not switch the machine on')
                self.widgets.machine_tbtn.setChecked(False)              
                return
        else:
            self.command.state( linuxcnc.STATE_OFF )
            self.command.wait_complete()
            self.stat.poll()

    def abort_tbtn_clicked(self):
        log.info("Button abort clicked")
            
        if len(NOTE.notify_list) > 0:
            NOTE.cleanup(None)
            NOTE.notify_list = []
            self.widgets.sender().setChecked(False)
        elif self.widgets.bottomWidgets.currentIndex() not in (0,1,2):
            self._page_back()
            self.widgets.sender().setChecked(False)
        else:
            self.widgets.stackedWidget.setCurrentIndex(5)
            self.widgets.bottomWidgets.setCurrentIndex(5)

    def equipment_tbtn_clicked(self):
        log.info("Button equipment clicked")

        if self.widgets.bottomWidgets.currentIndex()==6:
            self._page_back()
        else:
            self.widgets.bottomWidgets.setCurrentIndex(6)

    def homing_tbtn_clicked(self):
        log.info("Button homing clicked")

        if self.widgets.bottomWidgets.currentIndex()==9:
            self._page_back()
        else:
            self.widgets.bottomWidgets.setCurrentIndex(9)

    def load_tbtn_clicked(self):
        log.info("Button load clicked")

        if self.widgets.bottomWidgets.currentIndex()==7:
            self._page_back()
        else:
            self.widgets.stackedWidget.setCurrentIndex(6)
            self.widgets.bottomWidgets.setCurrentIndex(7)

    def edit_tbtn_clicked(self):
        log.info("Button edit clicked")

        if self.widgets.bottomWidgets.currentIndex()==8:
            self._page_back()
        else:
            self.widgets.stackedWidget.setCurrentIndex(7)
            self.widgets.bottomWidgets.setCurrentIndex(8)

            self.widgets.gcode_editor.editor.setFocus()

    def offset_tbtn_clicked(self):
        log.info("Button offset clicked")

        if self.widgets.bottomWidgets.currentIndex()==10:
            self._page_back()
        else:
            self.widgets.stackedWidget.setCurrentIndex(8)
            self.widgets.bottomWidgets.setCurrentIndex(10)

            self.widgets.originoffsetview.setFocus()

    def tools_tbtn_clicked(self):
        log.info("Button tools clicked")

        if self.widgets.bottomWidgets.currentIndex()==11:
            self._page_back()
        else:
            self.widgets.stackedWidget.setCurrentIndex(9)
            self.widgets.bottomWidgets.setCurrentIndex(11)
            for i in range(len(self.widgets.tooloffsetview.tablemodel.arraydata)):
                self.widgets.tooloffsetview.setRowHeight(i,20)
            self.widgets.tooloffsetview.setFocus()


    #####################
    # general functions #
    #####################

    def _page_back( self ):
        if self.stat.task_mode==linuxcnc.MODE_MANUAL:
            self.widgets.stackedWidget.setCurrentIndex(0)
            self.widgets.bottomWidgets.setCurrentIndex(0)
            self.widgets.manual_tbtn.setChecked(True)
        elif self.stat.task_mode==linuxcnc.MODE_MDI:
            self.widgets.stackedWidget.setCurrentIndex(1)
            self.widgets.bottomWidgets.setCurrentIndex(1)
            self.widgets.mdi_tbtn.setChecked(True)
        elif self.stat.task_mode==linuxcnc.MODE_AUTO:
            self.widgets.stackedWidget.setCurrentIndex(2)
            self.widgets.bottomWidgets.setCurrentIndex(2)
            self.widgets.auto_tbtn.setChecked(True)

    def _sensitize_widgets( self, widgetlist, value ):
        for name in widgetlist:
            try:
                self.widgets[name].setEnabled( value )
            except Exception, e:
                log.error("No widget named: %s to sensitize"%name)

    def _warning_msg(self, msg):
        NOTE.notify('Warning',msg,None,4,self.const.alertTime)


    ###################
    # general classes #
    ###################

    class JOG_pref():
        jog_activate = 0
        jog_step = 0
        jog_linear = 0
        jog_angular = 0
        jog_encoder = 0
        jog_continuous = 0

        def __getitem__(self, item):
            return getattr(self, item)

        def __setitem__(self, item, value):
            return __setattr__(self, item, value)

        def __setattr__(self, item, value):
            if item != "jog_activate" and not self.jog_activate:
                return False

            if item == "jog_step":
                STATUS.set_jog_increments(value,None)
                STATUS.set_jog_increment_angular(value,None)

            elif item == "jog_linear":
                STATUS.set_jograte(value)

            elif item == "jog_angular":
                STATUS.set_jograte_angular(value)

            self.__dict__[item] = value


    class preferences(ConfigParser.RawConfigParser):
        def __init__(self, path = None):
            ConfigParser.RawConfigParser.__init__(self)

            self.types = {
                bool: self.getboolean,
                float: self.getfloat,
                int: self.getint,
                str: self.get,
                repr: lambda section, option: eval(self.get(section, option)),
            }

            if not path:
                path = "~/.alterx_preferences"
            self.fn = os.path.expanduser(path)
            self.read(self.fn)

        def getpref(self, option, default = False, type = bool):
            m = self.types.get(type)
            try:
                o = m("DEFAULT", option)
            except Exception, detail:
                log.error("Get preference error: %s "%detail)
                self.set("DEFAULT", option, default)
                self.write(open(self.fn, "w"))
                if type in(bool, float, int):
                    o = type(default)
                else:
                    o = default
            return o

        def putpref(self, option, value, type = bool):
            self.set("DEFAULT", option, type(value))
            self.write(open(self.fn, "w"))

    class terminal(QtWidgets.QWidget):
        def __init__(self):
            super(QtWidgets.QWidget,self).__init__()
            try:
                self.process = QtCore.QProcess(self)
                self.process.start('xterm',['-into', str(int(self.winId())), '-geometry', "600x60+0+400"])
            except Exception as e:
                log.error( "%s"%e)

    class CONST(object):
        numButtons = 11
        useMacro = True
        alertTime = 99
        
        
        def __init__(self):
            pass

        def __setattr__(self, *_):
            pass

    class dialog_model(QtWidgets.QWidget):

        def __init__(self):
            super(QtWidgets.QWidget,self).__init__()
            
        def getInteger(self,title,message):
            i, okPressed = QtWidgets.QInputDialog.getInt(self,title,message)
            if okPressed:
                return i
            return

        def getDouble(self,title,message):
            d, okPressed = QtWidgets.QInputDialog.getDouble(self,title,message)
            if okPressed:
                return d
            return
            
        def getChoice(self,title,message):
            items = ("Red","Blue","Green")
            item, okPressed = QtWidgets.QInputDialog.getItem(self,title,message, items, 0, False)
            if ok and item:
                return item
            return

        def getText(self,title,message):
            text, okPressed = QtWidgets.QInputDialog.getText(self,title,message, QtWidgets.QLineEdit.Normal, "")
            if okPressed and text != '':
                return text
            return

    class button_model(QtWidgets.QWidget):
        def __init__(self, index, l, b, name=None, parent=None):
            super(QtWidgets.QWidget,self).__init__()

            self.btn = QtWidgets.QPushButton("BTN_%s%d"%(l,b))
            self.btn.setObjectName("BTN_%s%d"%(l,b))
            self.btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)

            if "menus.%s.%s"%(l,name) in sys.modules.keys():
                self.p = getattr(globals()[l],name).module.func(self.btn,parent)
            elif name != None:
                self.p = None
                log.error( "No module with name: menus.%s.%s"%(l,name) )
            else:
                return

            if hasattr(self.p,"execute"):
                self.btn.clicked.connect(partial(self.bottom_buttons_callback,index,b))
    
            if hasattr(self.p,"update"):
                timer = QtCore.QTimer(self)
                timer.timeout.connect(self.bottom_buttons_update)
                timer.start(1000)

        def bottom_buttons_callback(self,panel,button):
            try:
                self.p.execute()
            except Exception as e:
                log.error('Button execute exception: %s', e)

        def bottom_buttons_update(self):
            try:
                self.p.update()
            except Exception as e:
                log.error('Button update exception: %s', e)

    #####################
    # KEY BINDING CALLS #
    #####################

    def on_keycall_F12(self,event,state,shift,cntrl):
        if state:
            log.debug('Button F12 pressed: Show style dialog')
            self.STYLE.load_dialog()

    def on_keycall_F11(self,event,state,shift,cntrl):
        if state:
            log.debug('Button F11 pressed: Hide cursor')
            if self.hide_cursor:
                QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.BlankCursor))
            else:
                QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

            self.hide_cursor = not self.hide_cursor
            QtWidgets.qApp.processEvents()

    ###########################
    # **** closing event **** #
    ###########################

    def closing_cleanup__(self):
        NOTE.cleanup(None)
        try:
            if self.xterm and self.xterm.process:
                self.xterm.process.kill()
        except:
            pass

    ##############################
    # required class boiler code #
    ##############################

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, item, value):
        return setattr(self, item, value)

################################
# required handler boiler code #
################################

def get_handlers(halcomp,widgets,paths):
     return [HandlerClass(halcomp,widgets,paths)]
