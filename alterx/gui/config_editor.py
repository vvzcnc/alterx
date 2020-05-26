# -*- coding: utf-8 -*-
#
# AlterX GUI - widgets
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
        run_wizard = QPushButton()
        run_wizard.setText(_("Run wizard"))
        run_wizard.clicked.connect(self.run_wizard_clicked)
        hlay.addWidget(load_default)
        hlay.addWidget(load)
        hlay.addWidget(run_wizard)
        hlay.addWidget(save)
        hlay.addWidget(save_as)
        vlay.addLayout(hlay)
        self.page = QTabWidget()
        vlay.addWidget(self.page)
        self.setLayout(vlay)
        self.config_dir = pkg_resources.resource_filename("alterx", "configs")
        self.load_clicked()

    def run_wizard_clicked(self):
        if self.page.count() > 0:
            for i in reversed(range(self.page.count())):
                try:
                    self.page.widget(i).deleteLater()
                    self.page.removeTab(i)
                except Exception as e:
                    printDebug(_("Delete tab exception: {}",e))

    def new_section(self,section):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        scroll.setWidget(widget)
    
        vlay = QVBoxLayout()
        vlay.setContentsMargins(20,20,20,20)
        hlay = QHBoxLayout()
        
        add_button = QPushButton()
        add_button.setText(_("New"))
        add_button.clicked.connect(partial(self.new_line_clicked,vlay,section))
        hlay.addWidget(add_button)
        
        del_section_button = QPushButton()
        del_section_button.setText(_("Delete section"))
        del_section_button.clicked.connect(partial(self.delete_tab_clicked,scroll,section))
        hlay.addWidget(del_section_button)            
        
        hlay.addStretch()
        vlay.addLayout(hlay)
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
            printWarning(_("INI-file arg is not found."))
            return
                  
        default_hal = os.path.join(os.path.dirname(ini),"default.hal")  
        if not os.path.isfile(default_hal):
            copyfile(os.path.join(self.config_dir,"default_hal.cfg"),default_hal)
                    
        with open(ini, "w") as fp:
            if self.config._defaults:
                fp.write("[%s]\n" % DEFAULTSECT)
                for (key, value) in self.config._defaults.items():
                    if '\n' in value:
                        value = value.split('\n')
                    else:
                        value = [value]
                    for v in value:                            
                        if (v is not None) or (self.config._optcre == self.config.OPTCRE):
                            key = " = ".join((key, str(v)))
                        fp.write("%s\n" % (key))
                fp.write("\n")
            for section in self.config._sections:
                fp.write("[%s]\n" % section)
                for (key, value) in self.config._sections[section].items():
                    if key == "__name__":
                        continue
                    if '\n' in value:
                        value = value.split('\n')
                    else:
                        value = [value]
                    for v in value:                            
                        if (v is not None) or (self.config._optcre == self.config.OPTCRE):
                            k = " = ".join((key, str(v)))
                        fp.write("%s\n" % (k))
                fp.write("\n")
    
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
        edit.document().documentLayout().documentSizeChanged.connect(partial(self.fit_to_text,edit))
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
    
    def load_clicked(self,default_file=None):
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

        self.config = ConfigParser(dict_type=MultiOrderedDict,allow_no_value=True)
        self.config.optionxform = str
        self.page.addTab(widget,"+")        
                
        if default_file:
            ini = default_file
        else:
            ini = os.environ['INI_FILE_NAME']
        
        if ini:
            self.config.read(ini)
        else:
            printWarning(_("INI-file arg is not found."))
            return

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
