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


class GcodeLexer(QsciLexerCustom):
    def __init__(self, parent=None):
        QsciLexerCustom.__init__(self, parent)
        self._styles = {
            0: 'Default',
            1: 'Comment',
            2: 'Key',
            3: 'Assignment',
            4: 'Value',
        }
        for key, value in self._styles.iteritems():
            setattr(self, value, key)
        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(12)
        font.setBold(True)
        self.setFont(font, 2)

    def language(self):
        return"G code"

    def description(self, style):
        if style < len(self._styles):
            description = _(
                "Custom lexer for the G code programming languages")
        else:
            description = ""
        return description

    # Paper sets the background color of each style of text
    def setPaperBackground(self, color, style=None):
        if style is None:
            for i in range(0, 5):
                self.setPaper(color, i)
        else:
            self.setPaper(color, style)

    def defaultColor(self, style):
        if style == self.Default:
            return QColor('#000000')  # black
        elif style == self.Comment:
            return QColor('#000000')  # black
        elif style == self.Key:
            return QColor('#0000CC')  # blue
        elif style == self.Assignment:
            return QColor('#CC0000')  # red
        elif style == self.Value:
            return QColor('#00CC00')  # green
        return QsciLexerCustom.defaultColor(self, style)

    def styleText(self, start, end):
        editor = self.editor()
        if editor is None:
            return

        # scintilla works with encoded bytes, not decoded characters.
        # this matters if the source contains non-ascii characters and
        # a multi-byte encoding is used (e.g. utf-8)
        source = ''
        if end > editor.length():
            end = editor.length()
        if end > start:
            if sys.hexversion >= 0x02060000:
                # faster when styling big files, but needs python 2.6
                source = bytearray(end - start)
                editor.SendScintilla(
                    editor.SCI_GETTEXTRANGE, start, end, source)
            else:
                source = unicode(editor.text()).encode('utf-8')[start:end]
        if not source:
            return

        # the line index will also be needed to implement folding
        index = editor.SendScintilla(editor.SCI_LINEFROMPOSITION, start)
        if index > 0:
            # the previous state may be needed for multi-line styling
            pos = editor.SendScintilla(
                editor.SCI_GETLINEENDPOSITION, index - 1)
            state = editor.SendScintilla(editor.SCI_GETSTYLEAT, pos)
        else:
            state = self.Default

        set_style = self.setStyling
        self.startStyling(start, 0x1f)

        # scintilla always asks to style whole lines
        for line in source.splitlines(True):
            length = len(line)
            graymode = False
            msg = (b'msg' in line.lower() or b'debug' in line.lower())
            for char in str(line):
                #print char
                if char == ('('):
                    graymode = True
                    set_style(1, self.Comment)
                    continue
                elif char == (')'):
                    graymode = False
                    set_style(1, self.Comment)
                    continue
                elif graymode:
                    if (msg and char.lower() in ('m', 's', 'g', ',', 'd', 'e', 'b', 'u')):
                        set_style(1, self.Assignment)
                        if char == ',':
                            msg = False
                    else:
                        set_style(1, self.Comment)
                    continue
                elif char in ('%', '<', '>', '#', '='):
                    state = self.Assignment
                elif char in ('[', ']'):
                    state = self.Value
                elif char.isalpha():
                    state = self.Key
                elif char.isdigit():
                    state = self.Default
                else:
                    state = self.Default
                set_style(1, state)

            # folding implementation goes here
            index += 1


