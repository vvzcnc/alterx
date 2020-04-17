# -*- coding: utf-8 -*-
#
# AlterX GUI - file manager
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

__all__ = ['FileManager']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

from alterx.gui.util import *
from alterx.core.linuxcnc import *

class FileManager(QWidget):
        def __init__(self, parent=None):
                QWidget.__init__(self,parent)

		UPDATER.add("fileman_current_path")

                self.default_path = os.path.expanduser(INI.find("DISPLAY","PROGRAM_PREFIX") or "~/linuxcnc/nc_files/")
                self.user_path = os.path.expanduser(INI.find("DISPLAY","JUMP_TO") or "~/")

                self.currentPath = None

                self.setGeometry(10, 10, 640, 480)

                self.model = QFileSystemModel()
                self.model.setRootPath(QDir.currentPath())
                self.model.setFilter(QDir.AllDirs | QDir.NoDot | QDir.Files)
                self.model.setNameFilterDisables(False)
                self.model.setNameFilters(["*.ngc",'*.py'])

                self.list = QListView()
                self.list.setModel(self.model)
                self.updateDirectoryView(self.default_path)
                self.list.resize(640, 480)
                self.list.clicked[QModelIndex].connect(self.clicked)
                self.list.activated.connect(self.load)
                self.list.setAlternatingRowColors(True)

                self.cb = QComboBox()
                self.cb.currentTextChanged.connect(self.filterChanged)
                self.cb.addItems(sorted({'*.ngc','*.py','*'}))
                #self.cb.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

                hbox = QHBoxLayout()
                hbox.addWidget(self.cb)

                lay = QVBoxLayout()
		lay.setContentsMargins(0,0,0,0)
                lay.addWidget(self.list)
                lay.addLayout(hbox)
                self.setLayout(lay)

		UPDATER.add("fileman_prev")
		UPDATER.add("fileman_next")
		UPDATER.add("fileman_select")
		UPDATER.add("fileman_delete")
		UPDATER.add("fileman_home")
		UPDATER.add("fileman_jump")

		UPDATER.connect("fileman_prev",lambda s: self.up())
		UPDATER.connect("fileman_next",lambda s: self.down())
		UPDATER.connect("fileman_select",lambda s: self.load())
		UPDATER.connect("fileman_delete",lambda s: self.deleteSelected())
		UPDATER.connect("fileman_home",lambda s: self.updateDirectoryView(self.default_path))
		UPDATER.connect("fileman_jump",lambda s: self.updateDirectoryView(self.user_path))

        def deleteSelected(self):
		row = self.list.selectionModel().currentIndex()
		dir_path = self.model.filePath(row)
		try:
			if os.path.isfile(dir_path):
				os.remove(dir_path)
			else:
				os.rmdir(dir_path)
		except Exception as e:
			printError(_("Failed to delete path {}: {}",dir_path,e))

        def updateDirectoryView(self, path):
                self.list.setRootIndex(self.model.setRootPath(path))
		UPDATER.emit("fileman_current_path",path)

        def filterChanged(self, text):
                self.model.setNameFilters([text])

        def clicked(self, index):
                # the signal passes the index of the clicked item
                dir_path = self.model.filePath(index)
                if self.model.fileInfo(index).isFile():
                        self.currentPath = dir_path
                        return
                root_index = self.model.setRootPath(dir_path)
                self.list.setRootIndex(root_index)

        def select_row(self, style):
                style = style.lower()
                selectionModel = self.list.selectionModel()
                row = selectionModel.currentIndex().row()
                self.rows = self.model.rowCount(self.list.rootIndex())

                if style == 'last':
                        row = self.rows
                elif style == 'up':
                        if row > 0:
                                row -= 1
                        else:
                                row = 0
                elif style == 'down':
                        if row < self.rows:
                                row += 1
                        else:
                                row = self.rows
                else:
                        return
                top = self.model.index(row, 0, self.list.rootIndex())
                selectionModel.setCurrentIndex(top, QItemSelectionModel.Select | QItemSelectionModel.Rows)
                selection = QItemSelection(top, top)
                selectionModel.clearSelection()
                selectionModel.select(selection, QItemSelectionModel.Select)

        def load(self):
                row = self.list.selectionModel().currentIndex()
                self.clicked(row)

                fname = self.currentPath
                if fname is None: 
                        return
                if fname:
			COMMAND.abort()
                        printVerbose(_('Loading: {}',fname))
                        COMMAND.program_open(fname)

        def up(self):
                self.select_row('up')

        def down(self):
                self.select_row('down')
