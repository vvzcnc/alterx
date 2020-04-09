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

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

from alterx.gui.util import *
from alterx.core.linuxcnc import *

import operator

class OriginOffsetView(QTableView):
        def __init__(self, parent=None):
                QTableView.__init__(self,parent)
                self.setAlternatingRowColors(True)

                self.filename = INI.find('RS274NGC','PARAMETER_FILE') or '.cnc_var'
                self.axisletters = ["x", "y", "z", "a", "b", "c", "u", "v", "w"]
                self.current_system = "G54"
                self.current_tool = 0
                self.metric_display = True
                self.mm_text_template = '{:10.3f}'
                self.imperial_text_template = '{:9.4f}'
                self.setEnabled(False)
                self.table = self.createTable()

          	self.MACHINE_UNIT_CONVERSION_9 = [1.0/25.4]*3+[1]*3+[1.0/25.4]*3

		UPDATER.add("reload-offsets")
                UPDATER.connect('reload-offsets', self.reload_offsets)
                UPDATER.connect('program_units', lambda w, data: self.metricMode(data))
                UPDATER.connect('g5x_index', self._convert_system)

                conversion = {0:"X", 1:"Y", 2:"Z", 3:"A", 4:"B", 5:"C", 6:"U", 7:"V", 8:"W"}
                for num, let in conversion.iteritems():
                        if let in INFO.coordinates:
                                continue
                        self.hideColumn(num)

		self.reload_offsets()

        def _convert_system(self, w, data):
                convert = ("None", "G54", "G55", "G56", "G57", "G58", "G59", "G59.1", "G59.2", "G59.3")
                self.current_system = convert[int(data)]

        def currentTool(self, data):
                self.current_tool = data
        def metricMode(self, state):
                self.metric_display = state

        def createTable(self):
                # create blank taple array
                self.tabledata = [[0, 0, 1, 0, 0, 0, 0, 0, 0, 'Absolute Position'],
                                  [None, None, 2, None, None, None, None, None, None, 'Rotational Offsets'],
                                  [0, 0, 3, 0, 0, 0, 0, 0, 0, 'G92 Offsets'],
                                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 'Current Tool'],
                                  [0, 0, 4, 0, 0, 0, 0, 0, 0, 'System 1'],
                                  [0, 0, 5, 0, 0, 0, 0, 0, 0, 'System 2'],
                                  [0, 0, 6, 0, 0, 0, 0, 0, 0, 'System 3'],
                                  [0, 0, 7, 0, 0, 0, 0, 0, 0, 'System 4'],
                                  [0, 0, 8, 0, 0, 0, 0, 0, 0, 'System 5'],
                                  [0, 0, 9, 0, 0, 0, 0, 0, 0, 'System 6'],
                                  [0, 0, 10, 0, 0, 0, 0, 0, 0, 'System 7'],
                                  [0, 0, 11, 0, 0, 0, 0, 0, 0, 'System 8'],
                                  [0, 0, 12, 0, 0, 0, 0, 0, 0, 'System 9']]

                # create the view
                self.setSelectionMode(QAbstractItemView.SingleSelection)

                # set the table model
                header = ['X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W', 'Name']
                vheader = ['ABS', 'Rot', 'G92', 'Tool', 'G54', 'G55', 'G56', 'G57', 'G58', 'G59', 'G59.1', 'G59.2', 'G59.3']
                self.tablemodel = OffsetModel(self.tabledata, header, vheader, self)
                self.setModel(self.tablemodel)
                self.clicked.connect(self.showSelection)
                #self.dataChanged.connect(self.selection_changed)

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
                #text = cellContent.toPyObject()  # test
                text = cellContent
                printDebug(_('Text: {}, Row: {}, Column: {}',text, item.row(), item.column()))

        #############################################################

	def convert_units_9(self,v):
		c = self.MACHINE_UNIT_CONVERSION_9
		return map(lambda x,y: x*y, v, c)

        # Reload the offsets into display
        def reload_offsets(self):
                g54, g55, g56, g57, g58, g59, g59_1, g59_2, g59_3 = self.read_file()
                if g54 is None: return

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

                # set the text style based on unit type
                if self.metric_display:
                        tmpl = self.mm_text_template
                else:
                        tmpl = self.imperial_text_template

                degree_tmpl = "{:11.2f}"

                # fill each row of the liststore fron the offsets arrays
                for row, i in enumerate([ap, rot, g92, tool, g54, g55, g56, g57, g58, g59, g59_1, g59_2, g59_3]):
                        for column in range(0, 9):
                                if row == 1:
                                        if column == 2:
                                                self.tabledata[row][column] = degree_tmpl.format(rot)
                                        else:
                                                self.tabledata[row][column] = " "
                                else:
                                        self.tabledata[row][column] = tmpl.format(i[column])
                self.tablemodel.layoutChanged.emit()

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
                                printError(_('File does not exist: {}',self.filename))
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
                except:
                        return None, None, None, None, None, None, None, None, None

        def dataChanged(self, new, old, x):
                row = new.row()
                col = new.column()
                data = self.tabledata[row][col]

                # Hack to not edit any rotational offset but Z axis
                if row == 1 and not col == 2: return

                # set the text style based on unit type
                if self.metric_display:
                        tmpl = lambda s: self.mm_text_template % s
                else:
                        tmpl = lambda s: self.imperial_text_template % s

                # make sure we switch to correct units for machine and rotational, row 2, does not get converted
                try:
                                qualified = float(data)
                                #qualified = float(locale.atof(data))
                except Exception as e:
                        printError(_("Offset data changed error {}",e))
                # now update linuxcnc to the change
                try:
                        if STAT.task_mode == LINUXCNC.MODE_MDI:
                                if row == 0:  # current Origin
                                        COMMAND.mdi("G10 L2 P0 %s %10.4f" % (self.axisletters[col], qualified))
                                elif row == 1:  # rotational
                                        if col == 2:  # Z axis only
                                                COMMAND.mdi("G10 L2 P0 R %10.4f" % (qualified))
                                elif row == 2:  # G92 offset
                                        ACTION.CALL_MDI("G92 %s %10.4f" % (self.axisletters[col], qualified))
                                elif row == 3:  # Tool
                                        if not self.current_tool == 0:
                                                COMMAND.mdi("G10 L1 P%d %s %10.4f" % (self.current_tool, self.axisletters[col], qualified))
                                                COMMAND.mdi('g43')
                                else:
                                                COMMAND.mdi("G10 L2 P%d %s %10.4f" % (row-3, self.axisletters[col], qualified))

                                UPDATER.emit('reload-display')
                                self.reload_offsets()
                except Exception as e:
                        printError(_("Offsetpage widget error: MDI call error, {}",e))
                        self.reload_offsets()

