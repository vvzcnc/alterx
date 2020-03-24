#!/usr/bin/env python
# -*- coding:UTF-8 -*-

import os,linuxcnc

from qtvcp import logger
_logger = logger.getLogger(__name__)

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
        if self.that.jog.jog_activate:
            _logger.info( "JOG disactivated" )
            self.that.jog.jog_activate = 0
        elif self.that.stat.task_state == linuxcnc.STATE_ON:
            _logger.info( "JOG activated" )
            self.that.jog.jog_activate = 1

        self.update_image(self.that.jog.jog_activate)

    def update(self):
        self.update_image(self.that.jog.jog_activate)
