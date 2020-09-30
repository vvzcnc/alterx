# -*- coding: utf-8 -*-
#
# AlterX GUI - widgets
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

__all__ = ['BottomWidget', 'SideButton', 'MainLayout']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

from alterx.gui.util import *
from alterx.core.main import MAIN
from alterx.core.linuxcnc import *

from menus import *

from functools import partial

class BottomButton(QPushButton):
    def __init__(self, label):
        QPushButton.__init__(self, label)
        self.setObjectName(label)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.resizeEvent = self.resize_icon
        
    def setup(self, menu):
        if hasattr(menu, "execute"):
            self.clicked.connect(partial(menu.execute))

        if hasattr(menu, "update"):
            timer = QTimer(self)
            timer.timeout.connect(menu.update)
            timer.start(1000)

    def resize_icon(self,event):
        QWidget.resizeEvent(self, event)
        w = event.size().width()
        h = event.size().height()
        self.setIconSize(QSize(w*0.8, h*0.8))

class BottomWidget(QWidget):
    def __init__(self, layout_name):
        QWidget.__init__(self)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.setLayout(layout)

        menu_names = []
        try:
            menu_names = getattr(globals()[layout_name], 'buttons_order')
            if not isinstance(menu_names, list):
                menu_names = []
                raise Exception("'buttons_order' is not a list")
        except Exception as e:
            printError(
                _('Invalid buttons order list for menu {}, {}', layout_name, e))

        last_btn = 0
        for btn_number, name in enumerate(menu_names):
            btn = BottomButton("btn_%s_%d" % (layout_name, btn_number))
            layout.addWidget(btn)
            last_btn = btn_number+1

            if name is None:
                btn.setText("")
                continue

            if "menus.%s.%s" % (layout_name, name) in sys.modules.keys():
                menu = getattr(globals()[layout_name], name).module.func(btn)
            elif name != None:
                menu = None
                printError(
                    _("No menu module with name: menus.{}.{}", layout_name, name))
            else:
                return

            btn.setup(menu)

        for btn_number in range(last_btn, 11):
            btn = BottomButton("btn_%s_%d" % (layout_name, btn_number))
            btn.setText("")
            layout.addWidget(btn)

class SideButton(QPushButton):
    def __init__(self, label, checkDisable, checkToggle, parent=None,):
        QPushButton.__init__(self, "btn_%s" % (label), parent)
        self.label = label
        self.checkDisable = checkDisable
        self.checkToggle = checkToggle
        self.active = False

        self.set_active(self.active)
        self.setObjectName("btn_%s" % (label))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.resizeEvent = self.resize_icon
        self.clicked.connect(partial(MAIN.side_button_callback, self))

        checkList = ["task_state", "homed", "task_mode", "secondary_mode"]
        self.checkState = [True, True, True]
        for index, check in enumerate(checkDisable):
            if check:
                UPDATER.signal(checkList[index], 
                            lambda s, c=check, i=index: self.set_disable(
                                            True if s == c else False, i))

        for index, check in enumerate(checkToggle):
            if check:
                UPDATER.signal(checkList[index], 
                            lambda s, c=check: self.set_active(
                                            True if s == c else False))

    def resize_icon(self,event):
        QPushButton.resizeEvent(self, event)
        w = event.size().width()
        h = event.size().height()
        self.setIconSize(QSize(w*0.8, h*0.8))
                
    def set_active(self, state):
        self.active = state
        self.setProperty("active", self.active)
        self.setStyleSheet(self.styleSheet())

        icon = None
        for fn in os.listdir(os.path.join(IMAGE_DIR, "mainmenu")):
            if "{}{}.".format(self.label, "_on" if state == True else "") in fn:
                icon = os.path.join(IMAGE_DIR, "mainmenu", fn)

        if icon:
            with open(icon,'r') as i:
                #img = QImage()
                #img.loadFromData(i.read())
                #pixmap = QPixmap()
                #pixmap.convertFromImage(img)
                #self.setIcon(QIcon(pixmap))
                self.setIcon(QIcon(icon))
                #self.setIconSize(QSize(90, 90))
                self.setText("")

    def set_disable(self, state, index):
        self.checkState[index] = state

        if self.checkState == [True, True, True]:
            self.setEnabled(True)
        else:
            self.setEnabled(False)

