# -*- coding: utf-8 -*-
#
# AlterX GUI - notify
#
# Copyright 2020-2020 uncle-yura uncle-yura@tuta.io
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

from __future__ import division, absolute_import, print_function, unicode_literals

__all__ = ['Notify']

from alterx.common.compat import *
from alterx.gui.util import *

MESSAGES = []

def close_messages(msgs):
    for w in reversed(msgs):
        try:
            if w.isVisible():
                w.deleteLater()
        except:
            MESSAGES.remove(w)
        else:
            MESSAGES.remove(w)
    return 0

def count_messages():
    count = 0
    for w in reversed(MESSAGES):
        try:
            if w.isVisible():
                count = count + 1
        except:
            MESSAGES.remove(w)
    return count
    
def get_pos(widget):
    count_messages()
    for i,w in enumerate(MESSAGES):
        if widget == w:
            return i   
    return 0
    
class Notify(QLabel):
    def __init__(self,msg,delay=None,parent=None):
        QLabel.__init__(self,msg,parent)
        self.width = 300
        self.height = 75
        
        self.setWindowFlags(Qt.ToolTip)
        #self.setAttribute(Qt.WA_NoSystemBackground,True)
        #self.setAttribute(Qt.WA_TranslucentBackground,True)
        #self.setWindowOpacity(0.2)
        #self.setAutoFillBackground(False)

        self.resize(self.width, self.height)
        self.setStyleSheet("background-color: gray;"
                "font-size: 15pt;")
        self.setWordWrap(True)
        self.show()
        
        desktop = QApplication.desktop()
        screen = desktop.screenNumber(QCursor.pos())
        self.rect = desktop.screenGeometry(screen)
        self.move_down()
        
        self.mousePressEvent = lambda w: self.deleteLater()
        if delay:
            QTimer.singleShot(delay,self.deleteLater)     
        
        updater = QTimer(self)
        updater.start(500)
        updater.timeout.connect(self.move_up) 
    
    def move_up(self):
        pos = get_pos(self)
        self.move(self.rect.width()*0.1,
                    self.rect.height()*0.05+(self.height+5)*pos)

    def move_down(self):
        count = count_messages()
        self.move(self.rect.width()*0.1,
                    self.rect.height()*0.05+(self.height+5)*count)

    @classmethod    
    def Info(cls,msg):
        count = count_messages()
        if count > 9:
            close_messages([MESSAGES[0]])
        MESSAGES.append(Notify(" <span style='color:white;'>[i]:</span> "+str(msg),5000))
        
    @classmethod    
    def Warning(cls,msg):
        count = count_messages()
        if count > 9:
            close_messages([MESSAGES[0]])
        MESSAGES.append(Notify(" <span style='color:yellow;'>[w]:</span> "+str(msg),10000))
        
    @classmethod    
    def Error(cls,msg):
        count = count_messages()
        if count > 9:
            close_messages([MESSAGES[0]])
        MESSAGES.append(Notify(" <span style='color:red;'>[e]:</span> "+str(msg)))

    @classmethod    
    def closeAll(cls):
        close_messages(MESSAGES)
            
    @classmethod   
    def count(cls):
        return count_messages()
        