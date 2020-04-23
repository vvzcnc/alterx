# -*- coding: utf-8 -*-
#
# AlterX GUI - offset viewer
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

__all__ = ['OriginOffsetView']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

from alterx.gui.util import *
from alterx.core.linuxcnc import *

import operator


class OriginOffsetView(QTableView):
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)
        self.setAlternatingRowColors(True)

        self.filename = INI.find('RS274NGC', 'PARAMETER_FILE') or '.cnc_var'
        self.axisletters = ["x", "y", "z", "a", "b", "c", "u", "v", "w"]
        self.current_system = "G54"
        self.current_tool = 0

        self.metric_display = INFO.get_metric()
        self.mm_text_template = '{:10.3f}'
        self.imperial_text_template = '{:9.4f}'
        self.degree_text_template = '{:11.2f}'
        self.linear_tmpl = self.mm_text_template
        self.degree_tmpl = self.degree_text_template

        self.setEnabled(True)
        self.table = self.createTable()

        self.MACHINE_UNIT_CONVERSION_9 = [1.0/25.4]*3+[1]*3+[1.0/25.4]*3

        conversion = {0: "X", 1: "Y", 2: "Z", 3: "A",
                      4: "B", 5: "C", 6: "U", 7: "V", 8: "W"}
        for num, let in conversion.iteritems():
            if let in INFO.coordinates:
                continue
            self.hideColumn(num)

        self.reload_offsets()

        UPDATER.add("reload_offsets")
        UPDATER.connect("reload_offsets", self.reload_offsets)
        UPDATER.connect("tool_offset", self.reload_offsets)
        #UPDATER.connect("g5x_offset", self.reload_offsets)
        UPDATER.connect("g92_offset", self.reload_offsets)

        UPDATER.connect("program_units", self.metricMode)
        UPDATER.connect("g5x_index", self.currentSystem)
        UPDATER.connect("tool_in_spindle", self.currentTool)

        UPDATER.add("offsetviewer_next")
        UPDATER.add("offsetviewer_prev")
        UPDATER.add("offsetviewer_select")
        UPDATER.add("offsetviewer_edit")

        UPDATER.connect("offsetviewer_next", self.selection_next)
        UPDATER.connect("offsetviewer_prev", self.selection_prev)
        UPDATER.connect("offsetviewer_select", self.selection_set)
        UPDATER.connect("offsetviewer_edit", self.selection_edit)

    def selection_next(self, stat=None):
        index = self.get_row()
        if index:
            self.set_row(self.model().index(index.row() + 1, 2))
        else:
            self.set_row(self.model().index(0, 2))

    def selection_prev(self, stat=None):
        index = self.get_row()
        if index and index.row() > 0:
            self.set_row(self.model().index(index.row() - 1, 2))
        else:
            self.set_row(self.model().index(
                self.model().rowCount(None) - 1, 2))

    def selection_set(self, stat=None):
        index = self.get_row()
        if index and index.row() > 3 and STAT.task_mode == LINUXCNC.MODE_MDI:
            COMMAND.mdi(self.convert_system(index.row()-4))

    def selection_edit(self, stat=None):
        index = self.get_row()
        if index and index.row() > 0:
            try:
                axis, value = stat
            except:
                return

            self.tabledata[index.row()][axis] = value
            new_index = self.model().index(index.row(), axis)
            self.dataChanged(new_index, None, None)
            self.tablemodel.layoutUpdate.emit()

    def get_row(self):
        return self.selectionModel().currentIndex()

    def set_row(self, index):
        self.setCurrentIndex(index)

    def convert_system(self, data):
        convert = ("G54", "G55", "G56", "G57", "G58",
                   "G59", "G59.1", "G59.2", "G59.3")
        return convert[int(data)]

    def currentSystem(self, data):
        self.current_system = self.convert_system(data-1)

    def currentTool(self, data):
        self.current_tool = data
        self.reload_offsets()

    def metricMode(self, state):
        if self.metric_display != INFO.get_metric():
            # set the text style based on unit type
            if self.metric_display:
                self.linear_tmpl = self.mm_text_template
            else:
                self.linear_tmpl = self.imperial_text_template

            self.metric_display = INFO.get_metric()
            self.reload_offsets()

    def createTable(self):
        # create blank taple array
        self.tabledata = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 'Absolute Position'],
                          [None, None, None, None, None, None, None,
                              None, None, 'Rotational Offsets'],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 'G92 Offsets'],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 'Current Tool'],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 'System 1'],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 'System 2'],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 'System 3'],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 'System 4'],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 'System 5'],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 'System 6'],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 'System 7'],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 'System 8'],
                          [0, 0, 0, 0, 0, 0, 0, 0, 0, 'System 9']]

        # create the view
        self.setSelectionMode(QTableView.SingleSelection)
        self.setSelectionBehavior(QTableView.SelectRows)

        # set the table model
        header = ['X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W', 'Name']
        vheader = ['ABS', 'Rot', 'G92', 'Tool', 'G54', 'G55',
                   'G56', 'G57', 'G58', 'G59', 'G59.1', 'G59.2', 'G59.3']
        self.tablemodel = OffsetModel(self.tabledata, header, vheader, self)
        self.setModel(self.tablemodel)
        self.clicked.connect(self.showSelection)
        # self.dataChanged.connect(self.selection_changed)

        # set the minimum size
        self.setMinimumSize(100, 100)

        # set horizontal header properties
        hh = self.horizontalHeader()
        hh.setStretchLastSection(True)
        hh.setMinimumSectionSize(75)

        # set column width to fit contents
        self.resizeColumnsToContents()

        # set row height
        self.resizeRowsToContents()

        # enable sorting
        self.setSortingEnabled(False)

    def showSelection(self, item):
        cellContent = item.data()
        text = cellContent
        printDebug(_('Text: {}, Row: {}, Column: {}',
                     text, item.row(), item.column()))

    #############################################################

    def convert_units_9(self, v):
        c = self.MACHINE_UNIT_CONVERSION_9
        return map(lambda x, y: x*y, v, c)

    # Reload the offsets into display
    def reload_offsets(self, state=None):
        g54, g55, g56, g57, g58, g59, g59_1, g59_2, g59_3 = self.read_file()
        if g54 is None:
            return

        # Get the offsets arrays and convert the units if the display
        # is not in machine native units

        ap = STAT.actual_position
        tool = STAT.tool_offset
        g92 = STAT.g92_offset
        rot = STAT.rotation_xy

        if self.metric_display != INFO.machine_is_metric:
            ap = self.convert_units_9(ap)
            tool = self.convert_units_9(tool)
            g92 = self.convert_units_9(g92)
            g54 = self.convert_units_9(g54)
            g55 = self.convert_units_9(g55)
            g56 = self.convert_units_9(g56)
            g57 = self.convert_units_9(g57)
            g58 = self.convert_units_9(g58)
            g59 = self.convert_units_9(g59)
            g59_1 = self.convert_units_9(g59_1)
            g59_2 = self.convert_units_9(g59_2)
            g59_3 = self.convert_units_9(g59_3)

        # fill each row of the liststore fron the offsets arrays
        for row, i in enumerate([ap, rot, g92, tool, g54, g55, g56, g57, g58, g59, g59_1, g59_2, g59_3]):
            for column in range(0, 9):
                if row == 1:
                    if column == 2:
                        self.tabledata[row][column] = self.degree_tmpl.format(
                            rot)
                    else:
                        self.tabledata[row][column] = " "
                else:
                    self.tabledata[row][column] = self.linear_tmpl.format(
                        i[column])
        self.tablemodel.layoutUpdate.emit()

    # We read the var file directly
    # and pull out the info we need
    # if anything goes wrong we set all the info to 0
    def read_file(self):
        try:
            g54 = [0, 0, 0, 0, 0, 0, 0, 0, 0]
            g55 = [0, 0, 0, 0, 0, 0, 0, 0, 0]
            g56 = [0, 0, 0, 0, 0, 0, 0, 0, 0]
            g57 = [0, 0, 0, 0, 0, 0, 0, 0, 0]
            g58 = [0, 0, 0, 0, 0, 0, 0, 0, 0]
            g59 = [0, 0, 0, 0, 0, 0, 0, 0, 0]
            g59_1 = [0, 0, 0, 0, 0, 0, 0, 0, 0]
            g59_2 = [0, 0, 0, 0, 0, 0, 0, 0, 0]
            g59_3 = [0, 0, 0, 0, 0, 0, 0, 0, 0]
            if self.filename is None:
                return g54, g55, g56, g57, g58, g59, g59_1, g59_2, g59_3
            if not os.path.exists(self.filename):
                printError(_('File does not exist: {}', self.filename))
                return g54, g55, g56, g57, g58, g59, g59_1, g59_2, g59_3
            logfile = open(self.filename, "r").readlines()
            for line in logfile:
                temp = line.split()
                param = int(temp[0])
                data = float(temp[1])

                if 5229 >= param >= 5221:
                    g54[param - 5221] = data
                elif 5249 >= param >= 5241:
                    g55[param - 5241] = data
                elif 5269 >= param >= 5261:
                    g56[param - 5261] = data
                elif 5289 >= param >= 5281:
                    g57[param - 5281] = data
                elif 5309 >= param >= 5301:
                    g58[param - 5301] = data
                elif 5329 >= param >= 5321:
                    g59[param - 5321] = data
                elif 5349 >= param >= 5341:
                    g59_1[param - 5341] = data
                elif 5369 >= param >= 5361:
                    g59_2[param - 5361] = data
                elif 5389 >= param >= 5381:
                    g59_3[param - 5381] = data
            return g54, g55, g56, g57, g58, g59, g59_1, g59_2, g59_3
        except Exception as e:
            printDebug(_("Reading parameter file failed: {}", e))
            return None, None, None, None, None, None, None, None, None

    def dataChanged(self, new, old, x):
        row = new.row()
        col = new.column()
        data = self.tabledata[row][col]

        # Hack to not edit any rotational offset but Z axis
        if row == 1 and not col == 2:
            return

        # TODO: Save system name
        if col == 9:
            return

        if row == 1:
            if col == 2:
                self.tabledata[row][col] = self.degree_tmpl.format(data)
            else:
                self.tabledata[row][col] = " "
        else:
            self.tabledata[row][col] = self.linear_tmpl.format(data)

        # make sure we switch to correct units for machine and rotational, row 2, does not get converted
        try:
            qualified = float(data)
            #qualified = float(locale.atof(data))
        except Exception as e:
            printError(_("Offset data changed error {}", e))

        # now update linuxcnc to the change
        try:
            if STAT.task_mode == LINUXCNC.MODE_MDI:
                if row == 0:  # current Origin
                    COMMAND.mdi("G10 L2 P0 %s %10.4f" %
                                (self.axisletters[col], qualified))
                elif row == 1:  # rotational
                    if col == 2:  # Z axis only
                        COMMAND.mdi("G10 L2 P0 R %10.4f" % (qualified))
                elif row == 2:  # G92 offset
                    COMMAND.mdi("G92 %s %10.4f" %
                                (self.axisletters[col], qualified))
                elif row == 3:  # Tool
                    if not self.current_tool == 0:
                        COMMAND.mdi("G10 L1 P%d %s %10.4f" % (
                            self.current_tool, self.axisletters[col], qualified))
                        COMMAND.mdi("G43")
                else:
                    COMMAND.mdi("G10 L2 P%d %s %10.4f" %
                                (row-3, self.axisletters[col], qualified))
        except Exception as e:
            printError(_("Offsetpage widget error: MDI call error, {}", e))
            self.reload_offsets()