class ToolWidget(QGroupBox):
    def __init__(self, parent=None):
        QGroupBox.__init__(self, parent)
        self.setTitle(_("Tool"))
        h1 = QHBoxLayout()
        self.tool_number = QLabel(_("No tool"))
        self.tool_number.setObjectName("lbl_main_screen_toolnum")
        self.tool_comment = QLabel(_("No comment"))
        self.tool_comment.setObjectName("lbl_main_screen_toolcomment")

        self.tool_comment.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        h1.addWidget(self.tool_number, 1)
        h1.addWidget(self.tool_comment, 7)
        self.setLayout(h1)
        UPDATER.signal("tool_in_spindle", self.on_tool_changed)

    def on_tool_changed(self, data):
        if data == 0:
            self.tool_number.setText(_("No tool"))
            self.tool_comment.setText(_("No comment"))
        else:
            tool = INFO.get_tool_info(data)
            self.tool_number.setText("#{}".format(data))
            self.tool_comment.setText("{}".format(tool[19]))

class GCodeWidget(QGroupBox):
    def __init__(self, parent=None):
        QGroupBox.__init__(self, parent)
        self.setTitle(_("Codes"))
        v1 = QVBoxLayout()
        h1 = QHBoxLayout()
        self.feed = QLabel("FO")
        self.feed.setObjectName("lbl_main_screen_feedcode")
        self.spindle = QLabel("SO")
        self.spindle.setObjectName("lbl_main_screen_spindlecode")
        self.spindle.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        h1.addWidget(self.feed)
        h1.addWidget(self.spindle)
        v1.addLayout(h1)
        self.g_codes = QLabel("G")
        self.g_codes.setWordWrap(True)
        self.g_codes.setObjectName("lbl_main_screen_gcode")
        v1.addWidget(self.g_codes)
        v1.addStretch()
        # v1.addItem(QSpacerItem(0,0,QSizePolicy.Expanding,QSizePolicy.Expanding))
        v1.addWidget(HSeparator())
        self.m_codes = QLabel("M")
        self.m_codes.setWordWrap(True)
        self.m_codes.setObjectName("lbl_main_screen_mcode")
        v1.addWidget(self.m_codes)
        self.setLayout(v1)
        UPDATER.signal("mcodes", self.on_mcode_changed)
        UPDATER.signal("gcodes", self.on_gcode_changed)
        UPDATER.signal("settings", self.on_settings_changed)

    def on_settings_changed(self, data):
        self.feed.setText("F{}".format(data[1]))
        self.spindle.setText("S{}".format(data[2]))

    def on_mcode_changed(self, data):
        active = ""
        for i in sorted(data[1:]):
            if i == -1:
                continue
            active = active + "M{} ".format(i)

        self.m_codes.setText(active)

    def on_gcode_changed(self, data):
        active = ""
        for i in sorted(data[1:]):
            if i == -1:
                continue
            active = active + \
                "G{:.0f}".format(i/10) + (".{} ".format(i %
                                                        10) if i % 10 != 0 else " ")

        self.g_codes.setText(active)

class SpindleWidget(QGroupBox):
    def __init__(self, parent=None):
        QGroupBox.__init__(self, parent)
        self.setTitle(_("Spindlerate"))
        v1 = QVBoxLayout()
        self.actual_spindlerate = QLabel(
            _("Actual: {:.2f} {}/{}", 0, INFO.spindle_units, INFO.spindle_per_units))
        self.actual_spindlerate.setObjectName("lbl_main_screen_spindleactual")
        self.spindle_override = QLabel(_("SO: {}%", 100))
        self.spindle_override.setObjectName("lbl_main_screen_spindleoverride")
        v1.addWidget(self.actual_spindlerate)
        v1.addWidget(self.spindle_override)
        self.setLayout(v1)
        UPDATER.signal("spindle", self.on_spindle_changed)
        #UPDATER.signal("spindleoverride", self.on_spindlerate_changed)
        #UPDATER.signal("spindle_speed", self.on_actualrate_changed)
        UPDATER.signal("feed_mode", self.on_feedmode_changed)

    def on_spindle_changed(self, spindles):
        for spindle in spindles:
            self.on_spindlerate_changed(spindle["override"])
            self.on_actualrate_changed(spindle["speed"])
            break

    def on_feedmode_changed(self, mode):
        self.spindle_override.setVisible(False if mode == 'G96' else True)

    def on_actualrate_changed(self, speed):
        self.actual_spindlerate.setText(
            _("Actual: {:.2f} {}/{}", speed, INFO.spindle_units, INFO.spindle_per_units))

    def on_spindlerate_changed(self, speed):
        self.spindle_override.setText(_("SO: {}%", speed*100))

