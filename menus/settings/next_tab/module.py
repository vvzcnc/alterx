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

        dir_path = os.path.dirname(os.path.realpath(__file__))
        if os.path.isfile("%s/icon.png"%dir_path):
            self.button.setStyleSheet("image:url('%s/icon.png')"%dir_path)
        else:
            self.button.setStyleSheet("color:black")
            self.button.setText("")

    def execute(self):
        _logger.info( "Button NextTab clicked")
        
        if self.that.widgets.tabSettings.currentIndex() < 0 :
            self.that.widgets.tabSettings.setCurrentIndex(0)
        elif self.that.widgets.tabSettings.currentIndex() == self.that.widgets.tabSettings.count()-1:
            self.that.widgets.tabSettings.setCurrentIndex(0)
        else:
            self.that.widgets.tabSettings.setCurrentIndex(self.that.widgets.tabSettings.currentIndex()+1)

