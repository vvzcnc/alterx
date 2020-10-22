# -*- coding: utf-8 -*-
#
# AlterX GUI - tool viewer
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

__all__ = ['ToolOffsetView']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

from alterx.gui.util import *
from alterx.core.linuxcnc import *

import operator
import codecs

KEYWORDS = ['T', 'P', 'X', 'Y', 'Z', 'A', 'B',
            'C', 'U', 'V', 'W', 'D', 'I', 'J', 'Q', ';']

MACHINE_UNIT_CONVERSION = 25.4
ROW_TO_IMPERIAL = [1.0/25.4]*6+[1.0]*3+[1.0/25.4]*4
ROW_TO_METRIC = [25.4]*6+[1.0]*3+[25.4]*4
        
class ToolOffsetView(QTableView):
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)
        self.setAlternatingRowColors(True)
        
        self.toolfile = INFO.tool_file
        self.filename = INFO.parameter_file
        self.axisletters = ["x", "y", "z", "a", "b", "c", "u", "v", "w"]
        self.editing_flag = False
        self.current_system = None
        self.current_tool = 0
        self.metric_display = INFO.get_metric()
        self.mm_text_template = '%10.3f'
        self.imperial_text_template = '%9.4f'
        self.setEnabled(True)
        self.table = self.createTable()

        conversion = {5: "Y", 6: 'Y', 7: "Z", 8: 'Z', 9: "A",
                      10: "B", 11: "C", 12: "U", 13: "V", 14: "W"}
        for num, let in conversion.items():
            if let in INFO.coordinates:
                continue
            self.hideColumn(num)

        if not INFO.machine_is_lathe:
            for i in (4, 6, 8, 16, 17, 18):
                self.hideColumn(i)
        else:
            self.hideColumn(15)

        self.reload_tools()

        UPDATER.add("reload_tools")
        UPDATER.add("toolviewer_add")
        UPDATER.add("toolviewer_del")
        UPDATER.add("toolviewer_edit")
        UPDATER.add("toolviewer_left")
        UPDATER.add("toolviewer_right")
        UPDATER.add("toolviewer_next")
        UPDATER.add("toolviewer_prev")
        UPDATER.add("toolviewer_change")
        UPDATER.add("toolviewer_index")
        
        UPDATER.signal("toolviewer_add", self.add_tool)
        UPDATER.signal("toolviewer_del", self.delete_tool)
        UPDATER.signal("toolviewer_next", self.selection_next)
        UPDATER.signal("toolviewer_prev", self.selection_prev)
        UPDATER.signal("toolviewer_left", self.selection_left)
        UPDATER.signal("toolviewer_right", self.selection_right)
        UPDATER.signal("toolviewer_edit", self.selection_edit) 
        UPDATER.signal("reload_tools", self.reload_tools)
        UPDATER.signal("program_units", self.metricMode)
        UPDATER.signal("tool_in_spindle", self.currentTool)

        INFO.get_tool_info = self.get_tool_info
        INFO.get_selected_tool = self.get_selected_tool

    def resizeEvent(self, event):
        super(ToolOffsetView, self).resizeEvent(event)
        self.resizeRowsToContents()
        
    def get_selected_tool(self):
        index = self.get_row()
        if index.isValid():
            return self.tablemodel.arraydata[index.row()][1]
        return None
      
    def add_tool(self, state=None):
        tool_num = None
        for i in range(1,9999):
            skip = False
            for instr in self.tablemodel.arraydata:
                if instr[1] == i: 
                    skip = True
                    break
            if not skip:
                tool_num = i
                break
        printDebug(_('Add tool request: {}',tool_num))  
        if tool_num:
            data = [QCheckBox(), tool_num, tool_num, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 'No Comment']
            self.tablemodel.arraydata.append(data)
        else:
            printDebug(_('Failed to find new tool number'))
            
        self.save_tool_file(self.convert_to_standard_type(
                            self.tablemodel.arraydata))
        self.reload_tools()
        
        for n,instr in enumerate(self.tablemodel.arraydata):
            if instr[1] == i: 
                self.set_row(self.model().index(n, 0))
                break

    def delete_tool(self, state=None):
        index = self.get_row()
        if index.isValid():
            self.selection_prev()
            tool = self.tablemodel.arraydata[index.row()][1]
            printDebug(_('Delete tool request: {}',tool))  
            self.save_tool_file(self.convert_to_standard_type(
                        self.tablemodel.arraydata), delete=(tool,))
            self.reload_tools()

    def next_visible_column(self, index, rev=True):
        list_cols = [i for i in range(self.model().columnCount(None))]
        if rev:
            list_cols = [r for r in reversed(list_cols)]
            if index.column() > 0:
                list_cols = list_cols[self.model().columnCount(None) - index.column():]
        else:
            list_cols = list_cols[index.column() + 1:]
        for i in list_cols:
            if not self.horizontalHeader().isSectionHidden(i):
                return i
        return 0

    def selection_left(self, stat=None):
        self.setSelectionBehavior(QTableView.SelectItems)
        index = self.get_row()
        if index:
            self.set_row(self.model().index(index.row(), self.next_visible_column(index,True)))

    def selection_right(self, stat=None):
        self.setSelectionBehavior(QTableView.SelectItems)
        index = self.get_row()
        if index:
            self.set_row(self.model().index(index.row(), self.next_visible_column(index,False)))

    def selection_edit(self, stat=None):
        index = self.get_row()
        if stat and index:
            self.model().arraydata[index.row()][index.column()] = stat
            self.dataChanged(index,None,None)

    def selection_next(self, stat=None):
        self.setSelectionBehavior(QTableView.SelectRows)
        index = self.get_row()
        if index:
            self.set_row(self.model().index(index.row() + 1, 0))
        else:
            self.set_row(self.model().index(0, 0))

    def selection_prev(self, stat=None):
        self.setSelectionBehavior(QTableView.SelectRows)
        index = self.get_row()
        if index and index.row() > 0:
            self.set_row(self.model().index(index.row() - 1, 0))
        else:
            self.set_row(self.model().index(
                self.model().rowCount(None) - 1, 0))

    def get_row(self):
        return self.selectionModel().currentIndex()

    def set_row(self, index):
        self.setCurrentIndex(index)

    def get_tool_info(self, tool):
        try:
            for t in self.tablemodel.arraydata:
                if t[1] == tool:
                    return t
            return [None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 'No Comment']
        except Exception as e:
            printError(_("Failed to get tool info: {}", e))

    def currentTool(self, data):
        self.current_tool = data
        self.model().setCheckedLine(data)
        self.model().layoutChanged.emit()

    def metricMode(self, state):
        if self.metric_display != INFO.get_metric():
            self.metric_display = INFO.get_metric()
            self.reload_tools()

    def createTable(self):
        # create blank taple array
        tabledata = [[QCheckBox(), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                      0, 0, 0, 0, 0, 0, 0, 'No Comment']]

        # create the view
        self.setSelectionMode(QTableView.SingleSelection)
        self.setSelectionBehavior(QTableView.SelectRows)

        # set the table model
        header = [_('*'), _('Tool'), _('Pocket'),
                  _('X'), _('X Wear'), _('Y'), _('Y Wear'), _('Z'), _('Z Wear'),
                  _('A'), _('B'), _('C'), _('U'), _('V'), _('W'),
                  _('Diameter'), _('Front Angle'), _('Back Angle'),
                  _('Orientation'), _('Comment')]
        vheader = []
        self.tablemodel = ToolModel(tabledata, header, vheader, self)
        self.setModel(self.tablemodel)
        self.clicked.connect(self.showSelection)
        # self.dataChanged.connect(self.selection_changed)

        # set the minimum size
        self.setMinimumSize(100, 100)

        # enable sorting
        self.setSortingEnabled(True)

    def showSelection(self, item):
        cellContent = item.data()
        # text = cellContent.toPyObject()  # test
        text = cellContent
        printDebug(_('Text: {}, Row: {}, Column: {}',
                     text, item.row(), item.column()))

    def convert_units_to_file(self, v):
        if INFO.machine_is_metric:
            c = ROW_TO_METRIC[3:]
        else:
            c = ROW_TO_IMPERIAL[3:]
        return map(lambda x, y: x*y, v, c)

    def convert_units_from_file(self, v):
        if INFO.machine_is_metric:
            c = ROW_TO_IMPERIAL
        else:
            c = ROW_TO_METRIC
        return map(lambda x, y: x*y, v, c)

    def reload_tools(self, state=None):
        data = self.reload_tool_file()

        if data in (None, []):
            data = [[QCheckBox(), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 'No Comment']]
        else:
            data = self.convert_to_wear_type(data)

        for line in data:
            if line[0] != QCheckBox:
                line[0] = QCheckBox()

            if self.metric_display != INFO.machine_is_metric:
                line[3:16] = self.convert_units_from_file(line[3:16])

        self.tablemodel.layoutUpdate.emit(data)
        self.tablemodel.sort(1,Qt.AscendingOrder)
        
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(19,QHeaderView.Stretch)
        #self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def reload_tool_file(self):
        if self.toolfile is None or not os.path.exists(self.toolfile) or os.stat(self.toolfile).st_size==0:
            printDebug(_("Toolfile does not exist {}", self.toolfile))
            return None
        #print 'file',self.toolfile
        # clear the current liststore, search the tool file, and add each tool
        tool_model = []
        wear_model = []
        with open(self.toolfile, "r") as tool_file:
            self.toolinfo = None
            toolinfo_flag = False
            for line_index,rawline in enumerate(tool_file):
                rawline = toUnicode(rawline)
                # strip the comments from line and add directly to array
                # if index = -1 the delimiter ; is missing - clear comments
                index = rawline.find(";")
                comment = ''
                if not index == -1:
                    comment = (rawline[index+1:])
                    comment = comment.rstrip("\n")
                    line = rawline.rstrip(comment)
                else:
                    line = rawline
                array = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, comment]
                wear_flag = False
                # search beginning of each word for keyword letters
                # if i = ';' that is the comment and we have already added it
                # offset 0 and 1 are integers the rest floats
                # we strip leading and following spaces from the comments
                for offset, i in enumerate(KEYWORDS):
                    if i == ';':
                        continue
                    for word in line.split():
                        if word.startswith(';'):
                            break
                        if word.startswith(i):
                            if offset == 0:
                                if int(word.lstrip(i)) == STAT.tool_in_spindle:
                                    toolinfo_flag = True
                                    # This array's tool num is the current tool num
                                    # remember it for later
                                    temp = array
                                # check if tool is greater then 10000 -then it's a wear tool
                                if int(word.lstrip(i)) > 10000:
                                    wear_flag = True
                            if offset in(0, 1, 14):
                                try:
                                    array[offset] = int(word.lstrip(i))
                                except ValueError as e:
                                    try:
                                        array[offset] = int(float(word.lstrip(i)))
                                    except Exception as e:
                                        printError(
                                            _("Toolfile integer access: {} : {}", word.lstrip(i), e))
                            else:
                                try:
                                    if float(word.lstrip(i)) < 0.000001:
                                        array[offset] = 0
                                    else:
                                        array[offset] = float(word.lstrip(i))
                                except:
                                    printError(
                                        _("Toolfile float access: {}", self.toolfile))
                            break
                # add array line to model array
                if wear_flag:
                    wear_model.append(array)
                else:
                    tool_model.append(array)
       
            if toolinfo_flag:
                self.toolinfo = temp
            else:
                self.toolinfo = [0, 0, 0, 0, 0, 0, 0, 0,
                                 0, 0, 0, 0, 0, 0, 0, 'No Comment']
        return (tool_model, wear_model)

    def save_tool_file(self, new_model, delete=()):
        if self.toolfile == None:
            return True
        with codecs.open(self.toolfile, "w",encoding="utf-8") as file:
            for row in new_model:
                if self.metric_display != INFO.machine_is_metric:
                    row[2:12] = self.convert_units_to_file(row[2:12])
            
                values = [value for value in row]
                line = u""
                skip = False
                print(values)
                for num, i in enumerate(values):
                    # print KEYWORDS[num], i, #type(i), int(i)
                    if num == 0 and i in delete:
                        printDebug(_("Delete tool: {}", i))
                        skip = True
                    if num in (0, 1, 14):  # tool# pocket# orientation
                        line = line + u"{}{} ".format(KEYWORDS[num], i)
                    elif num == 15:  # comments
                        text = i.strip()
                        line = line + u"{}{} ".format(KEYWORDS[num], text)
                    else:
                        text = str(i).lstrip()  # floats
                        line = line + u"{}{} ".format(KEYWORDS[num], text)
                if not skip:
                    file.write(line + os.linesep)
                    printDebug(_("Save line: {}", line)) 

        # tell linuxcnc we changed the tool table entries
        try:
            COMMAND.load_tool_table()
        except:
            printError(
                _("Reloading of tool table into linuxcnc: {}", self.toolfile))
            return True

    def convert_to_wear_type(self, data):
        if data is None:
            data = ([], [])
        if not INFO.machine_is_lathe:
            maintool = data[0] + data[1]
            weartool = []
        else:
            maintool = data[0]
            weartool = data[1]
        tool_num_list = {}
        full_tool_list = []
        for rnum, row in enumerate(maintool):
            new_line = [False, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 'No Comment']
            valuesInRow = [value for value in row]
            for cnum, i in enumerate(valuesInRow):
                if cnum == 0:
                    # keep a dict of actual tools numbers vrs row index
                    tool_num_list[i] = rnum
                if cnum in(0, 1, 2):
                    # transfer these positions directly to new line (offset by 1 for checkbox)
                    new_line[cnum + 1] = i
                elif cnum == 3:
                    # move Y past x wear position
                    new_line[5] = i
                elif cnum == 4:
                    # move z past y wear position
                    new_line[7] = i
                elif cnum in(5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15):
                    # a;; the rest past z wear position
                    new_line[cnum+4] = i
            full_tool_list.append(new_line)

        # any tool number over 10000 is a wear offset
        # It's already been separated in the weartool variable.
        # now we pull the values we need out and put it in our
        # full tool list's  tool variable's parent tool row
        # eg 10001 goes to tool 1, 10002 goes to tool 2 etc
        for rnum, row in enumerate(weartool):
            values = [value for value in row]
            parent_tool = tool_num_list[(values[0]-10000)]
            full_tool_list[parent_tool][4] = values[2]
            full_tool_list[parent_tool][6] = values[3]
            full_tool_list[parent_tool][8] = values[4]
        return full_tool_list

    def convert_to_standard_type(self, data):
        if data is None:
            data = ([])
        tool_wear_list = []
        full_tool_list = []
        for rnum, row in enumerate(data):
            new_line = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '']
            new_wear_line = [0, 0, 0, 0, 0, 0, 0, 0,
                             0, 0, 0, 0, 0, 0, 0, 'Wear Offset']
            wear_flag = False
            values = [value for value in row]
            for cnum, i in enumerate(values):
                #print cnum, i, type(i)
                if cnum in(1, 2):
                    new_line[cnum-1] = int(i)
                elif cnum == 3:
                    new_line[cnum-1] = float(i)
                elif cnum == 4 and i != 0:
                    wear_flag = True
                    new_wear_line[2] = float(i)
                elif cnum == 5 and i != 0:
                    new_line[cnum-2] = float(i)
                elif cnum == 6 and i != 0:
                    wear_flag = True
                    new_wear_line[3] = float(i)
                elif cnum == 7 and i != 0:
                    new_line[cnum-3] = float(i)
                elif cnum == 8 and i != 0:
                    wear_flag = True
                    new_wear_line[4] = float(i)
                elif cnum in(9, 10, 11, 12, 13, 14, 15, 16, 17):
                    new_line[cnum-4] = float(i)
                elif cnum == 18:
                    new_line[cnum-4] = int(i)
                elif cnum == 19:
                    new_line[cnum-4] = toUnicode(i)

            if wear_flag:
                new_wear_line[0] = int(values[1]+10000)
                new_wear_line[15] = 'Wear Offset Tool %d' % values[1]
                tool_wear_list.append(new_wear_line)
            # add tool line to tool list
            full_tool_list.append(new_line)
        # add wear list to full tool list
        full_tool_list = full_tool_list + tool_wear_list
        return full_tool_list

    def dataChanged(self, new, old, roles):
        self.editing_flag = True
        row = new.row()
        col = new.column()
        data = self.tablemodel.arraydata[row][col]
        printDebug(_('Entered tool data:{} {} {}', data, row, col))
        
        # now update linuxcnc to the change
        try:
            if STAT.task_mode == LINUXCNC.MODE_MDI:
                error = self.save_tool_file(
                    self.convert_to_standard_type(self.tablemodel.arraydata))
                if error:
                    raise
                COMMAND.mdi("G43")
                COMMAND.wait_complete()
                self.reload_tools()
        except Exception as e:
            printError(_("Tool offsetpage widget error: MDI call error, {}", e))
            self.reload_tools()
        self.editing_flag = False

    def get_checked_list(self):
        return self.tablemodel.listCheckedTools()

