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
        _logger.info( "Button ToolChange clicked" )

        selection = self.that.widgets.tooloffsetview.currentIndex()

        tool = self.that.widgets.tooloffsetview.tablemodel.arraydata[selection.row()][1]

        if tool == None:
            message = ( "you selected no or more than one tool, the tool selection must be unique" )
            self.that._warning_msg(message)
            return
        if tool == self.that.stat.tool_in_spindle:
            message = ( "Selected tool is already in spindle, no change needed." )
            self.that._warning_msg(message)
            return
        if tool or tool == 0:
            self.that.tool_change = True
            tool = int( tool )
            self.that.command.mode( linuxcnc.MODE_MDI )
            self.that.command.wait_complete()

            command = "M61 Q%s" % tool

            self.that.command.mdi( command )

            _logger.info( "Tool cmd: %s"%command )
        else:
            message = ( "Could not understand the entered tool number. Will not change anything" )
            self.that._warning_msg(message)

