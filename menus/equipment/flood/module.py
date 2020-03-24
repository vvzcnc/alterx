#!/usr/bin/env python
# -*- coding:UTF-8 -*-

import os,linuxcnc

from qtvcp import logger
_logger = logger.getLogger(__name__)

class func:
    def __init__(self,button,that):
        self.that = that
        self.button = button

        self.update_image(self.that.stat.flood)

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
        if self.that.stat.flood:
            _logger.info( "Flood disactivated" )
            self.that.command.flood( linuxcnc.FLOOD_OFF )
        else:
            _logger.info( "Flood activated" )
            self.that.command.flood( linuxcnc.FLOOD_ON )

    def update(self):
        self.update_image(self.that.stat.flood)
