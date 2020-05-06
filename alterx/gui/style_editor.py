# -*- coding: utf-8 -*-
#
# AlterX GUI - style sheet editor
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

__all__ = ["StyleSheetEditor"]

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common.preferences import *
from alterx.common import *
from alterx.gui.util import *


class StyleSheetEditor(QWidget):
    mainwindow = None
    @classmethod
    def setMainwindow(cls, parent):
        cls.mainwindow = parent
        
    def __init__(self, parent=None, path=None):
        QWidget.__init__(self, parent)
        self.setMinimumSize(640, 480)

        layout = QVBoxLayout()
        
        label = QLabel("Stylesheet Editor")
        label.setObjectName("lbl_settings_styleeditor")
        layout.addWidget(label)
        
        layout_edit = QVBoxLayout()
        layout_view = QVBoxLayout()

        self.styleSheetCombo = QComboBox()
        layout.addWidget(self.styleSheetCombo)

        self.tabWidget = QTabWidget()
        layout.addWidget(self.tabWidget)

        self.styleTextView = QTextEdit()
        self.styleTextView.setReadOnly(True)
        layout_view.addWidget(self.styleTextView)

        self.copyButton = QPushButton()
        self.copyButton.setText(_("Copy and Edit"))
        self.copyButton.clicked.connect(self.on_copyButton_clicked)
        layout_view.addWidget(self.copyButton)

        viewWidget = QWidget()
        viewWidget.setLayout(layout_view)
        self.tabWidget.addTab(viewWidget, _("View"))

        self.styleTextEdit = QTextEdit()
        self.styleTextEdit.textChanged.connect(
            self.on_styleTextView_textChanged)
        layout_edit.addWidget(self.styleTextEdit)

        self.colorButton = QPushButton()
        self.colorButton.setText(_("Color"))
        self.colorButton.clicked.connect(self.on_colorButton_clicked)
        layout_edit.addWidget(self.colorButton)
        
        self.fontButton = QPushButton()
        self.fontButton.setText(_("Font"))
        self.fontButton.clicked.connect(self.on_fontButton_clicked)
        layout_edit.addWidget(self.fontButton)

        lay_h1 = QHBoxLayout()
        self.openButton = QPushButton()
        self.openButton.setText(_("Open"))
        self.openButton.clicked.connect(self.on_openButton_clicked)
        lay_h1.addWidget(self.openButton)
        self.saveButton = QPushButton()
        self.saveButton.setText(_("Save"))
        self.saveButton.clicked.connect(self.on_saveButton_clicked)
        lay_h1.addWidget(self.saveButton)
        layout_edit.addLayout(lay_h1)

        lay_h2 = QHBoxLayout()
        self.applyButton = QPushButton()
        self.applyButton.setText(_("Apply"))
        self.applyButton.clicked.connect(self.on_applyButton_clicked)
        lay_h2.addWidget(self.applyButton)
        self.clearButton = QPushButton()
        self.clearButton.setText(_("Clear"))
        self.clearButton.clicked.connect(self.on_clearButton_clicked)
        lay_h2.addWidget(self.clearButton)
        layout_edit.addLayout(lay_h2)

        editWidget = QWidget()
        editWidget.setLayout(layout_edit)
        self.tabWidget.addTab(editWidget, _("Edit"))

        self.setLayout(layout)
        self.applyButton.setEnabled(False)

        self.setWindowTitle(_("Style sheet editor"))
        
        if self.mainwindow:
            self.origStyleSheet = self.mainwindow.styleSheet()
            self.styleTextView.setPlainText(self.origStyleSheet)
            
        self.setPath()

        self.styleSheetCombo.currentIndexChanged.connect(self.selectionChanged)

    def setPath(self):
        self.styleSheetCombo.addItem('Default')
        model = self.styleSheetCombo.model()

        try:
            fileNames = [f for f in os.listdir(
                STYLESHEET_DIR) if f.endswith('.qss')]
            for i in(fileNames):
                item = QStandardItem(i)
                item.setData(STYLESHEET_DIR, role=Qt.UserRole + 1)
                model.appendRow(item)
        except Exception as e:
            print(e)

    def selectionChanged(self, i):
        path = self.styleSheetCombo.itemData(i, role=Qt.UserRole + 1)
        name = self.styleSheetCombo.itemData(i, role=Qt.DisplayRole)
        if name == 'Default':
            sheetName = name
        else:
            sheetName = os.path.join(path, name)
        self.loadStyleSheet(sheetName)
        PREF.putpref("stylesheet", name)

    def on_styleTextView_textChanged(self):
        self.applyButton.setEnabled(True)

    def on_applyButton_clicked(self):
        if self.mainwindow:
            if self.tabWidget.currentIndex() == 0:
                self.mainwindow.setStyleSheet(self.styleTextView.toPlainText())
            else:
                self.mainwindow.setStyleSheet(self.styleTextEdit.toPlainText())

    def on_openButton_clicked(self):
        dialog = QFileDialog(self)
        dialog.setDirectory(STYLESHEET_DIR)
        fileName, _ = dialog.getOpenFileName()
        if fileName:
            file = QFile(fileName)
            file.open(QFile.ReadOnly)
            stylesheet = file.readAll()
            try:
                # Python v2.
                stylesheet = unicode(stylesheet, encoding='utf8')
            except NameError:
                # Python v3.
                stylesheet = str(styleSheet, encoding='utf8')

            self.styleTextView.setPlainText(stylesheet)

    def on_saveButton_clicked(self):
        dialog = QFileDialog()
        dialog.setFilter(dialog.filter()|QDir.Hidden)
        dialog.setDefaultSuffix("qss")
        dialog.setDirectory(STYLESHEET_DIR)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters(["QSS (*.qss)"])
        if dialog.exec_() == QDialog.Accepted:
            fileName = dialog.selectedFiles()[0]
            self.saveStyleSheet(fileName)
            if self.styleSheetCombo.currentText() != fileName:
                model = self.styleSheetCombo.model()
                item = QStandardItem(os.path.basename(fileName))
                item.setData(STYLESHEET_DIR, role=Qt.UserRole + 1)
                model.appendRow(item)

    def on_clearButton_clicked(self):
        self.styleTextEdit.clear()

    def on_copyButton_clicked(self):
        self.styleTextEdit.setPlainText(self.styleTextView.toPlainText())
        self.tabWidget.setCurrentIndex(1)

    def on_colorButton_clicked(self):
        _color = QColorDialog.getColor()
        if _color.isValid():
            Color = _color.name()
            self.colorButton.setStyleSheet(
                'QPushButton {background-color: %s ;}' % Color)
            self.styleTextEdit.insertPlainText(Color)
            
    def on_fontButton_clicked(self):
        _font,btn = QFontDialog.getFont()
        if btn:
            self.styleTextEdit.insertPlainText((
                "font-family: {};\n"
                "font-size: {}pt;\n"
                "font-style: {};\n"
                "font-weight: {};\n"
                "text-decoration: {};\n"
                ).format(_font.family(),
                        _font.pointSize(),
                        ["normal","bold","italic","oblique"][_font.style()+1],
                        _font.weight(),
                        "underline " if _font.underline() else " " +
                        "line-through" if _font.strikeOut() else " "))

    def loadStyleSheet(self, sheetName):
        if not sheetName == 'Default':
            qssname = os.path.join(STYLESHEET_DIR, sheetName)
            file = QFile(qssname)
            file.open(QFile.ReadOnly)
            styleSheet = file.readAll()
            try:
                # Python v2.
                styleSheet = unicode(styleSheet, encoding='utf8')
            except NameError:
                # Python v3.
                styleSheet = str(styleSheet, encoding='utf8')
        else:
            styleSheet = self.origStyleSheet

        self.styleTextView.setPlainText(styleSheet)

    def saveStyleSheet(self, fileName):
        styleSheet = self.styleTextEdit.toPlainText()
        file = QFile(fileName)
        if file.open(QFile.WriteOnly):
            QTextStream(file) << styleSheet
        else:
            QMessageBox.information(
                self, _("Unable to open file"), file.errorString())
