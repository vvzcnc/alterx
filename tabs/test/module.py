#!/usr/bin/env python
# -*- coding:UTF-8 -*-

import time,os

from qtvcp import logger
_logger = logger.getLogger(__name__)

from PyQt5 import QtCore, QtWidgets,QtGui,uic

class func(QtWidgets.QMainWindow):

    def __init__(self,parent=None):
        super(func, self).__init__(parent)
        dir_path = os.path.dirname(os.path.realpath(__file__)) 
        uic.loadUi('%s/module.ui'%dir_path, self)

    def testButtonClicked(self):
        _logger.info("Button macro stop clicked")
        self.label.setText("123")
