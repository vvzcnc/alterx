#!/usr/bin/env python
# -*- coding:UTF-8 -*-

import time,os

from qtvcp import logger
_logger = logger.getLogger(__name__)

class func:
    def __init__(self,button,that):
        self.that = that
        self.button = button

        dir_path = os.path.dirname(os.path.realpath(__file__))
        if os.path.isfile("%s/icon.png"%dir_path):
            self.button.setStyleSheet("image:url('%s/icon.png')"%dir_path)
        else:
            self.button.setStyleSheet("color:black")

    def execute(self):
        _logger.info( "Command Home A" )
        self.that.command.home(3)

