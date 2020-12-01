#!/usr/bin/env python
# -*- coding:UTF-8 -*-# -*- coding: utf-8 -*-
#
# AlterX GUI - jog tab
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

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *
from alterx.gui.util import *
from alterx.core.linuxcnc import *

from functools import partial

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
        UPDATER.signal("diameter_multiplier", self.diameter_mode)
        UPDATER.signal("update_feed_labels", 
            lambda stat: self.update_position(getattr(STAT,INFO.axes_list)))

    def diameter_mode(self, data):
        self.update_position(getattr(STAT,INFO.axes_list))

    def update_position(self, stat):
        #if self.drolabel.visibleRegion().isEmpty():
		#	return
    
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

class func(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)

        self.centralwidget = QWidget(self)
        vlay = QVBoxLayout(self.centralwidget)
        vlay.addWidget(AxisWidget())
        layout = QGridLayout()

        def safe_get_label(index):
            if index<len(INFO.coordinates):
                return INFO.coordinates[index]
            else:
                return ' '

        labels = [safe_get_label(3)+"+",safe_get_label(1)+"+",safe_get_label(2)+"+",
                safe_get_label(0)+"-"," ",safe_get_label(0)+"+",
                safe_get_label(2)+"-",safe_get_label(1)+"-",safe_get_label(3)+"-",]

        for i in range(3):
            for j in range(3):
                num = i*3+j
                pb = QPushButton(labels[num])
                if num < 4:
                    num = num +1
                pb.pressed.connect(partial(self.btn_pressed,num))
                pb.released.connect(partial(self.btn_released,num))
                layout.addWidget(pb,i,j)

        for i in range(3):
            pb = QPushButton(str((i+1)*30)+"%")
            pb.clicked.connect(partial(self.btn_jog_speed,(i+1)*3/10))
            layout.addWidget(pb,3,i)
        
        vlay.addLayout(layout)
        vlay.addStretch()
        self.setCentralWidget(self.centralwidget)
        self.show()
    
    def btn_jog_speed(self,value):
        UPDATER.emit('jog_speed',value)

    def btn_pressed(self, btn):
        UPDATER.set("jog_screen",1)
        UPDATER.emit("display_button_binding", btn)

    def btn_released(self, btn):
        UPDATER.set("jog_screen",1)
        UPDATER.emit("display_button_binding", 0)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = func()
    sys.exit(app.exec_())