class EditorBase(QsciScintilla):
    ARROW_MARKER_NUM = 8

    def __init__(self, parent=None):
        QsciScintilla.__init__(self, parent)
        # don't allow editing by default
        self.setReadOnly(True)
        # Set the default font
        self.font = QFont()
        self.font.setFamily('Courier')
        self.font.setFixedPitch(True)
        self.font.setPointSize(12)
        self.setFont(self.font)
        self.setMarginsFont(self.font)

        # Margin 0 is used for line numbers
        self.setMarginsFont(self.font)
        self.set_margin_width(7)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QColor("#cccccc"))

        # Clickable margin 1 for showing markers
        self.setMarginSensitivity(1, False)
        # setting marker margin width to zero make the marker highlight line
        self.setMarginWidth(1, 0)
        # self.matginClicked.connect(self.on_margin_clicked)
        self.markerDefine(QsciScintilla.Background, self.ARROW_MARKER_NUM)
        self.setMarkerBackgroundColor(QColor("#ffe4e4"), self.ARROW_MARKER_NUM)

        # Brace matching: enable for a brace immediately before or after
        # the current position
        #
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        # Current line visible with special background color
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#ffe4e4"))

        # Set custom gcode lexer
        self.set_gcode_lexer()

        # Don't want to see the horizontal scrollbar at all
        # Use raw message to Scintilla here (all messages are documented
        # here: http://www.scintilla.org/ScintillaDoc.html)
        #self.SendScintilla(QsciScintilla.SCI_SETHSCROLLBAR, 0)
        self.SendScintilla(QsciScintilla.SCI_SETSCROLLWIDTH, 700)
        self.SendScintilla(QsciScintilla.SCI_SETSCROLLWIDTHTRACKING)

        # default gray background
        self.set_background_color('#C0C0C0')

        # not too small
        self.setMinimumSize(200, 100)
        self.filepath = None

    def set_margin_width(self, width):
        fontmetrics = QFontMetrics(self.font)
        self.setMarginsFont(self.font)
        self.setMarginWidth(0, fontmetrics.width("0"*width) + 6)

    # must set lexer paper background color _and_ editor background color it seems
    def set_background_color(self, color):
        self.SendScintilla(QsciScintilla.SCI_STYLESETBACK,
                           QsciScintilla.STYLE_DEFAULT, QColor(color))
        self.lexer.setPaperBackground(QColor(color))

    def on_margin_clicked(self, nmargin, nline, modifiers):
        # Toggle marker for the line the margin was clicked on
        if self.markersAtLine(nline) != 0:
            self.markerDelete(nline, self.ARROW_MARKER_NUM)
        else:
            self.markerAdd(nline, self.ARROW_MARKER_NUM)

    def set_python_lexer(self):
        self.lexer = QsciLexerPython()
        self.lexer.setDefaultFont(self.font)
        self.setLexer(self.lexer)
        self.SendScintilla(QsciScintilla.SCI_STYLESETFONT, 1, 'Courier')

    def set_gcode_lexer(self):
        self.lexer = GcodeLexer(self)
        self.lexer.setDefaultFont(self.font)
        self.setLexer(self.lexer)
        self.set_background_color('#C0C0C0')

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
        self.SendScintilla(QsciScintilla.SCI_VERTICALCENTRECARET)
        self.setModified(False)

    def save_text(self):
        with open(self.filepath, "w") as text_file:
            text_file.write(self.text())

    def replace_text(self, text):
        self.replace(text)

    def search(self, text, re=False, case=False, word=False, wrap=False, fwd=True):
        self.findFirst(text, re, case, word, wrap, fwd)

    def search_next(self):
        self.SendScintilla(QsciScintilla.SCI_SEARCHANCHOR)
        self.findNext()


class GcodeDisplay(EditorBase):
    ARROW_MARKER_NUM = 8

    def __init__(self, parent=None):
        EditorBase.__init__(self, parent)

        self.last_line = 0

        UPDATER.connect("file", self.load_program)
        UPDATER.connect("motion_line", self.highlight_line)

    def load_program(self, filename=None):
        self.load_text(filename)
        # self.zoomTo(6)
        self.setCursorPosition(0, 0)
        self.setModified(False)

    def load_text(self, filename):
        if filename:
            try:
                fp = os.path.expanduser(filename)
                self.setText(open(fp).read())
                self.ensureCursorVisible()
                self.SendScintilla(QsciScintilla.SCI_VERTICALCENTRECARET)
                self.emit_file(filename, self.lines())
                return
            except:
                printError(_('File path is not valid: {}', filename))
        self.setText('')

    def highlight_line(self, line):
        if STAT.interp_state != LINUXCNC.INTERP_IDLE or STAT.interp_state != LINUXCNC.INTERP_PAUSED:
            self.emit_percent(line*100/self.lines())

        self.markerAdd(line, self.ARROW_MARKER_NUM)
        if self.last_line:
            self.markerDelete(self.last_line, self.ARROW_MARKER_NUM)
        self.setCursorPosition(line, 0)
        self.ensureCursorVisible()
        self.SendScintilla(QsciScintilla.SCI_VERTICALCENTRECARET)
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

        UPDATER.connect("geditor_save", self.save_file)
        UPDATER.connect("geditor_new", lambda s: self.new_file())
        UPDATER.connect("geditor_undo", lambda s: self.editor.undo())
        UPDATER.connect("geditor_redo", lambda s: self.editor.redo())
        UPDATER.connect("geditor_search", lambda s: self.editor.search_next())
        UPDATER.connect("geditor_replace",
                        lambda s: self.editor.replace_text(self.replace))
        UPDATER.connect("geditor_set_search", self.set_search)
        UPDATER.connect("geditor_set_replace", self.set_replace)

    def save_file(self, path):
        if type(path) is not bool:
            self.editor.filepath = path
        self.editor.save_text()

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
