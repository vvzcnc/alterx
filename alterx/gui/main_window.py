# -*- coding: utf-8 -*-
#
# AlterX GUI - mainwindow
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

__all__ = ['MainWindow']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common.preferences import *
from alterx.common import *

from alterx.core.main import MAIN
from alterx.core.linuxcnc import *

from alterx.gui.util import *
from alterx.gui.main_screen import *
from alterx.gui.path_viewer import *
from alterx.gui.mdi_history import *
from alterx.gui.gcode_editor import *
from alterx.gui.file_manager import *
from alterx.gui.offset_viewer import *
from alterx.gui.tool_viewer import *
from alterx.gui.dro_viewer import *
from alterx.gui.tabs_viewer import *
from alterx.gui.settings_viewer import *
from alterx.gui.style_editor import *

from functools import partial

class MainWindow(QWidget):
    TITLE = _("AlterX v{}", VERSION_STRING)

    @classmethod
    def start(cls):
        QApplication.setOrganizationName("alterx")
        QApplication.setOrganizationDomain(ALTERX_HOME_DOMAIN)
        QApplication.setApplicationName("AlterX")
        QApplication.setApplicationVersion(VERSION_STRING)

        mainwnd = cls()
        mainwnd.show()

        mainwnd.setWindowState(Qt.WindowMaximized)

        return mainwnd

    def activate_screen(self, screen, state=None):
        w, b, i = screen
        if w:
            self.mainLayout.centralWidgets.setCurrentWidget(w)
        if b:
            self.mainLayout.bottomWidgets.setCurrentWidget(b)
            
        if i is not None:
            UPDATER.emit("mainscreen_full",i)
            
    def set_stylesheet(self):
        ss_name = os.path.join(STYLESHEET_DIR, PREF.getpref(
            "stylesheet", "default.qss", str))
            
        if not os.path.isfile(ss_name):
            ss_name = os.path.join(STYLESHEET_DIR, "default.qss")
        try:
            with open(ss_name,'r') as file:
                stylesheet = file.read()
                try:
                    # Python v2.
                    stylesheet = unicode(stylesheet, encoding='utf-8')
                except NameError:
                    # Python v3.
                    stylesheet = str(stylesheet)
                self.setStyleSheet(stylesheet)
        except Exception as e:
            printWarning(_("Failed to load stylesheet: {}",e))
            
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        StyleSheetEditor.setMainwindow(self)
        self.set_stylesheet()

        # Main layout
        self.mainLayout = MainLayout(self)

        ON_STATE = [LINUXCNC.STATE_ON]  # Enable when CNC is ON
        # Enable when CNC is ON, is HOMED
        HOMED_STATE = ON_STATE + \
            [(1,)*len(INFO.coordinates)+(0,)*(9-len(INFO.coordinates))]
        # Enable when CNC is ON, is HOMED and in MDI mode
        MDI_STATE = HOMED_STATE + [LINUXCNC.MODE_MDI]
        # Enable when CNC is ON, is HOMED and in AUTO mode
        AUTO_STATE = HOMED_STATE + [LINUXCNC.MODE_AUTO]
        # Activate only when bottom widget active
        SEC_WIDGET = [None, None, None, True]

        # info widget state
        infoWidget = [False,False,False,True,True,None,True,None,True,True,None,True,True]

        # mainscreen widgets
        centralWidget = [DROWidget, MDIHistory, GcodeWidget, SettingsWidget, TabsWidget, None,
                         PathViewer, None, FileManager, GcodeEditor, None, OriginOffsetView, ToolOffsetView]

        # buttons for mainscreen mode
        bottomWidget = ["manual", "mdi", "auto", "settings", "tabs", None,
                        "display", "equipment", "load", "edit", "homing", "offset", "tool"]

        # side buttons
        #        #layout#    #name#        #enable state#    #active state#            #
        sideWidget = [
            ["right",    "manual",    [],    [None, None, LINUXCNC.MODE_MANUAL, None]],
            ["right",    "mdi",        HOMED_STATE,[None, None, LINUXCNC.MODE_MDI, None]],
            ["right",    "auto",        HOMED_STATE,[None, None, LINUXCNC.MODE_AUTO, None]],
            ["right",    "settings",    [],            SEC_WIDGET],
            ["right",    "tabs",        ON_STATE,    SEC_WIDGET],
            ["right",    "machine",    [],            ON_STATE+[None]*3],
            ["left",    "abort",    [],    SEC_WIDGET],
            ["left",    "equipment",ON_STATE,    SEC_WIDGET],
            ["left",    "load",        AUTO_STATE,    SEC_WIDGET],
            [None],
            ["left",    "homing",    ON_STATE +
                                     [None, LINUXCNC.MODE_MANUAL], SEC_WIDGET],
            ["left",    "offset",    MDI_STATE,    SEC_WIDGET],
            ["left",    "tool",        MDI_STATE,    SEC_WIDGET],
        ]

        for i, name in enumerate(bottomWidget):
            widget = None
            if centralWidget[i] is not None:
                widget = centralWidget[i]()
                self.mainLayout.centralWidgets.addWidget(widget)

            buttons = None
            bottom_index = None
            if name is not None:
                buttons = BottomWidget(name)
                bottom_index = self.mainLayout.bottomWidgets.addWidget(buttons)

                UPDATER.add("screen_{}".format(name))
                UPDATER.connect("screen_{}".format(name), partial(
                    self.activate_screen, (widget, buttons, infoWidget[i])))

            if sideWidget[i][0] is not None:
                if sideWidget[i][3][3]:
                    sideWidget[i][3][3]=bottom_index
                    
                sidebutton = SideButton(
                    sideWidget[i][1], sideWidget[i][2], sideWidget[i][3])
                if sideWidget[i][0] == "right":
                    self.mainLayout.rightLayout.addWidget(sidebutton)
                else:
                    self.mainLayout.leftLayout.addWidget(sidebutton)

        UPDATER.start(INFO.display_cycle_time)
