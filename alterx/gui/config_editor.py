# -*- coding: utf-8 -*-
#
# AlterX GUI - config editor
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

__all__ = ['ConfigEditor']

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

from alterx.gui.util import *
from alterx.core.linuxcnc import *

from functools import partial
from collections import OrderedDict
from shutil import copyfile

class WizardWidget(QWidget):
    def __init__(self,parent,parameters):
        QWidget.__init__(self)
        lay = QVBoxLayout()
        caption = QLabel(parameters[0])
        text = QLabel(parameters[1])
        self.p = parameters
        self.parser = parent.config
        self.page = parent.page
        self.parent = parent
        self.edit = QLineEdit()
        buttonYes = QPushButton()
        buttonYes.setText(_("Yes"))
        buttonYes.clicked.connect(self.yes_clicked)
        buttonNo = QPushButton()
        buttonNo .setText(_("No"))
        buttonNo.clicked.connect(self.no_clicked)
        buttonNext = QPushButton()
        buttonNext .setText(_("Next"))
        buttonNext.clicked.connect(self.next_clicked)
        
        lay.addWidget(caption)
        if parameters[2]:
            lay.addWidget(self.edit)
        lay.addWidget(text)
        
        lay.addStretch()
        
        if not parameters[2]:
            lay.addWidget(buttonNo)
        lay.addWidget(buttonYes)
        lay.addWidget(buttonNext)        

        self.setLayout(lay)
  
    def next_clicked(self):
        p = int(self.p[3])
        if p<0:
            cur = self.page.currentIndex()
            self.page.setCurrentIndex(cur + 1)
        else:
            self.page.setCurrentIndex(p) 
        
    def yes_clicked(self):
        p = int(self.p[3])
        if p<0:
            cur = self.page.currentIndex()
            self.page.setCurrentIndex(cur + 1)
        else:
            self.page.setCurrentIndex(p)
            
        options = self.p[5].split(',')
        for opt in options:
            if len(opt.split(' ')) == 1:
                if opt == "add_axes":
                    self.parent.add_default_axes()
                elif opt == "stop_wizard":
                    self.parent.stop_wizard()
                elif "copy_hal" in opt:
                    try:
                        self.parent.copy_default_hal(
                            (opt.split('=')[1]).format(self.p[0]))
                    except Exception as e:
                        printDebug(_("Default hal file copy failed, {}",e))
                elif opt == "axis_wizard":
                    self.parent.run_axis_wizard()
                
                continue
        
            section,option,value = opt.split(' ')
            try:
                last = self.parser.get(section,option)+'\n'
            except:
                last = ''
            self.parser.set(section,option,value.format(last,self.edit.text(),
                                                        self.p[0]))   
        
    def no_clicked(self): 
        p = int(self.p[4])
        if p<0:
            cur = self.page.currentIndex()
            self.page.setCurrentIndex(cur + 1)
        else:
            self.page.setCurrentIndex(p)
            
        options = self.p[6].split(',')
        for opt in options:
            if len(opt.split(' ')) == 1:
                continue
                
            section,option,value = opt.split(' ')
            try:
                last = self.parser.get(section,option)
            except:
                last = ''
            self.parser.set(section,option,value.format(last,self.edit.text()))   

class MultiOrderedDict(OrderedDict):
    def __setitem__(self, key, value):
        if isinstance(value, list) and key in self:
            self[key].extend(value)
        else:
            OrderedDict.__setitem__(self, key, value)

