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


class Main():
    #------ Initialize ------#
    def __init__(self):
        UPDATER.add('update_feed_labels')
        UPDATER.add('feed_mode')
        UPDATER.add('diameter_multiplier', 1)

        UPDATER.connect("task_state", self.task_state_handler)
        UPDATER.connect("task_mode", self.task_mode_handler)
        UPDATER.connect("homed", self.homed_handler)
        UPDATER.connect("file", self.load_program_handler)
        UPDATER.connect("program_units", self.change_units_handler)
        UPDATER.connect("gcodes", self.gcode_changed)

#------ Global handlers ------#
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

        UPDATER.emit('update_feed_labels')
        printInfo(_('Units: {}', INFO.linear_units))

#------ Button callbacks ------#

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
        UPDATER.emit("screen_display")

    def btn_equipment_callback(self, button):
        UPDATER.emit("screen_equipment")

    def btn_load_callback(self, button):
        UPDATER.emit("screen_load")

    def btn_homing_callback(self, button):
        UPDATER.emit("screen_homing")

    def btn_offset_callback(self, button):
        UPDATER.emit("reload_offsets")
        UPDATER.emit("screen_offset")

    def btn_tool_callback(self, button):
        UPDATER.emit("reload_tools")
        UPDATER.emit("screen_tool")

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
