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

class ToolOffsetView(QTableView):
        def __init__(self, parent=None):
                QTableView.__init__(self,parent)
                self.setAlternatingRowColors(True)

		self.toolfile = INI.find('EMCIO','TOOL_TABLE') or '.tool_table'
                self.filename = INI.find('RS274NGC','PARAMETER_FILE') or '.cnc_var'
                self.axisletters = ["x", "y", "z", "a", "b", "c", "u", "v", "w"]
                self.editing_flag = False
                self.current_system = None
                self.current_tool = 0
                self.metric_display = INFO.get_metric()
                self.mm_text_template = '%10.3f'
                self.imperial_text_template = '%9.4f'
                self.setEnabled(False)
		self.table = self.createTable()
        
		self.MACHINE_UNIT_CONVERSION = [1.0/25.4]*6+[1]*3+[1.0/25.4]*4

                conversion = {5:"Y", 6:'Y', 7:"Z", 8:'Z', 9:"A", 10:"B", 11:"C", 12:"U", 13:"V", 14:"W"}
                for num, let in conversion.iteritems():
                        if let in INFO.coordinates:
                                continue
                        self.hideColumn(num)

                if not INFO.machine_is_lathe:
                        for i in (4,6,8,16,17,18):
                                self.hideColumn(i)
                else:
                        self.hideColumn(15)

		self.reload_tools()

		UPDATER.add("reload-tools")
                UPDATER.connect('reload-tools', self.reload_tools)
                UPDATER.connect('program_units', self.metricMode)
                UPDATER.connect('tool_in_spindle', self.currentTool)

		INFO.get_tool_info = self.get_tool_info

	def get_tool_info(self,tool):
		try:	
			for t in self.tablemodel.arraydata:
				if t[1] == tool:
					return t
			return [None,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'No Comment']
		except Exception as e:
			printError(_("Failed to get tool info: {}",e))

        def currentTool(self, data):
                self.current_tool = data

        def metricMode(self, state):
		if self.metric_display != INFO.get_metric():
			self.metric_display = INFO.get_metric()
			self.reload_tools()

        def createTable(self):
                # create blank taple array
		tabledata = [[QCheckBox(),0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'No Comment']]

		# create the view
		self.setSelectionMode(QAbstractItemView.SingleSelection)

                # set the table model
                header = [_('Select'),_('Tool'),_('Pocket'),
			_('X'),_('X Wear'), _('Y'), _('Y Wear'), _('Z'), _('Z Wear'), 
			_('A'), _('B'), _('C'), _('U'), _('V'), _('W'), 
			_('Diameter'), _('Front Angle'), _('Back Angle'),
			_('Orientation'),_('Comment')]
                vheader = []
                self.tablemodel = ToolModel(tabledata, header, vheader, self)
                self.setModel(self.tablemodel)
                self.clicked.connect(self.showSelection)
                #self.dataChanged.connect(self.selection_changed)

                # set the minimum size
                self.setMinimumSize(100, 100)

                # set horizontal header properties
                hh = self.horizontalHeader()
                hh.setMinimumSectionSize(75)
                hh.setStretchLastSection(True)
                hh.setSortIndicator(1,Qt.AscendingOrder)

                # set column width to fit contents
                self.resizeColumnsToContents()

                # set row height
                self.resizeRowsToContents()

                # enable sorting
                self.setSortingEnabled(True)

        def showSelection(self, item):
                cellContent = item.data()
                #text = cellContent.toPyObject()  # test
                text = cellContent
                printDebug(_('Text: {}, Row: {}, Column: {}',text, item.row(), item.column()))

	def convert_units(self,v):
		c = self.MACHINE_UNIT_CONVERSION
		return map(lambda x,y: x*y, v, c)

   	def reload_tools(self,state=None):
		data = self.reload_tool_file()

		if data in (None, []):
	                data = [[QCheckBox(),0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'No Comment']]
		else:		
			data = self.convert_to_wear_type(data)

	        for line in data:
                        if line[0] != QCheckBox:
                                line[0] = QCheckBox()

                	if self.metric_display != INFO.machine_is_metric:
				line[3:16] = self.convert_units(line[3:16])

                self.tablemodel.layoutUpdate.emit(data)

                self.resizeColumnsToContents()
                self.resizeRowsToContents()

        def reload_tool_file(self):
		KEYWORDS = ['T', 'P', 'X', 'Y', 'Z', 'A', 'B', 'C', 'U', 'V', 'W', 'D', 'I', 'J', 'Q', ';']

                if self.toolfile is None or not os.path.exists(self.toolfile):
                        printDebug(_("Toolfile does not exist' {}",self.toolfile))
                        return None
                #print 'file',self.toolfile
                # clear the current liststore, search the tool file, and add each tool
                tool_model = []
                wear_model = []
                logfile = open(self.toolfile, "r").readlines()
                self.toolinfo = None
                toolinfo_flag = False
                for rawline in logfile:
                        # strip the comments from line and add directly to array
                        # if index = -1 the delimiter ; is missing - clear comments
                        index = rawline.find(";")
                        comment =''
                        if not index == -1:
                                comment = (rawline[index+1:])
                                comment = comment.rstrip("\n")
                                line = rawline.rstrip(comment)
                        else:
                                line = rawline
                        array = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,comment]
                        wear_flag = False
                        # search beginning of each word for keyword letters
                        # if i = ';' that is the comment and we have already added it
                        # offset 0 and 1 are integers the rest floats
                        # we strip leading and following spaces from the comments
                        for offset,i in enumerate(KEYWORDS):
                                if i == ';': continue
                                for word in line.split():
                                        if word.startswith(';'): break
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
                                                if offset in(0,1,14):
                                                        try:
                                                                array[offset]= int(word.lstrip(i))
                                                        except ValueError as e:
                                                                try:
                                                                        array[offset]= int(float(word.lstrip(i)))
                                                                except Exception as e:
                                                                        printError(_("Toolfile integer access: {} : {}",word.lstrip(i), e))
                                                else:
                                                        try:
                                                                if float(word.lstrip(i)) < 0.000001:
                                                                        array[offset]= 0
                                                                else:
                                                                        array[offset]= float(word.lstrip(i))
                                                        except:
                                                                printError(_("Toolfile float access: {}",self.toolfile))
                                                break

                        # add array line to model array
                        if wear_flag:
                                wear_model.append(array)
                        else:
                                tool_model.append(array)
                if toolinfo_flag:
                        self.toolinfo = temp
                else:
                        self.toolinfo = [0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,'No Comment']
                return (tool_model, wear_model)

        def save_tool_file(self, new_model, delete=()):
                if self.toolfile == None:
                        return True
                file = open(self.toolfile, "w")
                for row in new_model:
                        values = [ value for value in row ]
                        #print values
                        line = ""
                        skip = False
                        for num,i in enumerate(values):
                                #print KEYWORDS[num], i, #type(i), int(i)
                                if num == 0 and i in delete:
                                        printDebug(_("Delete tool ' {}",i))
                                        skip = True
                                if num in (0,1,14): # tool# pocket# orientation
                                        line = line + "%s%d "%(KEYWORDS[num], i)
                                elif num == 15: # comments
                                        test = i.strip()
                                        line = line + "%s%s "%(KEYWORDS[num],test)
                                else:
                                        test = str(i).lstrip()  # floats
                                        line = line + "%s%s "%(KEYWORDS[num], test)
                        printDebug(_("Save line: {}",line))
                        if not skip:
                                print >>file,line
                # Theses lines are required to make sure the OS doesn't cache the data
                # That would make linuxcnc and the widget to be out of synch leading to odd errors
                file.flush()
                os.fsync(file.fileno())
                # tell linuxcnc we changed the tool table entries
                try:
                        COMMAND.load_tool_table()
                except:
                        printError(_("Reloading of tool table into linuxcnc: {}",self.toolfile))
                        return True

        def convert_to_wear_type(self, data):
                if data is None:
                        data = ([],[])
                if not INFO.machine_is_lathe:
                        maintool = data[0] + data[1]
                        weartool = []
                else:
                        maintool = data[0]
                        weartool = data[1]
                #print 'main',data
                tool_num_list = {}
                full_tool_list = []
                for rnum, row in enumerate(maintool):
                        new_line = [False, 0, 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'No Comment']
                        valuesInRow = [ value for value in row ]
                        for cnum,i in enumerate(valuesInRow):
                                if cnum == 0:
                                        # keep a dict of actual tools numbers vrs row index
                                        tool_num_list[i] = rnum
                                if cnum in(0,1,2):
                                        # transfer these positions directly to new line (offset by 1 for checkbox)
                                        new_line[cnum +1] = i
                                elif cnum == 3:
                                        # move Y past x wear position
                                        new_line[5] = i
                                elif cnum == 4:
                                        # move z past y wear position
                                        new_line[7] = i
                                elif cnum in(5,6,7,8,9,10,11,12,13,14,15):
                                        # a;; the rest past z wear position
                                        new_line[cnum+4] = i
                        full_tool_list.append(new_line)
                        #print 'row',row
                        #print 'new row',new_line
                # any tool number over 10000 is a wear offset
                # It's already been separated in the weartool variable.
                # now we pull the values we need out and put it in our
                # full tool list's  tool variable's parent tool row
                # eg 10001 goes to tool 1, 10002 goes to tool 2 etc
                for rnum, row in enumerate(weartool):
                        values = [ value for value in row ]
                        parent_tool = tool_num_list[( values[0]-10000)]
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
                        new_line = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'']
                        new_wear_line = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'Wear Offset']
                        wear_flag = False
                        values = [ value for value in row ]
                        for cnum,i in enumerate(values):
                                #print cnum, i, type(i)
                                if cnum in(1,2):
                                        new_line[cnum-1] = int(i)
                                elif cnum == 3:
                                        new_line[cnum-1] = float(i)
                                elif cnum == 4 and i !='0':
                                        wear_flag = True
                                        new_wear_line[2] = float(i)
                                elif cnum == 5 and i !='0':
                                        new_line[cnum-2] = float(i)
                                elif cnum == 6 and i !='0':
                                        wear_flag = True
                                        new_wear_line[3] = float(i)
                                elif cnum == 7 and i !='0':
                                        new_line[cnum-3] = float(i)
                                elif cnum == 8 and i !='0':
                                        wear_flag = True
                                        new_wear_line[4] = float(i)
                                elif cnum in(9,10,11,12,13,14,15,16,17):
                                        new_line[cnum-4] = float(i)
                                elif cnum == 18:
                                        new_line[cnum-4] = int(i)
                                elif cnum == 19:
                                        new_line[cnum-4] = str(i)
                        if wear_flag:
                                new_wear_line[0] = int(values[1]+10000)
                                new_wear_line[15] = 'Wear Offset Tool %d'% values[1]
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
                printDebug(_('Entered data:{} {}', data, row,col))
                # now update linuxcnc to the change
                try:
                        if STAT.task_mode == LINUXCNC.MODE_MDI:
                                #for i in self.tablemodel.arraydata:
                                #        printDebug("2>>> = {}".format(i))
                                error = save_tool_file(self.convert_to_standard_type(self.tablemodel.arraydata))
                                if error:
                                        raise
                                COMMAND.mdi('g43')
				UPDATER.emit('reload-display')
	    			self.reload_table()
                                #self.resizeColumnsToContents()
                except Exception as e:
                        printError(_("Offsetpage widget error: MDI call error, {}",e))
			self.reload_table()
                self.editing_flag = False

        def add_tool(self):
                if STAT.task_mode != LINUXCNC.MODE_AUTO:
                        printDebug(_('Add tool request'))
                        TOOL.ADD_TOOL()

        def delete_tools(self):
                if STAT.task_mode != LINUXCNC.MODE_AUTO:
                        printDebug(_('Delete tools request'))
                        dtools = self.tablemodel.listCheckedTools()
                        if dtools:
                                error = save_tool_file(self.convert_to_standard_type(self.tablemodel.arraydata),dtools)

        def get_checked_list(self):
                return self.tablemodel.listCheckedTools()