#########################################
# offset model
#########################################
class OffsetModel(QAbstractTableModel):
    layoutUpdate = pyqtSignal()

    def __init__(self, datain, headerdata, vheaderdata, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.arraydata = datain
        self.headerdata = headerdata
        self.Vheaderdata = vheaderdata
        self.layoutUpdate.connect(self.update)

    def update(self):
        self.layoutChanged.emit()

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        if len(self.arraydata) > 0:
            return len(self.arraydata[0])
        return 0

    def data(self, index, role):
        if role == Qt.EditRole:
            return self.arraydata[index.row()][index.column()]
        if role == Qt.DisplayRole:
            return QVariant(self.arraydata[index.row()][index.column()])
        return QVariant()

    def flags(self, index):
        if not index.isValid():
            return None
        if index.column() == 9 and index.row() in(0, 1, 2, 3):
            return Qt.ItemIsEnabled
        elif index.row() == 1 and not index.column() == 2:
            return Qt.NoItemFlags
        else:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def setData(self, index, value, role):
        if not index.isValid():
            return False

        try:
            if index.column() == 9:
                v = str(value)
            else:
                v = float(value)
        except Exception as e:
            printDebug(_("Set offset data failed: {}", e))
            if index.column() == 9:
                v = str(" ")
            else:
                v = float(0.0)

        self.arraydata[index.row()][index.column()] = v
        self.dataChanged.emit(index, index)
        return True

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.headerdata[col])
        if orientation != Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.Vheaderdata[col])
        return QVariant()

    def sort(self, Ncol, order):
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))
        if order == Qt.DescendingOrder:
            self.arraydata.reverse()
        self.emit(SIGNAL("layoutChanged()"))