class FeedWidget(QGroupBox):
    def __init__(self, parent=None):
        QGroupBox.__init__(self, parent)
        self.setTitle(_("Feedrate"))
        v1 = QVBoxLayout()
        self.actual_feedrate = QLabel(_("Actual: {:.2f}", 0))
        self.actual_feedrate.setObjectName("lbl_main_screen_feedactual")
        self.feed_override = QLabel(_("FO: {}%", 100))
        self.feed_override.setObjectName("lbl_main_screen_feedoverride")
        self.rapid_override = QLabel(_("RO: {}%", 100))
        self.rapid_override.setObjectName("lbl_main_screen_rapidoverride")
        v1.addWidget(self.actual_feedrate)
        v1.addWidget(self.feed_override)
        v1.addWidget(self.rapid_override)
        self.setLayout(v1)
        UPDATER.signal("feedrate", self.on_feedrate_changed)
        UPDATER.signal("rapidrate", self.on_rapidrate_changed)
        UPDATER.signal("current_vel", self.on_actualrate_changed)
        UPDATER.signal("feed_mode", self.on_feedmode_changed)
        UPDATER.signal("update_feed_labels", self.update_labels)

    def update_labels(self, data):
        self.on_actualrate_changed(STAT.current_vel)

    def on_feedmode_changed(self, mode):
        if mode == 'G93':
            self.feed_override.setVisible(False)
            self.rapid_override.setVisible(False)
        else:
            self.feed_override.setVisible(True)
            self.rapid_override.setVisible(True)

    def on_actualrate_changed(self, feed):
        self.actual_feedrate.setText(
            _("Actual: {:.2f} {}/{}", feed*60, INFO.linear_units, INFO.feed_per_units))

    def on_feedrate_changed(self, feed):
        self.feed_override.setText(_("FO: {}%", feed*100))

    def on_rapidrate_changed(self, rapid):
        self.rapid_override.setText(_("RO: {}%", rapid*100))

class JOGWidget(QGroupBox):
    def __init__(self, parent=None):
        QGroupBox.__init__(self, parent)

        UPDATER.signal("task_mode", self.task_mode_handler)

        self.activate = [_("Disactivated"), _("Activated")]
        self.mode = [_("Increment"), _("Continuous")]
        self.device = [_("Joystick"), _("Encoder")]

        self.jog_activate = 0
        self.jog_mode = 0
        self.jog_device = 0
        self.jog_increment = 0
        self.jog_speed = 0

        UPDATER.add('jog_speed')
        UPDATER.add('jog_increment')
        UPDATER.add('jog_activate')
        UPDATER.add('jog_continuous')
        UPDATER.add('jog_encoder')
        UPDATER.add('jog_fast')       

        self.setTitle(_("JOG"))
        hlay = QHBoxLayout()

        v1 = QVBoxLayout()
        self.label_jog_speed = QLabel(_("Speed: {:.2f}", self.jog_speed))
        self.label_jog_speed.setObjectName("lbl_main_screen_jogspeed")
        self.label_jog_increment = QLabel(
            _("Increment: {}", self.jog_increment))
        self.label_jog_increment.setObjectName("lbl_main_screen_jogincrement")
        v1.addWidget(self.label_jog_speed)
        v1.addWidget(self.label_jog_increment)
        hlay.addLayout(v1)

        hlay.addWidget(VSeparator())

        v2 = QVBoxLayout()
        self.label_jog_activate = QLabel(
            _("JOG ")+self.activate[self.jog_activate])
        self.label_jog_activate.setObjectName("lbl_main_screen_jogactivate")
        self.label_jog_mode = QLabel(_("Mode: ")+self.mode[self.jog_mode])
        self.label_jog_mode.setObjectName("lbl_main_screen_jogmode")
        self.label_jog_device = QLabel(
            _("Device: ")+self.device[self.jog_device])
        self.label_jog_device.setObjectName("lbl_main_screen_jogdevice")
        v2.addWidget(self.label_jog_activate)
        v2.addWidget(self.label_jog_mode)
        v2.addWidget(self.label_jog_device)
        hlay.addLayout(v2)

        self.setLayout(hlay)

        UPDATER.signal("jog_activate", self.on_active_changed)
        UPDATER.signal("jog_continuous", self.on_mode_changed)
        UPDATER.signal("jog_encoder", self.on_device_changed)
        UPDATER.signal("jog_increment", self.on_increment_changed)
        UPDATER.signal("jog_speed", self.on_speed_changed)

    def on_speed_changed(self, s):
        self.jog_speed = s
        self.label_jog_speed.setText(_("Speed: {}%", self.jog_speed*100))

    def on_increment_changed(self, i):
        self.jog_increment = i
        self.label_jog_increment.setText(
            _("Increment: {}", self.jog_increment))

    def on_active_changed(self, active):
        self.jog_activate = active
        self.label_jog_activate.setText(
            _("JOG ")+self.activate[self.jog_activate])

    def on_mode_changed(self, mode):
        self.jog_mode = mode
        self.label_jog_mode.setText(_("Mode: ")+self.mode[self.jog_mode])

    def on_device_changed(self, encoder):
        self.jog_device = encoder
        self.label_jog_device.setText(
            _("Device: ")+self.device[self.jog_device])

    def task_mode_handler(self, data):
        if data == LINUXCNC.MODE_MANUAL:
            self.setVisible(True)
        else:
            self.setVisible(False)

