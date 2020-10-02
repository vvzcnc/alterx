# -*- coding: utf-8 -*-
#
# AlterX GUI - core main
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

__all__ = ['MAIN']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common.preferences import *
from alterx.common import *
from alterx.core.linuxcnc import *
from alterx.gui.util import *

from functools import partial
from collections import OrderedDict

class MultiOrderedDict(OrderedDict):
    def __setitem__(self, key, value):
        if isinstance(value, list) and key in self:
            self[key].extend(value)
        else:
            OrderedDict.__setitem__(self, key, value)

class Main():
    #------ Initialize ------#
    def __init__(self):
        UPDATER.add('update_feed_labels')
        UPDATER.add('feed_mode')
        UPDATER.add('diameter_multiplier', 1)
        UPDATER.add('display_feedrate',-1)
        UPDATER.add('display_spindlerate',-1)
        UPDATER.add('display_jog_fast')  
        UPDATER.add('display_button_binding')
        UPDATER.add('display_inputs_binding')
        UPDATER.add('display_encoder_binding')   
        UPDATER.add('hal_jog_enable')

        UPDATER.signal("display_encoder_binding", self.display_encoder_handler)
        UPDATER.signal("display_inputs_binding", self.display_inputs_handler)
        UPDATER.signal("display_spindlerate", self.spindlerate_changed)
        UPDATER.signal("display_feedrate", self.feedrate_changed)
        UPDATER.signal("task_state", self.task_state_handler)
        UPDATER.signal("task_mode", self.task_mode_handler)
        UPDATER.signal("homed", self.homed_handler)
        UPDATER.signal("file", self.load_program_handler)
        UPDATER.signal("program_units", self.change_units_handler)
        UPDATER.signal("gcodes", self.gcode_changed)
        UPDATER.signal("hal_jog_enable", self.hal_jog_enable_changed)
        
        self.keyboard_cmd_list = "0000000"
        if HAL:
            self.halcomp = HAL.component( "alterx" )

            self.config = ConfigParser.ConfigParser(
                dict_type=MultiOrderedDict,allow_no_value=True)
            self.config.optionxform = str
            ini = os.environ['INI_FILE_NAME']
            self.config.read(ini)
            items = self.config.items("DISPLAY")
            for i in items:
                item = i[0].lower()
                if item.startswith("message_"):
                    pin = self.halcomp.newpin( "messages.{}".format(item), HAL.HAL_BIT, HAL.HAL_IN )
                    UPDATER.listen("messages.{}".format(item), pin.get)
                    UPDATER.signal("messages.{}".format(item), partial(self.hal_messages_handler,i[1]))
            
            self.halcomp.newpin( "jog-enable", HAL.HAL_BIT, HAL.HAL_OUT )
            
            for i in range(7):
                pin = self.halcomp.newpin( "io.output-"+str(i), HAL.HAL_BIT, HAL.HAL_IN )
                UPDATER.listen("io.output-"+str(i),pin.get)
                UPDATER.signal("io.output-"+str(i), partial(self.hw_output_state_handler,i))
                self.halcomp.newpin( "io.input-"+str(i), HAL.HAL_BIT, HAL.HAL_OUT )
            self.halcomp.ready()

