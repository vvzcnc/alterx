#!/usr/bin/env python
# -*- coding:UTF-8 -*-

import time,os,linuxcnc

from qtvcp import logger
_logger = logger.getLogger(__name__)

from PyQt5 import QtCore, QtWidgets,QtGui

class func:
    def __init__(self,button,that):
        self.that = that
        self.button = button

        dir_path = os.path.dirname(os.path.realpath(__file__))
        if os.path.isfile("%s/icon.png"%dir_path):
            self.button.setStyleSheet("image:url('%s/icon.png')"%dir_path)
        else:
            self.button.setStyleSheet("color:black")
            self.button.setText("")

        self.button.setCheckable(True)

    def execute(self):
        _logger.info( "Button Pause clicked" )
        if self.that.stat.interp_state == linuxcnc.INTERP_PAUSED:
            self.that.command.auto(linuxcnc.AUTO_RESUME)
        else:
            self.that.command.auto( linuxcnc.AUTO_PAUSE )

    def update(self):
        if self.that.stat.interp_state == linuxcnc.INTERP_PAUSED:
            self.button.setChecked(True)
        else:
            self.button.setChecked(False)
