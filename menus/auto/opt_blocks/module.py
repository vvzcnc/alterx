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

        self.update_image(self.that.stat.block_delete)
        self.button.setCheckable(True)
        self.button.setChecked(self.that.stat.block_delete)

        if self.that.prefs.getpref( "block_delete", False, bool ):
            self.that.command.set_block_delete( True )
        else:
            self.that.command.set_block_delete( False )

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
        _logger.info( "Button Optional Blocks clicked" )
        if self.that.stat.block_delete:
            self.that.command.set_block_delete( False )
        else:
            self.that.command.set_block_delete( True )

        self.that.stat.poll()

        self.that.prefs.putpref( "block_delete", self.that.stat.block_delete, bool)

        self.update_image(self.that.stat.block_delete)

    def update(self):
        self.update_image(self.that.stat.block_delete)
        self.button.setChecked(self.that.stat.block_delete)