class ConfigEditor(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        vlay = QVBoxLayout()
        
        label = QLabel(_("Config Editor"))
        label.setObjectName("lbl_settings_configeditor")
        vlay.addWidget(label)
        
        hlay = QHBoxLayout()
        hlay2 = QHBoxLayout()
        save = QPushButton()
        save.setText(_("Save"))
        save.clicked.connect(self.save_clicked)
        load = QPushButton()
        load.setText(_("Load"))
        load.clicked.connect(self.load_clicked)    
        load_default = QPushButton()
        load_default.setText(_("Load default"))
        load_default.clicked.connect(self.load_default_clicked)
        save_as = QPushButton()
        save_as.setText(_("Save as"))
        save_as.clicked.connect(self.save_as_clicked)
        self.run_wizard = QPushButton()
        self.run_wizard.setText(_("Run wizard"))
        self.run_wizard.clicked.connect(self.run_wizard_clicked)
        hlay.addWidget(load_default)
        hlay.addWidget(load)
        hlay.addWidget(self.run_wizard)
        hlay.addWidget(save)
        hlay.addWidget(save_as)
        vlay.addLayout(hlay)
        prev_page = QPushButton()
        prev_page.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Minimum)
        prev_page.setText("<")
        prev_page.clicked.connect(self.prev_page_clicked)
        hlay2.addWidget(prev_page)
        self.page = QTabWidget()
        hlay2.addWidget(self.page)
        next_page = QPushButton()
        next_page.setText(">")
        next_page.clicked.connect(self.next_page_clicked)
        next_page.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Minimum)
        hlay2.addWidget(next_page)
        vlay.addLayout(hlay2)
        self.setLayout(vlay)
        self.config_dir = pkg_resources.resource_filename("alterx", "configs")
        self.config = ConfigParser.ConfigParser(
            dict_type=MultiOrderedDict,allow_no_value=True)
        self.config.optionxform = str
        self.load_clicked()
        self.wizard = False

    def prev_page_clicked(self):
        current = self.page.currentIndex()
        if current > 0:
            self.page.setCurrentIndex(current-1)
    
    def next_page_clicked(self):
        current = self.page.currentIndex()
        if current < self.page.count()-1:
            self.page.setCurrentIndex(current+1)

    def add_default_axes(self):
        num_axes = self.config.get("KINS","JOINTS")
        version = self.config.get("EMC","CORE")
        coordinates = self.config.get("TRAJ","COORDINATES")
        
        if int(num_axes) != len(coordinates.split(' ')):
            QMessageBox.critical(None,_("COORDINATES not equal AXES"),
                _("The number of axes and coordinates does not converge.\n"
                "Check [TRAJ]COORDINATES and [KINS]JOINTS"),
                QMessageBox.Ok,QMessageBox.Ok)
            return
            
        if len(version)<3:
            QMessageBox.critical(None,_("Wrong core version"),
                _("Invalid parameter [EMC]CORE.\n"),
                QMessageBox.Ok,QMessageBox.Ok)
            return
            
        default = os.path.join(self.config_dir,"default_axis_ini.cfg")
        self.config.read(default)

        try:
            items = self.config.items(
                "DEFAULT_AXIS_{}".format(version[:3]))
                
            if float(version[:3]) <= '2.7':
                axes_list = range(int(num_axes))    
                joints_list = []
            else:
                axes_list = coordinates.split(' ')
                joints_list = range(int(num_axes))    
            
            for axis in axes_list:
                name = "AXIS_{}".format(axis)
                self.config.add_section(name)
                for item in items:
                    self.config.set(name,item[0],item[1])
                    
            items = self.config.items(
                "DEFAULT_JOINT_{}".format(version[:3]))
                   
            for joint in joints_list:
                name = "JOINT_{}".format(joint)
                self.config.add_section(name)
                for item in items:
                    self.config.set(name,item[0],item[1])

            for s in self.config.sections():
                if s.startswith("DEFAULT_"):
                    self.config.remove_section(s)
        except ConfigParser.NoSectionError as e:
            QMessageBox.critical(None,_("Can't find section"),
                _("Can't find section. {}.\n"
                "Probably wrong core version.",e),
                QMessageBox.Ok,QMessageBox.Ok)
        except Exception as e:
            printDebug(_("Add default axis exception: {}",e))

    def copy_default_hal(self,param):
        p = param.split('|')
        name_from = p[0]
        name_to = p[1]
        with open(os.path.join(self.config_dir,name_from)) as fr:
            with open(name_to, "w") as fw:
                for line in fr:
                   if len(p)>2:
                       fw.write(line.replace(p[2],p[3])) 
                   else:
                       fw.write(line)

    def stop_wizard(self):
        self.load_clicked(default_file=None,only_update=True)

    def run_axis_wizard(self):
        if self.page.count() > 0:
            for i in reversed(range(self.page.count())):
                try:
                    self.page.widget(i).deleteLater()
                    self.page.removeTab(i)
                except Exception as e:
                    printDebug(_("Delete tab exception: {}",e))

        version = self.config.get("EMC","CORE")

        if float(version[:3]) <= '2.7':
            default_wizard = os.path.join(self.config_dir,"axis_wizard.cfg")  
        else:
            default_wizard = os.path.join(self.config_dir,"joint_wizard.cfg")  

        coordinates = self.config.get("TRAJ","COORDINATES")

        with open(default_wizard, "r") as fp:
            for line in fp:
                if line.startswith('#') or len(line) < 8 or not line:
                    continue
                for i,axis in enumerate(coordinates.split(' ')):
                    try:
                        c,t,e,nYes,nNo,aYes,aNo = line.split(';')[:-1]
                    except Exception as e:
                        printDebug(_("Broken wizard line: {}\n{}",e,line))
                        continue
                        
                    if float(version[:3]) <= '2.7':
                        num = {'X':0,'Y':1,'Z':2,'A':3,'B':4,'C':5,'U':6,'V':7,'W':8}[axis]
                    else:
                        num = i
                    
                    c = c.replace("_('",'')
                    c = c.replace("')",'')
                    t = t.replace("_('",'')
                    t = t.replace("')",'')

                    caption = c
                    text = t
                    try:
                        caption = _(c).format(num,axis)
                        text = _(t).format(num,axis)
                    except:
                        caption = c.format(num,axis)
                        text = t.format(num,axis)
                        
                    p = (caption,text,e,nYes,nNo,aYes,aNo)
                    self.page.addTab(WizardWidget(self,p),caption)

    def run_wizard_clicked(self):
        if self.page.count() > 0:
            for i in reversed(range(self.page.count())):
                try:
                    self.page.widget(i).deleteLater()
                    self.page.removeTab(i)
                except Exception as e:
                    printDebug(_("Delete tab exception: {}",e))
                    
        if self.wizard:
            self.stop_wizard()
        else:
            self.wizard = True
            self.run_wizard.setText(_("Stop wizard"))
                    
            default_wizard = os.path.join(self.config_dir,"default_wizard.cfg")  
                        
            with open(default_wizard, "r") as fp:
                for line in fp:
                    if line.startswith('#') or len(line) < 8 or not line:
                        continue
                    try:
                        c,t,e,nYes,nNo,aYes,aNo = line.split(';')[:-1]
                    except Exception as e:
                        printDebug(_("Broken wizard line: {}\n{}",e,line))
                        continue
                        
                    c = c.replace("_('",'')
                    c = c.replace("')",'')
                    t = t.replace("_('",'')
                    t = t.replace("')",'')
                        
                    caption = c
                    text = t
                    try:
                        caption = _(c)
                        text = _(t)
                    except:
                        pass
                    p = (caption,text,e,nYes,nNo,aYes,aNo)
                    self.page.addTab(WizardWidget(self,p),caption)

    def new_section(self,section):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        scroll.setWidget(widget)
    
        vlay = QVBoxLayout()
        vlay.setContentsMargins(20,20,20,20)
        hlay1 = QHBoxLayout()
        hlay2 = QHBoxLayout()
        
        del_section_button = QPushButton()
        del_section_button.setText(_("Delete section"))
        del_section_button.clicked.connect(partial(self.delete_tab_clicked,
                                                    scroll,section))
        hlay1.addWidget(del_section_button)            

        add_button = QPushButton()
        add_button.setText(_("New option"))
        add_button.clicked.connect(partial(self.new_line_clicked,vlay,section))
        hlay2.addWidget(add_button)
        
        hlay1.addStretch()
        hlay2.addStretch()
        
        vlay.addLayout(hlay1)
        vlay.addLayout(hlay2)
        widget.setLayout(vlay)
        return scroll,vlay        
        
    def new_section_clicked(self,widget):
        section = widget.text()
        if section:
            try:
                self.config.add_section(section)
                w,l = self.new_section(section)
                l.addStretch()
                index = self.page.addTab(w,section)
                self.page.setCurrentIndex(index)
            except Exception as e:
                printDebug(_("Add section exception: {}",e))
        widget.setText("")
        
    def save_as_clicked(self):
        filename = QFileDialog.getSaveFileName(self,_('Save as'),"",'INI (*.ini)')
        if filename:
            if '.ini' not in filename[0]:
                fn = filename[0] + '.ini'
            else:
                fn = filename[0]
            self.save_clicked(fn)
        
    def save_clicked(self,default_file=None):
        if default_file:
            ini = default_file
        else:
            ini = os.environ['INI_FILE_NAME']
            if not os.path.isfile(ini):
                ini = None
            
        if not ini:
            Notify.Warning(_("INI-file arg is not found."))
            printWarning(_("INI-file arg is not found."))
            return
                  
        default_hal = os.path.join(os.path.dirname(ini),"default.hal")  
        if not os.path.isfile(default_hal):
            copyfile(os.path.join(self.config_dir,"default_hal.cfg"),default_hal)
                    
        with open(ini, "w") as fp:
            if self.config._defaults:
                fp.write("[%s]\n" % DEFAULTSECT)
                for (key, value) in self.config._defaults.items():
                    value = toUnicode(value)
                    key = toUnicode(key)
                    if '\n' in value:
                        value = value.split('\n')
                    else:
                        value = [value]
                    for v in value:                            
                        if (v is not None) or (self.config._optcre == self.config.OPTCRE):
                            data = "{} = {}\n".format(key, v)
                            fp.write(data.encode('utf-8'))
                fp.write("\n")

            for section in self.config._sections:
                fp.write("[%s]\n" % section)
                for (key, value) in self.config._sections[section].items():
                    value = toUnicode(value)
                    key = toUnicode(key)
                    if key == "__name__":
                        continue
                    if '\n' in value:
                        value = value.split('\n')
                    else:
                        value = [value]
                    for v in value:    
                        if (v is not None) or (self.config._optcre == self.config.OPTCRE):
                            data = "{} = {}\n".format(key, v)
                            fp.write(data.encode('utf-8'))
                fp.write("\n")
        Notify.Info(_("Config file saved."))
    
    def fit_to_text(self,widget):
        height = widget.document().size().height()
        margin = widget.document().documentMargin()
        widget.setMaximumHeight(height+2*margin)
        
    def editing_finished(self,widget,section,option):
        self.fit_to_text(widget)
        self.config.set(section,option,widget.toPlainText())
        printDebug(_("Option changed: {} {} {}",section,option,widget.toPlainText()))
    
    def delete_option(self,widget,section,option):
        for i in reversed(range(widget.count())):
            item = widget.itemAt(i)
            item.widget().setVisible(False)
            item.widget().deleteLater()
            widget.removeItem(item)
        self.config.remove_option(section,option)
    
    def new_line(self,layout,section,option):
        label = QLabel(option)
        label.setObjectName("lbl_config_editor_{}_{}".format(section,option))
        layout.addWidget(label,2)
        edit = QTextEdit()
        edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        edit.setText(self.config.get(section,option))
        edit.document().documentLayout().documentSizeChanged.connect(
            partial(self.fit_to_text,edit))
        edit.textChanged.connect(partial(self.editing_finished,edit,section,option))
        edit.setObjectName("edit_config_editor_{}_{}".format(section,option))
        layout.addWidget(edit,6)
        button = QPushButton()
        button.setText(_("Delete"))
        button.clicked.connect(partial(self.delete_option,layout,section,option))
        layout.addWidget(button,1)

    def new_line_edit(self,widget,layout,section):
        text = widget.text()
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if type(item.widget()) in (QLineEdit,QPushButton):
                item.widget().setVisible(False)
                item.widget().deleteLater()
            layout.removeItem(item)
        if not text:
            return
        else:
            self.config.set(section,text,"0")
            self.new_line(layout,section,text)
            
    def new_line_clicked(self,layout,section):
        hlay = QHBoxLayout()
        edit = QLineEdit()
        edit.setObjectName("edit_config_editor_{}_{}".format(section,"new"))
        button = QPushButton()
        button.setText(_("Insert"))
        button.clicked.connect(partial(self.new_line_edit,edit,hlay,section))
        hlay.addWidget(edit,2)
        hlay.addWidget(button,7)
        layout.insertLayout(1,hlay)

    def delete_tab_clicked(self,widget,section):
        try:
            self.config.remove_section(section)
            index = self.page.indexOf(widget)
            self.page.removeTab(index)
        except Exception as e:
            printDebug(_("Delete section exception: {}",e))
    
    def load_default_clicked(self):
        self.load_clicked(os.path.join(self.config_dir,"default_ini.cfg"))
    
    def load_clicked(self,default_file=None,only_update=False):
        self.wizard = False
        self.run_wizard.setText(_("Run wizard"))
        
        if self.page.count() > 0:
            for i in reversed(range(self.page.count())):
                try:
                    self.page.widget(i).deleteLater()
                    self.page.removeTab(i)
                except Exception as e:
                    printDebug(_("Delete tab exception: {}",e))
                
        widget = QWidget()
        layout = QVBoxLayout()
        edit = QLineEdit()
        edit.setObjectName("edit_config_editor_{}_{}".format("new","new"))
        button = QPushButton()
        button.setText(_("Add new section"))
        button.clicked.connect(partial(self.new_section_clicked,edit))
        layout.addWidget(edit,2)
        layout.addWidget(button,7)
        layout.addStretch()
        widget.setLayout(layout)

        if default_file:
            ini = default_file
        else:
            ini = os.environ['INI_FILE_NAME']
        
        if ini:
            if not only_update:
                self.config = ConfigParser.ConfigParser(
                    dict_type=MultiOrderedDict,allow_no_value=True)
                self.config.optionxform = str
                self.config.read(ini)
        else:
            printWarning(_("INI-file arg is not found."))
            return

        self.page.addTab(widget,"+")   

        for s in sorted(self.config.sections()):
            widget,layout = self.new_section(s)
            
            for o in sorted(self.config.options(s)):
                lay = QHBoxLayout()
                self.new_line(lay,s,o)
                layout.addLayout(lay)
                
            layout.addStretch()
            self.page.addTab(widget,s)
            
        if self.page.count()>1:
            self.page.setCurrentIndex(1)
