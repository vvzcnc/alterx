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
        hlay = QHBoxLayout()
        save = QPushButton()
        save.setText("Save")
        save.clicked.connect(self.save)
        load = QPushButton()
        load.setText("Load")
        load.clicked.connect(self.load)        
        hlay.addWidget(load)
        hlay.addWidget(save)
        vlay.addLayout(hlay)
        self.page = QTabWidget()
        vlay.addWidget(self.page)
        self.setLayout(vlay)
    
    def save(self):
        ini = os.environ['INI_FILE_NAME']
        if ini:
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
        else:
            printWarning("INI-file args is not found.")
            return
    
    def load(self):
        if self.page.count() > 0:
            for i in reversed(range(self.page.count())):
                try:
                    self.page.widget(i).deleteLater()
                    self.page.removeTab(i)
                except Exception as e:
                    print("%s"%e)
                
        ini = os.environ['INI_FILE_NAME']
        if ini:
            self.config = ConfigParser(dict_type=MultiOrderedDict,allow_no_value=True)
            self.config.optionxform = str
            self.config.read(ini)
        else:
            printWarning("INI-file args is not found.")
            return
            
        def editing_finished(widget,section,option):
            fit_to_text(widget)
            self.config.set(section,option,widget.toPlainText())
            printDebug(_("Option changed: {} {} {}",section,option,widget.toPlainText()))
        
        def fit_to_text(widget):
            height = widget.document().size().height()
            margin = widget.document().documentMargin()
            widget.setMaximumHeight(height+2*margin)
        
        def delete_option(widget,section,option):
            for i in reversed(range(widget.count())):
                item = widget.itemAt(i)
                item.widget().setVisible(False)
                item.widget().deleteLater()
                widget.removeItem(item)
            self.config.remove_option(section,option)
        
        def new_line(lay,sect,opt):
            label = QLabel(opt)
            label.setObjectName("lbl_config_editor_{}_{}".format(sect,opt))
            lay.addWidget(label,2)
            edit = QTextEdit()
            edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            edit.setText(self.config.get(sect,opt))
            edit.document().documentLayout().documentSizeChanged.connect(partial(fit_to_text,edit))
            edit.textChanged.connect(partial(editing_finished,edit,sect,opt))
            edit.setObjectName("edit_config_editor_{}_{}".format(sect,opt))
            lay.addWidget(edit,6)
            del_button = QPushButton()
            del_button.setText(_("Delete"))
            del_button.clicked.connect(partial(delete_option,hlay,sect,opt))
            del_button.setMaximumWidth(100)
            lay.addWidget(del_button,1)
        
        for section in self.config.sections():
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            widget = QWidget()
            scroll.setWidget(widget)
            vlay = QVBoxLayout()
            vlay.setContentsMargins(20,20,20,20)

            def new_line_edit(widget,layout,sect):
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
                    self.config.set(sect,text,"0")
                    new_line(layout,sect,text)
                    
            def new_line_clicked(lay,sect):
                hlay = QHBoxLayout()
                edit = QLineEdit()
                edit.setObjectName("edit_config_editor_{}_{}".format(sect,"new"))
                edit.setMaximumWidth(300)
                ok_button = QPushButton()
                ok_button.setText(_("Ok"))
                ok_button.clicked.connect(partial(new_line_edit,edit,hlay,sect))
                ok_button.setMaximumWidth(50)
                hlay.addWidget(edit)
                hlay.addWidget(ok_button)
                hlay.addStretch()
                lay.insertLayout(1,hlay)
            
            add_button = QPushButton()
            add_button.setText(_("New"))
            add_button.clicked.connect(partial(new_line_clicked,vlay,section))
            add_button.setMaximumWidth(100)
            vlay.addWidget(add_button,1)
            
            for option in sorted(self.config.options(section)):
                hlay = QHBoxLayout()
                new_line(hlay,section,option)
                vlay.addLayout(hlay)
                
            vlay.addStretch()
            widget.setLayout(vlay)
            self.page.addTab(scroll,section)
