# -*- coding: utf-8 -*-
#
# AlterX GUI - linuxcnc
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

__all__ = ['STAT', 'COMMAND', 'INI', 'UPDATER', 'LINUXCNC', 'INFO', 'POSLOG','GCODE','HAL']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *
from alterx.gui.qt_bindings import *

import time
import socket

class fake_linuxcnc():
    axis = []
    joint = []
    def __call__(self, source, *args):
        return 0

    def __getattr__(self,name):
        return 0

    def __dir__(self):
        return []
        
    def poll(self):
        return 0
        
    def find(self,section,option):
        return ""

        
class fake_position_logger():
    def __getattr__(self,name):
        return 0

    def __call__(self, source, *args):
        return self
        
    def start(self, *args):
        return 0
        
        
class fake_command():
    def __getattr__(self,name):
        return lambda *args: None


try:
    import linuxcnc as LINUXCNC
    import gcode as GCODE
    import hal as HAL

    STAT = LINUXCNC.stat()
    COMMAND = LINUXCNC.command()
    ERROR = LINUXCNC.error_channel()
    POSLOG = LINUXCNC.positionlogger
    INI = LINUXCNC.ini(os.environ['INI_FILE_NAME'])
    
    STAT.poll()
    ERROR.poll()

    from alterx.core.remote import RemoteControl
    
    port = INI.find("DISPLAY", "REMOTE_PORT") or RemoteControl.PORT
    if port:
        RemoteControl.PORT = port
        REMOTE = RemoteControl()
        
except Exception as e:
    printError(_("Failed to import LinuxCNC module: '{}'", e))
    
    LINUXCNC = fake_linuxcnc()
    STAT = fake_linuxcnc()
    COMMAND = fake_command()
    POSLOG = fake_position_logger()
    ERROR = fake_linuxcnc()
    INI = fake_linuxcnc()
    GCODE = fake_linuxcnc()
    HAL = None
    
    QMessageBox.critical(None,
            _("AlterX: Failed to import LinuxCNC"),
            _("AlterX interface launched in recovery mode!"),
            QMessageBox.Ok,
            QMessageBox.Ok)


class linuxcnc_info():
    def __init__(self):
        if INI.find('TRAJ', 'LINEAR_UNITS') in ('mm', 'metric'):
            self.machine_is_metric = True
        else:
            self.machine_is_metric = False

        self.units_factor = 1

        self.default_axes_list = {'X':0,'Y':1,'Z':2,'A':3,'B':4,'C':5,'U':6,'V':7,'W':8}
        self.coordinates = (INI.find('TRAJ', 'COORDINATES') or ' ').split(' ')
        
        if int(INI.find('TRAJ', 'AXES')) == len(self.coordinates):
            self.joints = [ i for i,j in enumerate(self.coordinates) ]
        else:
            self.joints = [ self.default_axes_list[j] for j in self.coordinates ]

        self.homed_list = [0,]*9
        for i in self.joints:
            self.homed_list[i] = 1

        self.machine_is_lathe = True if INI.find('DISPLAY', 'LATHE') else False

        self.get_metric = lambda: False if STAT.program_units == 1 else True
        
        if (INI.find("DISPLAY", "POSITION_FEEDBACK") or "ACTUAL").lower() == "actual":
            self.feedback_actual = True
        else:
            self.feedback_actual = False
        
        self.tool_file = INI.find('EMCIO', 'TOOL_TABLE') or 'tools.var'
        self.parameter_file = INI.find("RS274NGC", "PARAMETER_FILE") or 'parameters.var'
        self.preferences_file = INI.find("DISPLAY", "PREFERENCE_FILE_PATH") or 'preferences.var'
        self.position_file = INI.find("TRAJ", "POSITION_FILE") or 'position.var'
        self.mdi_history_file = INI.find("DISPLAY", "MDI_HISTORY_FILE") or 'mdi.log'
        self.working_dir = os.path.dirname(os.environ['INI_FILE_NAME'])
        
        self.max_feed_override = float(INI.find("TRAJ", "MAX_FEED_OVERRIDE") or '1.0')
        self.max_spindle_override = float(INI.find("TRAJ", "MAX_SPINDLE_OVERRIDE") or '1.0')
        
        self.dro_format = "{:.3f}"
        self.linear_units = _("mm")
        self.angular_units = _("deg")
        self.spindle_units = _("rev")
        self.spindle_per_units = _("min")
        self.feed_per_units = _("min")
        self.angular_per_units = _("min")

        self.display_cycle_time = float(INI.find("DISPLAY", "CYCLE_TIME") or '0.1')*1000
        
        self.axes_list = "joint" if hasattr(STAT, "joint") else "axis"

    def get_offset_table(self):
        return [[0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],]

    def get_tool_info(self, tool):
        pass
        
    def get_selected_tool(self):
        pass

