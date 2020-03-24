#!/usr/bin/env python
# -*- coding:UTF-8 -*-

import time,os

from qtvcp import logger
_logger = logger.getLogger(__name__)

from PyQt5 import QtCore, QtWidgets,QtGui

class func:
    def __init__(self,button,that):
        self.that = that
        self.button = button

        self.update_image(False)

    def update_image(self,state):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if state:
            if os.path.isfile("%s/icon_on.png"%dir_path):
                self.button.setStyleSheet("image:url('%s/icon_on.png')"%dir_path)
            else:
                self.button.setStyleSheet("color:black")
        else:
            if os.path.isfile("%s/icon.png"%dir_path):
                self.button.setStyleSheet("image:url('%s/icon.png')"%dir_path)
            else:
                self.button.setStyleSheet("color:black")

    def execute(self):
        if self.that.jog.jog_continuous:
            _logger.info( "JOG incremental" )
            self.that.jog.jog_continuous = 0
        else:
            _logger.info( "JOG continuous" )
            self.that.jog.jog_continuous = 1

        self.update_image(self.that.jog.jog_continuous)

    def update(self):
        self.update_image(self.that.jog.jog_continuous)

