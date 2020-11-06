# -*- coding: utf-8 -*-
#
# AlterX GUI - gcode editor
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

__all__ = ['GcodeWidget', 'GcodeEditor']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

from alterx.gui.util import *
from alterx.core.linuxcnc import *

class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        QSyntaxHighlighter.__init__(self, parent)

        self.set_gcode_lexer()

    def set_gcode_lexer(self):               
        self.regexp_by_format = dict()

        #Comment
        char_format = QTextCharFormat()
        char_format.setFontWeight(QFont.Normal)
        char_format.setForeground(Qt.darkGray)
        self.Comment = char_format
                
        #Text
        char_format = QTextCharFormat()
        char_format.setFontWeight(QFont.Normal)
        char_format.setForeground(Qt.black)
        self.Text = char_format
        
        #Error
        char_format = QTextCharFormat()
        char_format.setFontWeight(QFont.Normal)
        char_format.setForeground(Qt.red)
        self.Error = char_format
        
        #Info
        char_format = QTextCharFormat()
        char_format.setFontWeight(QFont.Bold)
        char_format.setForeground(Qt.darkBlue)
        self.Info = char_format
        
        #Words
        char_format = QTextCharFormat()
        char_format.setFontWeight(QFont.Bold)
        char_format.setForeground(Qt.darkMagenta)
        self.Words = char_format
                
        self.regexp_by_format[r'\((.*?)\)|^;.*'] = self.Comment
        #self.regexp_by_format[r'\[(.*?)\]'] = self.Text
        self.regexp_by_format[r'\<(.*?)\>'] = self.Info
        self.regexp_by_format[r'#|msg|debug'] = self.Error
        self.regexp_by_format[r'(?<!\()[a-zA-Z](?![^\(]*[\)])'] = self.Words

    def highlightBlock(self, text):
        for regexp, char_format in self.regexp_by_format.items():
            expression = QRegularExpression(regexp)
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), char_format)
        
class EditorBase(QTextEdit):
    def __init__(self, parent=None):
        QTextEdit.__init__(self, parent)

        self.setReadOnly(True)
        self.filepath = None
        self.highlighter = CodeHighlighter(self)
        self.modified = False
        
        self.textChanged.connect(lambda: self.setModified(True))
        
    def setCursorPosition(self,line,pos):
        block = self.document().findBlockByLineNumber(line-1)
        cursor = self.textCursor()
        cursor.setPosition(block.position())
        self.setFocus()
        self.setTextCursor(cursor)
       
    def markerAdd(self,line):
        block = self.document().findBlockByLineNumber(line-1)
        fmt = QTextBlockFormat()
        fmt.setBackground(Qt.yellow)
        QTextCursor(block).setBlockFormat(fmt)
        
    def markerDelete(self,line):
        block = self.document().findBlockByLineNumber(line-1)
        fmt = QTextBlockFormat()
        fmt.setBackground(Qt.white)
        QTextCursor(block).setBlockFormat(fmt)
        
    def setModified(self,mod):
        self.modified = mod
        
    def lines(self):
        return self.document().lineCount()

    def new_text(self):
        self.setText('')

    def load_text(self, filepath):
        self.filepath = filepath
        try:
            fp = os.path.expanduser(filepath)
            self.setText(open(fp).read())
        except:
            printError(_('File path is not valid: {}', filepath))
            self.setText('')
            return
        self.ensureCursorVisible()
        self.setModified(False)
        
    def save_text(self):
        with open(self.filepath, "w") as text_file:
            text_file.write(self.toPlainText())
        self.setModified(False)

    def replace_text(self, text):
        self.replace(text)

    def search(self, text, re=False, case=False, word=False, wrap=False, fwd=True):
        self.findFirst(text, re, case, word, wrap, fwd)

    def search_next(self):
        self.findNext()


class GcodeDisplay(EditorBase):
    def __init__(self, parent=None):
        EditorBase.__init__(self, parent)
        self.last_line = 0

        UPDATER.add("file_reload")
        UPDATER.signal("file_reload", self.reload_program)

        UPDATER.signal("file", self.load_program)
        UPDATER.signal("motion_line", self.highlight_line)

    def reload_program(self, state):
        self.load_program(self.filepath)

    def load_program(self, filename=None):
        self.load_text(filename)
        self.setCursorPosition(0, 0)
        self.setModified(False)

    def highlight_line(self, line):
        if ( STAT.interp_state != LINUXCNC.INTERP_IDLE or 
            STAT.interp_state != LINUXCNC.INTERP_PAUSED ):
            self.emit_percent(line*100/self.lines())

        if STAT.interp_state != LINUXCNC.INTERP_IDLE:
            self.markerAdd(line)
            
        if self.last_line:
            self.markerDelete(self.last_line)
            
        self.setCursorPosition(line, 0)
        self.ensureCursorVisible()
        self.last_line = line

    def emit_percent(self, percent):
        pass

    def emit_file(self, filename, lines):
        pass


class GcodeWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        self.editor = GcodeDisplay()
        self.editor.setObjectName("edit_gcode_widget")
        lay.addWidget(self.editor)
        self.setLayout(lay)

        gbox = QGroupBox()
        lay.addWidget(gbox)
        gbox.setTitle(_("Program"))

        vlay = QVBoxLayout()
        gbox.setLayout(vlay)
        self.filename = QLabel(_("Filename: "))
        self.filename.setObjectName("lbl_gwidget_filename")
        vlay.addWidget(self.filename)

        hlay = QHBoxLayout()
        vlay.addLayout(hlay)
        self.lines = QLabel(_("Lines: "))
        self.lines.setObjectName("lbl_geditor_lines")
        hlay.addWidget(self.lines)
        self.progress = QLabel(_("Progress: "))
        self.progress.setObjectName("lbl_gwidget_progress")
        hlay.addWidget(self.progress)

        self.editor.emit_percent = self.emit_percent
        self.editor.emit_file = self.emit_file

    def emit_percent(self, percent):
        self.progress.setText(_('Progress: {:2.2f}%', percent))

    def emit_file(self, fn, ln):
        self.filename.setText(_('Filename: {}', fn))
        self.lines.setText(_('Lines: {}', ln))


class GcodeEditor(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.setMinimumSize(QSize(300, 200))

        lay = QVBoxLayout()
        lay.setContentsMargins(0, 0, 0, 0)

        self.editor = GcodeDisplay(self)
        self.editor.setReadOnly(False)
        self.editor.setModified(False)
        self.editor.setObjectName("edit_gcode_editor")
        lay.addWidget(self.editor)

        gbox = QGroupBox()
        lay.addWidget(gbox)
        gbox.setTitle(_("Editor"))
        vlay = QVBoxLayout()
        gbox.setLayout(vlay)

        self.filename = QLabel(_("Filename: "))
        self.filename.setObjectName("lbl_geditor_filename")
        vlay.addWidget(self.filename)

        hlay = QHBoxLayout()
        vlay.addLayout(hlay)

        self.search = ""
        self.replace = ""

        self.search_label = QLabel(_("Search: {}", self.search))
        self.search_label.setObjectName("lbl_geditor_search")
        hlay.addWidget(self.search_label)
        self.replace_label = QLabel(_("Replace: {}", self.replace))
        self.replace_label.setObjectName("lbl_geditor_replace")
        hlay.addWidget(self.replace_label)

        self.setLayout(lay)

        self.editor.emit_file = self.emit_file

        UPDATER.add("geditor_new")
        UPDATER.add("geditor_save")
        UPDATER.add("geditor_undo")
        UPDATER.add("geditor_redo")
        UPDATER.add("geditor_search")
        UPDATER.add("geditor_replace")
        UPDATER.add("geditor_set_search")
        UPDATER.add("geditor_set_replace")

        UPDATER.signal("geditor_save", self.save_file)
        UPDATER.signal("geditor_new", lambda s: self.new_file())
        UPDATER.signal("geditor_undo", lambda s: self.editor.undo())
        UPDATER.signal("geditor_redo", lambda s: self.editor.redo())
        UPDATER.signal("geditor_search", lambda s: self.editor.search_next())
        UPDATER.signal("geditor_replace",
                        lambda s: self.editor.replace_text(self.replace))
        UPDATER.signal("geditor_set_search", self.set_search)
        UPDATER.signal("geditor_set_replace", self.set_replace)

    def save_file(self, path):
        if type(path) is not bool:
            self.editor.filepath = path
        try:
            self.editor.save_text()
        except Exception as e:
            printError(_('File save failed: {}', filename))
            Notify.Warning(_("Not saved"))
        else:
            Notify.Info(_("Saved"))

    def new_file(self):
        self.editor.filepath = None
        self.editor.new_text()
        self.filename.setText(_('Filename: {}', ""))

    def set_search(self, text):
        self.search = text
        self.search_label.setText(_("Search: {}", self.search))
        self.editor.search(self.search)

    def set_replace(self, text):
        self.replace = text
        self.replace_label.setText(_("Replace: {}", self.replace))

    def emit_file(self, fn, ln):
        self.filename.setText(_('Filename: {}', fn))