class AxisWidget(QGroupBox):
    def __init__(self, parent=None):
        QGroupBox.__init__(self, parent)
        self.setTitle(_("Axis"))
        h1 = QHBoxLayout()
        self.drolabel = QLabel(" ".join(INFO.coordinates))
        self.drolabel.setObjectName("lbl_main_screen_dro_all")
        h1.addWidget(self.drolabel)
        self.setLayout(h1)
        
        UPDATER.signal(INFO.axes_list, lambda axis: self.update_position(axis))
        UPDATER.signal("task_mode", self.task_mode_handler)
        UPDATER.signal("diameter_multiplier", self.diameter_mode)
        UPDATER.signal("update_feed_labels", 
            lambda stat: self.update_position(getattr(STAT,INFO.axes_list)))

    def diameter_mode(self, data):
        self.update_position(getattr(STAT,INFO.axes_list))

    def update_position(self, stat):
        text = ""
        for i, axis in enumerate(INFO.coordinates):
            #position=stat[i]['input'] is absolute

            if INFO.feedback_actual:
                position = stat[i]['input']
            else:
                position = stat[i]['output']
                
            position -= STAT.g5x_offset[i] + STAT.tool_offset[i] + \
                STAT.g92_offset[i]

            position *= INFO.units_factor

            if axis == 'X' and INFO.machine_is_lathe:
                text += '{}{}:'.format(axis, 
                    ['', 'R', 'D'][UPDATER.diameter_multiplier]) + \
                    INFO.dro_format.format(
                        position*UPDATER.diameter_multiplier)+'  '
            else:
                text += '{}:'.format(axis) + \
                    INFO.dro_format.format(position)+'  '

        self.drolabel.setText(text)

    def task_mode_handler(self, data):
        if data == LINUXCNC.MODE_MANUAL:
            self.setVisible(False)
        else:
            self.setVisible(True)

class MainLayout(QVBoxLayout):
    def __init__(self, parent=None):
        QVBoxLayout.__init__(self, parent)

        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(2)

        h1 = QHBoxLayout()

        self.leftLayout = QVBoxLayout()
        self.leftLayout.setContentsMargins(0, 0, 0, 0)
        self.leftLayout.setSpacing(2)

        self.rightLayout = QVBoxLayout()
        self.rightLayout.setContentsMargins(0, 0, 0, 0)
        self.rightLayout.setSpacing(2)

        h2 = QHBoxLayout()
        h2.setContentsMargins(5, 0, 5, 5)

        self.centralWidgets = QStackedWidget()
        h2.addWidget(self.centralWidgets, 3)

        infoLayout = QVBoxLayout()

        axis_widget = AxisWidget()
        infoLayout.addWidget(axis_widget)

        jog_widget = JOGWidget()
        infoLayout.addWidget(jog_widget)

        feedrate_widget = FeedWidget()
        infoLayout.addWidget(feedrate_widget)

        spindle_widget = SpindleWidget()
        infoLayout.addWidget(spindle_widget)

        active_codes_widget = GCodeWidget()
        infoLayout.addWidget(active_codes_widget)

        tool_widget = ToolWidget()
        infoLayout.addWidget(tool_widget)

        infoLayout.addStretch()

        infoWidget = QWidget()
        infoWidget.setLayout(infoLayout)

        infoScroll = QScrollArea()
        infoScroll.setWidget(infoWidget)
        infoScroll.setWidgetResizable(True)
        
        h2.addWidget(infoScroll, 2)

        def setFullscreen(state):
            if state:
                h2.setStretch(1,0)
                infoScroll.setVisible(False)
            else:
                h2.setStretch(1,2)
                infoScroll.setVisible(True)
                
        UPDATER.add("mainscreen_full")
        UPDATER.signal("mainscreen_full",setFullscreen)

        h1.addLayout(self.leftLayout, 1)
        h1.addLayout(h2, 9)
        h1.addLayout(self.rightLayout, 1)
        self.addLayout(h1, 6)

        self.bottomWidgets = QStackedWidget()
        UPDATER.add("secondary_mode")
        self.bottomWidgets.currentChanged.connect(
            lambda i: UPDATER.emit("secondary_mode", i))
        self.addWidget(self.bottomWidgets, 1)