#------ Global handlers ------#
    def hal_messages_handler(self, message, signal):
        printInfo(message)
        Notify.Info(message)
        
    def hal_jog_enable_changed(self, signal):
        if HAL and self.halcomp:
            self.halcomp["jog-enable"] = signal

    def display_encoder_handler(self, signal):
        printVerbose(_("LinuxCNC display input signal {}", signal))

    def display_inputs_handler(self, signals):
        if HAL and self.halcomp:
            for i in range(7):
                self.halcomp["io.input-"+str(i)] = signals[i]

    def hw_output_state_handler(self, number, signal):
        self.keyboard_cmd_list = ( self.keyboard_cmd_list[:number] + 
                                    str(int(signal)) + 
                                    self.keyboard_cmd_list[number+1:] )
        UPDATER.emit("keyboard_set_output_state",self.keyboard_cmd_list)

    def spindlerate_changed(self, value):
		COMMAND.spindleoverride(value/100.0*INFO.max_spindle_override)

    def feedrate_changed(self, value):
        COMMAND.feedrate(value/100.0*INFO.max_feed_override)
        COMMAND.rapidrate(value/100.0*INFO.max_feed_override)
        UPDATER.emit("jog_speed",value/100.0)

    def gcode_changed(self, data):
        for i in sorted(data[1:]):
            if i == -1:
                continue
            active = "G{:.0f}".format(
                i/10) + (".{}".format(i % 10) if i % 10 != 0 else "")

            # G93 inverse time mode
            # G94 feed per minute mode
            # G95 feed per revolution mode
            # G96 constant surface speed mode
            # G97 stop constant surface speed control

            if active in ['G93', 'G94', 'G95', 'G96', 'G97']:
                if active == 'G94':
                    INFO.feed_per_units = _("min")
                elif active == 'G95':
                    INFO.feed_per_units = _("rev")
                UPDATER.emit('feed_mode', active)
            elif active == 'G7':
                UPDATER.emit('diameter_multiplier', 2)
            elif active == 'G8':
                UPDATER.emit('diameter_multiplier', 1)

    def task_state_handler(self, data):
        if data == LINUXCNC.STATE_ESTOP:
            state = _("ESTOP")
        elif data == LINUXCNC.STATE_ESTOP_RESET:
            state = _("ESTOP RESET")
        elif data == LINUXCNC.STATE_ON:
            state = _("ON")
        elif data == LINUXCNC.STATE_OFF:
            state = _("OFF")
        else:
            state = _("None")

        if data != LINUXCNC.STATE_ON:
            if STAT.task_mode == LINUXCNC.MODE_MANUAL:
                UPDATER.emit("screen_manual")
            else:
                COMMAND.mode(LINUXCNC.MODE_MANUAL)

        printVerbose(_("LinuxCNC state {}", state))

    def task_mode_handler(self, data):
        if data == LINUXCNC.MODE_MANUAL:
            mode = _("MANUAL")
            UPDATER.emit("screen_manual")
        elif data == LINUXCNC.MODE_MDI:
            mode = _("MDI")
            UPDATER.emit("screen_mdi")
        elif data == LINUXCNC.MODE_AUTO:
            mode = _("AUTO")
            UPDATER.emit("screen_auto")
        else:
            mode = _("None")

        printVerbose(_("LinuxCNC mode {}", mode))

    def homed_handler(self, data):
        printVerbose(_("LinuxCNC homed {}", data))

    def load_program_handler(self, data):
        if STAT.task_mode == LINUXCNC.MODE_AUTO:
            UPDATER.emit("screen_auto")
        printInfo(_('Loaded: {}', data))

    def change_units_handler(self, data):
        if data == 1:
            INFO.linear_units = _("inch")
        elif data == 2:
            INFO.linear_units = _("mm")
        elif data == 3:
            INFO.linear_units = _("cm")

        axis_mul = 1
        if INFO.machine_is_metric != INFO.get_metric():
            if INFO.machine_is_metric:
                axis_mul /= 25.4
            else:
                axis_mul *= 25.4

        INFO.units_factor = axis_mul

        UPDATER.emit('update_feed_labels')
        printInfo(_('Units: {}', INFO.linear_units))