#########################################
# offset model
#########################################
class OffsetModel(QAbstractTableModel):
        def __init__(self, datain, headerdata, vheaderdata, parent=None):
                """
                Args:
                        datain: a list of lists\n
                        headerdata: a list of strings
                """
                QAbstractTableModel.__init__(self,parent)
                self.arraydata = datain
                self.headerdata = headerdata
                self.Vheaderdata = vheaderdata

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
                # print(">>> flags() index.column() = ", index.column())
                if index.column() == 9 and index.row() in(0, 1, 2, 3):
                        return Qt.ItemIsEnabled
                elif index.row() == 1 and not index.column() == 2:
                        return Qt.NoItemFlags
                else:
                        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

        def setData(self, index, value, role):
                if not index.isValid():
                        return False
                printDebug(self.arraydata[index.row()][index.column()])
                printDebug(">>> setData() role = {}".format(role))
                printDebug(">>> setData() index.column() = {}".format(index.column()))
                try:
                        if index.column() == 9:
                                v = str(value)
                        else:
                                v = float(value)
                except:
                        return False
                printDebug(">>> setData() value = {}".format(value))
                printDebug(">>> setData() qualified value = {}".format(v))
                printDebug(">>> setData() index.row = {}".format(index.row()))
                printDebug(">>> setData() index.column = {}".format(index.column()))
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
                """
                Sort table by given column number.
                """
                self.emit(SIGNAL("layoutAboutToBeChanged()"))
                self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))
                if order == Qt.DescendingOrder:
                        self.arraydata.reverse()
                self.emit(SIGNAL("layoutChanged()"))

