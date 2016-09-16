# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gui_save_failed.ui'
#
# Created: Mon Sep 12 13:40:02 2016
#      by: PyQt4 UI code generator 4.8.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_frmSpeichern(object):
    def setupUi(self, frmSpeichern):
        frmSpeichern.setObjectName(_fromUtf8("frmSpeichern"))
        frmSpeichern.resize(835, 561)
        self.gridLayout = QtGui.QGridLayout(frmSpeichern)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.frmTabelle = QtGui.QFrame(frmSpeichern)
        self.frmTabelle.setEnabled(True)
        self.frmTabelle.setMinimumSize(QtCore.QSize(500, 500))
        self.frmTabelle.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frmTabelle.setFrameShadow(QtGui.QFrame.Raised)
        self.frmTabelle.setObjectName(_fromUtf8("frmTabelle"))
        self.gridLayout.addWidget(self.frmTabelle, 0, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btnSave = QtGui.QPushButton(frmSpeichern)
        self.btnSave.setObjectName(_fromUtf8("btnSave"))
        self.horizontalLayout.addWidget(self.btnSave)
        spacerItem1 = QtGui.QSpacerItem(80, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.btnClose = QtGui.QPushButton(frmSpeichern)
        self.btnClose.setObjectName(_fromUtf8("btnClose"))
        self.horizontalLayout.addWidget(self.btnClose)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)

        self.retranslateUi(frmSpeichern)
        QtCore.QMetaObject.connectSlotsByName(frmSpeichern)

    def retranslateUi(self, frmSpeichern):
        frmSpeichern.setWindowTitle(QtGui.QApplication.translate("frmSpeichern", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.btnSave.setText(QtGui.QApplication.translate("frmSpeichern", "Save Records", None, QtGui.QApplication.UnicodeUTF8))
        self.btnClose.setText(QtGui.QApplication.translate("frmSpeichern", "Close", None, QtGui.QApplication.UnicodeUTF8))