#------ Button callbacks ------#
    def jog_button_callback(self, button):  
        if UPDATER.value("jog_activate"):
            COMMAND.teleop_enable(1)
            direction = 0
            if button in (4,6,7,8):
                direction = -1
            elif button in (1,2,3,5):
                direction = 1  

            selected_axis = -1            
            if button in (4,5):
                selected_axis = 0
            elif button in (2,7):
                selected_axis = 1
            elif button in (3,6):
                selected_axis = 2  
            elif button in (1,8):
                selected_axis = 3

            speed = 0
            if STAT.joint[selected_axis]['jointType'] == 1:
                if UPDATER.value("display_jog_fast"):
                    speed = direction*float(
                        INI.find("DISPLAY", "MAX_LINEAR_VELOCITY"))/60.0
                else:
                    speed = direction*UPDATER.value("jog_speed")*float(
                        INI.find("DISPLAY", "MAX_LINEAR_VELOCITY"))/60.0
            else:
                if UPDATER.value("jog_fast"):
                    speed = direction*float(
                        INI.find("DISPLAY", "MAX_ANGULAR_VELOCITY"))/60.0
                else:
                    speed = direction*UPDATER.value("jog_speed")*float(
                        INI.find("DISPLAY", "MAX_LINEAR_VELOCITY"))/60.0

            if not UPDATER.value("jog_encoder"):
                if UPDATER.value("jog_continuous"):
                    if button:
                        COMMAND.jog(LINUXCNC.JOG_CONTINUOUS,False,selected_axis,speed)
                    else:
                        for a in range(9):
                            COMMAND.jog(LINUXCNC.JOG_STOP,False,a) 
                else:
                    if button:
                        COMMAND.jog(LINUXCNC.JOG_INCREMENT,False,
                            selected_axis,speed,UPDATER.value("jog_increment"))
                    else:
                        for a in range(9):
                            COMMAND.jog(LINUXCNC.JOG_STOP,False,a) 
            printVerbose(_("LinuxCNC mode {} {} {} {}", direction,selected_axis,speed,button))

    def side_button_callback(self, button):
        if button.label == "abort":
            self.btn_abort_callback(button)
        elif button.label == "equipment":
            self.btn_equipment_callback(button)
        elif button.label == "load":
            self.btn_load_callback(button)
        elif button.label == "homing":
            self.btn_homing_callback(button)
        elif button.label == "offset":
            self.btn_offset_callback(button)
        elif button.label == "tool":
            self.btn_tool_callback(button)
        elif button.label == "manual":
            self.btn_manual_callback(button)
        elif button.label == "mdi":
            self.btn_mdi_callback(button)
        elif button.label == "auto":
            self.btn_auto_callback(button)
        elif button.label == "settings":
            self.btn_settings_callback(button)
        elif button.label == "tabs":
            self.btn_tabs_callback(button)
        elif button.label == "machine":
            self.btn_machine_callback(button)
        else:
            printError(_("Unknown button"))

    def btn_abort_callback(self, button):
        if Notify.count() > 0:
            Notify.closeAll()
        else:
            UPDATER.emit("screen_display")

    def btn_equipment_callback(self, button):
        UPDATER.emit("screen_equipment")

    def btn_load_callback(self, button):
        UPDATER.emit("screen_load")

    def btn_homing_callback(self, button):
        UPDATER.emit("screen_homing")

    def btn_offset_callback(self, button):
        UPDATER.emit("screen_offset")
        UPDATER.emit("reload_offsets")

    def btn_tool_callback(self, button):
        UPDATER.emit("screen_tool")
        UPDATER.emit("reload_tools")

    def btn_manual_callback(self, button):
        if STAT.task_mode == LINUXCNC.MODE_MANUAL:
            UPDATER.emit("screen_manual")
        else:
            COMMAND.mode(LINUXCNC.MODE_MANUAL)

    def btn_mdi_callback(self, button):
        if STAT.task_mode == LINUXCNC.MODE_MDI:
            UPDATER.emit("screen_mdi")
        else:
            COMMAND.mode(LINUXCNC.MODE_MDI)

    def btn_auto_callback(self, button):
        if STAT.task_mode == LINUXCNC.MODE_AUTO:
            UPDATER.emit("screen_auto")
        else:
            COMMAND.mode(LINUXCNC.MODE_AUTO)

    def btn_settings_callback(self, button):
        UPDATER.emit("screen_settings")

    def btn_tabs_callback(self, button):
        UPDATER.emit("screen_tabs")

    def btn_machine_callback(self, button):
        COMMAND.state(LINUXCNC.STATE_ESTOP_RESET)

        if STAT.task_state == LINUXCNC.STATE_ON:
            COMMAND.state(LINUXCNC.STATE_OFF)
        else:
            COMMAND.state(LINUXCNC.STATE_ON)


MAIN = Main()