#########################################
# tool model
#########################################
class ToolModel(QAbstractTableModel):
	layoutUpdate = pyqtSignal(list)

        def __init__(self, datain, headerdata, vheaderdata, parent=None):
                """
                Args:
                        datain: a list of lists\n
                        headerdata: a list of strings
                """
                QAbstractTableModel.__init__(self,parent)
                self.text_template = '%.4f'
                self.arraydata = datain
                self.headerdata = headerdata
                self.Vheaderdata = vheaderdata
		self.layoutUpdate.connect(self.update)

	def update(self,data):
		self.arraydata = data
		self.layoutChanged.emit()

        # make a list of all the checked tools
        def listCheckedTools(self):
                checkedlist = []
                for row in self.arraydata:
                        if row[0].isChecked():
                                checkedlist.append(row[1])
                return checkedlist

        # Returns the number of rows under the given parent.
        # When the parent is valid it means that rowCount is
        # returning the number of children of parent.
        #
        # Note: When implementing a table based model, rowCount() 
        # should return 0 when the parent is valid.
        def rowCount(self, parent):
                return len(self.arraydata)

        # Returns the number of columns for the children of the given parent.
        # Note: When implementing a table based model, columnCount() should 
        # return 0 when the parent is valid.
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
                                # print(">>> data() row,col = %d, %d" % (index.row(), index.column()))
                                if self.arraydata[index.row()][index.column()].isChecked():
                                        return Qt.Checked
                                else:
                                        return Qt.Unchecked
                return QVariant()


        # Returns the item flags for the given index.
        def flags(self, index):
                if not index.isValid():
                        return None
                if index.column() == 0:
                        return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
                else:
                        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

        # Sets the role data for the item at index to value.
        # Returns true if successful; otherwise returns false.
        # The dataChanged() signal should be emitted if the data was successfully set.
        # these column numbers correspond to our included wear columns
        # it will be converted when saved
        def setData(self, index, value, role):
                col = index.column()
                if not index.isValid():
                        printError(">>> index not valid {}".format(index))
                        return False
                printDebug("original value:{}".format(self.arraydata[index.row()][col]))
                printDebug(">>> setData() role = {}".format(role))
                printDebug(">>> setData() column() = {}".format(col))
                if role == Qt.CheckStateRole and index.column() == 0:
                        #print(">>> setData() role = ", role)
                        #print(">>> setData() index.column() = ", index.column())
                        if value == Qt.Checked:
                                self.arraydata[index.row()][index.column()].setChecked(True)
                                #self.arraydata[index.row()][index.column()].setText("Delete")
                                #print 'selected',self.arraydata[index.row()][1]
                        else:
                                self.arraydata[index.row()][index.column()].setChecked(False)
                                #self.arraydata[index.row()][index.column()].setText("Un")
                        # don't emit dataChanged - return right away
                        return True

                # TODO make valuse actually change in metric/impeial mode
                # currently it displays always in machine units.
                # there needs to be conversion added to this code
                # and this class needs access to templates and units mode.
                # don't convert tool,pocket,A, B, C, front angle, back angle, orintation or comments
                tmpl = lambda s: self.text_template % s
                try:
                        if col in (1,2,18): # tool, pocket, orientation
                                v = int(value)
                        elif col == 19:
                                v = str(value) # comment
                        else:
                                v = float(value)
                        self.arraydata[index.row()][col] = v
                except:
                        printError(_("Invaliad data type in row {} column:{} ",index.row(), col))
                        return False
                printDebug(">>> setData() value = {} ".format(value))
                printDebug(">>> setData() qualified value = {}".format(v))
                printDebug(">>> setData() index.row = {}".format(index.row()))
                printDebug(">>> setData() index.column = {}".format(col))

                printDebug(">>> = {}".format(self.arraydata[index.row()][col]))
                for i in self.arraydata:
                        printDebug(">>> = {}".format(i))

                self.dataChanged.emit(index, index)
                return True

        # Returns the data for the given role and section in the header with the specified orientation.
        # For horizontal headers, the section number corresponds to the column number. 
        # Similarly, for vertical headers, the section number corresponds to the row number.
        def headerData(self, col, orientation, role):
                if orientation == Qt.Horizontal and role == Qt.DisplayRole:
                        return QVariant(self.headerdata[col])
                if orientation != Qt.Horizontal and role == Qt.DisplayRole:
                        return QVariant('')
                return QVariant()

        # Sorts the model by column in the given order.
        def sort(self, Ncol, order):
                """
                Sort table by given column number.
                """
                self.layoutAboutToBeChanged.emit()
                self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))
                if order == Qt.DescendingOrder:
                        self.arraydata.reverse()
                self.layoutChanged.emit()