INFO = linuxcnc_info()


class linuxcnc_poll(QTimer):
    def __init__(self):
        QTimer.__init__(self)
        self.timeout.connect(self.run)
        self.stat_old = {}
        self._observers = {}
        self._listener = {}
        self.custom_signals = {}
        self.custom_signals_old = {}
        
        self.add("last_error")

    # 'One to many' item check
    def run(self):
        try:
            STAT.poll()
            error_data = ERROR.poll()
        except LINUXCNC.error as e:
            printError(_("Failed to poll LinuxCNC stat: '{}'", e))
            return

        if error_data:
            kind, text = error_data
            self.emit("last_error",text)
            if kind in (LINUXCNC.NML_ERROR, LINUXCNC.OPERATOR_ERROR):
                printError(text)
                Notify.Error(text)
            else:
                printInfo(text)
                Notify.Info(text)

        for s in dir(STAT):
            if not s.startswith('_'):
                if s not in self.stat_old or self.stat_old[s] != getattr(STAT, s):
                    self.stat_old[s] = getattr(STAT, s)
                    if s in self._observers:
                        for h in self._observers[s]:
                            try:
                                h(self.stat_old[s])
                            except Exception as e:
                                printError(
                                    _("Failed to execute '{}' handler {}: '{}'", s, h, e))

		for name in self._listener:
			self.custom_signals[name] = self._listener[name]()

        for name in self.custom_signals:
            if ( self.custom_signals[name] != self.custom_signals_old[name] and 
                name in self._observers ):
                self.custom_signals_old[name] = self.custom_signals[name]

                for h in self._observers[name]:
                    try:
                        h(self.custom_signals_old[name])
                    except Exception as e:
                        printError(
                            _("Failed to execute '{}' handler {}: '{}'", name, h, e))

    # 'Many to one' item check
    def check(self, name):
        if ( name in self.custom_signals and 
            self.custom_signals[name] != self.custom_signals_old[name] ):
            self.custom_signals_old[name] = self.custom_signals[name]
            return True
        return False

    # 'Many to one' item get value
    def value(self, name):
        if name in self.custom_signals:
            return self.custom_signals[name]
        elif name in dir(STAT):
            return getattr(STAT, name)
        return False

    # Emit custom signal
    def emit(self, name, value=None):
        if name in self.custom_signals:
            if ( value is None and 
                self.custom_signals[name] == self.custom_signals_old[name] ):
                value = not self.custom_signals[name]

            self.custom_signals[name] = value
        else:
            printError(_("Failed to emit signal. Signal '{}' no exist", name))

    # Create custom listener in database
    def listen(self, name, method):
        if name not in self._listener and name not in self.custom_signals:
            self._listener[name] = method
            self.custom_signals[name] = method()
            self.custom_signals_old[name] = method()
        else:
            printError(_("Failed to add listener. Listener '{}' already exist", name))

    # Create custom signal in database
    def add(self, name, value=False):
        if name not in self.custom_signals:
            self.custom_signals[name] = value
            self.custom_signals_old[name] = value
        else:
            printError(_("Failed to add signal. Signal '{}' already exist", name))

    # Add signal to 'one to many' database
    def signal(self, name, handler):
        if name in self._observers:
            self._observers[name].append(handler)
        else:
            self._observers[name] = [handler]

    def __getattr__(self, name):
        try:
            return self.custom_signals[name]
        except Exception as e:
            printError(_("Failed to get atribute {}: {}", name, e))
        return None

    #def __del__(self):
    #    self.wait()

UPDATER = linuxcnc_poll()
