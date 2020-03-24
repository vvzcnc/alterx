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
        _logger.info( "Button Delete clicked" )

        path = self.that.widgets.filemanager.model.filePath(self.that.widgets.filemanager.list.selectionModel().currentIndex())

        name = self.that.dialogs.getText("Delete file?", "Enter 'y' to delete file %s:" %path)
        if name == 'y':
            os.remove(path)

