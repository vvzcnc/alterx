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
        _logger.info( "Button Save clicked" )
        
        if self.that.widgets.gcode_editor.editor._last_filename:
            name = os.path.basename(self.that.widgets.gcode_editor.editor._last_filename)
            path = os.path.dirname(self.that.widgets.gcode_editor.editor._last_filename)
        else:
            name = self.that.dialogs.getText("Enter value", "Enter filename:")
            path = self.that.widgets.filemanager.model.filePath(self.that.widgets.filemanager.list.selectionModel().currentIndex())
            path = os.path.dirname(path)

        if name != None and name != "":

            if path == None or path == "":
                path = self.that.widgets.filemanager.default_path

            source = self.that.widgets.gcode_editor.editor.text()
            if len(name.split('.'))<2:
                name = name + '.ngc'

            try:
                outfile = open("%s/%s"%(path,name),'w')
                outfile.write(source)
            except Exception as e:
                _logger.error( "Save file error: %s"%e )
            finally:
                outfile.close()

            _logger.error( "path file error: %s"%path )
            _logger.error( "name file error: %s"%name )
            self.that._warning_msg("Saved to:%s/%s"%(" "+path,name+" "))