#########################################
# tool model
#########################################


class ToolModel(QAbstractTableModel):
    layoutUpdate = pyqtSignal(list)

    def __init__(self, datain, headerdata, vheaderdata, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.text_template = '%.4f'
        self.arraydata = datain
        self.headerdata = headerdata
        self.Vheaderdata = vheaderdata
        self.layoutUpdate.connect(self.update)

    def update(self, data):
        self.arraydata = data
        self.layoutChanged.emit()

    # make a list of all the checked tools
    def listCheckedTools(self):
        checkedlist = []
        for row in self.arraydata:
            if row[0].isChecked():
                checkedlist.append(row[1])
        return checkedlist

    def setCheckedLine(self,tool):
        for row in self.arraydata:
            if row[1] != tool:
                row[0].setChecked(False)
            else:
                row[0].setChecked(True)

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        if len(self.arraydata) > 0:
            return len(self.arraydata[0])
        return 0

    # Returns the data stored under the given role for the item referred to by the index.
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.EditRole:
            return self.arraydata[index.row()][index.column()]
        elif role == Qt.DisplayRole:
            return self.arraydata[index.row()][index.column()]
        elif role == Qt.CheckStateRole:
            if index.column() == 0:
                if self.arraydata[index.row()][index.column()].isChecked():
                    return Qt.Checked
                else:
                    return Qt.Unchecked
        return None

    # Returns the item flags for the given index.
    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
        else:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def setData(self, index, value, role):
        col = index.column()
        if not index.isValid():
            printError("Tool viewer index not valid {}".format(index))
            return False
        if role == Qt.CheckStateRole and index.column() == 0:
            if value == Qt.Checked:
                self.arraydata[index.row()][index.column()].setChecked(True)
            else:
                self.arraydata[index.row()][index.column()].setChecked(False)
            return True

        # TODO make valuse actually change in metric/impeial mode
        # currently it displays always in machine units.
        # there needs to be conversion added to this code
        # and this class needs access to templates and units mode.
        # don't convert tool,pocket,A, B, C, front angle, back angle, orintation or comments
        def tmpl(s): return self.text_template % s
        try:
            if col in (1, 2, 18):  # tool, pocket, orientation
                v = int(value)
            elif col == 19:
                v = str(value)  # comment
            else:
                v = float(value)
            self.arraydata[index.row()][col] = v
        except:
            printError(
                _("Invaliad data type in row {} column:{} ", index.row(), col))
            return False

        self.dataChanged.emit(index, index)
        return True

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headerdata[col]
        if orientation != Qt.Horizontal and role == Qt.DisplayRole:
            return ''
        return None

    def sort(self, Ncol, order):
        self.layoutAboutToBeChanged.emit()
        self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))
        if order == Qt.DescendingOrder:
            self.arraydata.reverse()
        self.layoutChanged.emit()
