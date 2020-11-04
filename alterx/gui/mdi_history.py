# -*- coding: utf-8 -*-
#
# AlterX GUI - mdi history
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

__all__ = ['MDIHistory']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

from alterx.gui.util import *
from alterx.core.linuxcnc import *


class MDI(QLineEdit):
    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)
        self.mdi_history_file = INFO.mdi_history_file
        self.parent = parent
        #self.returnPressed.connect(lambda: self.submit())
        
    def submit(self):
        text = str(self.text()).rstrip()
        if text == '':
            return

        COMMAND.mdi(text+'\n')
        printVerbose(_("MDI: {}",text))
        try:
            fp = os.path.expanduser(self.mdi_history_file)
            fp = open(fp, 'a')
            fp.write(text + "\n")
            fp.close()
        except:
            pass


class MDIHistory(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setMinimumSize(QSize(200, 150))

        lay = QVBoxLayout()
        lay.setContentsMargins(0, 0, 0, 0)
        self.setLayout(lay)

        self.list = QListView()
        self.list.setEditTriggers(QListView.NoEditTriggers)
        self.list.activated.connect(self.activated)
        self.list.setAlternatingRowColors(True)
        self.list.selectionChanged = self.selectionChanged
        self.model = QStandardItemModel(self.list)

        self.MDI = MDI()
        self.MDI.installEventFilter(self)
        
        self.set_focus = self.MDI.setFocus
        
        lay.addWidget(self.list)
        lay.addWidget(self.MDI)

        self.fp = self.MDI.mdi_history_file
        self.reload()
        self.select_row('last')

        UPDATER.add("mdi_run_command")
        UPDATER.signal("mdi_run_command", lambda s: self.run_command())

    def eventFilter(self, source, event):
        if ( event.type() == QEvent.KeyPress ):
            if event.key() == Qt.Key_Up:
                 self.line_up()
            elif event.key() == Qt.Key_Down:
                self.line_down()
            elif event.key() == Qt.Key_Return:
                self.MDI.submit()
                self.model.appendRow(QStandardItem(self.MDI.text()))
            #else:
            #    self.MDI.setFocus()
                
        return QWidget.eventFilter(self, source, event)

    def reload(self, w=None):
        self.model.clear()
        try:
            with open(self.fp, 'r') as inputfile:
                for line in inputfile:
                    line = line.rstrip('\n')
                    item = QStandardItem(line)
                    self.model.appendRow(item)
        except:
            printDebug(_('MDI history file path is not valid: {}', self.fp))

        self.list.setModel(self.model)
        self.list.scrollToBottom()
        if self.MDI.hasFocus():
            self.select_row('last')            

    def selectionChanged(self, old, new):
        cmd = self.getSelected()
        self.MDI.setText(cmd)
        selectionModel = self.list.selectionModel()
        if selectionModel.hasSelection():
            self.row = selectionModel.currentIndex().row()

    def getSelected(self):
        selected_indexes = self.list.selectedIndexes()
        selected_rows = [item.row() for item in selected_indexes]
        # iterates each selected row in descending order
        for selected_row in sorted(selected_rows, reverse=True):
            text = self.model.item(selected_row).text()
            return text

    def activated(self):
        cmd = self.getSelected()
        self.MDI.setText(cmd)
        self.MDI.submit()
        self.model.appendRow(QStandardItem(cmd))
        # self.select_row('down')

    def run_command(self):
        self.MDI.submit()
        self.select_row('last')

    def select_row(self, style):
        style = style.lower()
        selectionModel = self.list.selectionModel()
        parent = QModelIndex()
        self.rows = self.model.rowCount(parent) - 1
        if style == 'last':
            self.row = self.rows
        elif style == 'up':
            if self.row > 0:
                self.row -= 1
            else:
                self.row = 0
        elif style == 'down':
            if self.row < self.rows:
                self.row += 1
            else:
                self.row = self.rows
        else:
            return
        top = self.model.index(self.row, 0, parent)
        bottom = self.model.index(self.row, 0, parent)
        selectionModel.setCurrentIndex(
            top, QItemSelectionModel.Select | QItemSelectionModel.Rows)
        selection = QItemSelection(top, top)
        selectionModel.clearSelection()
        selectionModel.select(selection, QItemSelectionModel.Select)

    def line_up(self):
        self.select_row('up')

    def line_down(self):
        self.select_row('down')
