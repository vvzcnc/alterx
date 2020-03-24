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

    def execute(self):
        _logger.info( "Button Run from line clicked" )

        okPressed = self.that.dialogs.getInteger("Enter value", "Enter line number")
        if okPressed != None:
            self.that.start_line = okPressed
            self.that.command.auto( linuxcnc.AUTO_RUN, self.that.start_line )

    def update(self):
        if self.that.stat.interp_state == linuxcnc.INTERP_IDLE:
            self.button.setEnabled(True)
        else:
            self.button.setEnabled(False)