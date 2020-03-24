#!/usr/bin/env python
# -*- coding:UTF-8 -*-

import time,os,sys

import linuxcnc

from qtvcp import logger
_logger = logger.getLogger(__name__)

from PyQt5 import QtCore, QtWidgets,QtGui

class func:
    def __init__(self,button,that):
        self.x = 0
        self.that = that
        self.button = button

        dir_path = os.path.dirname(os.path.realpath(__file__))
        if os.path.isfile("%s/icon.png"%dir_path):
            self.button.setStyleSheet("image:url('%s/icon.png')"%dir_path)
        else:
            self.button.setStyleSheet("color:black")

    def execute(self):
        _logger.info( "Button Edit clicked" )

        self.that.edit_tbtn_clicked()
        self.that.widgets.gcode_editor.editMode()

