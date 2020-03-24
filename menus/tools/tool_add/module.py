#!/usr/bin/env python
# -*- coding:UTF-8 -*-

import time,os

from qtvcp import logger
_logger = logger.getLogger(__name__)

from PyQt5 import QtCore, QtWidgets,QtGui

from qtvcp.core import Tool

TOOL = Tool()

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
        _logger.info( "Button ToolAdd clicked")
        newtool = [-99, 0,'0','0','0','0','0','0','0','0','0','0','0','0', 0,0,0,0,'New Tool']
        array = self.that.widgets.tooloffsetview.tablemodel.arraydata
        array_len = len(array)

        array.insert(0, newtool)
        error = TOOL.SAVE_TOOLFILE(TOOL.CONVERT_TO_STANDARD_TYPE(array))

        self.that.widgets.tooloffsetview.createAllView()

        if array_len == 0:
            self.that.widgets.tooloffsetview._hal_init()

        self.that.widgets.tooloffsetview.setFocus()

