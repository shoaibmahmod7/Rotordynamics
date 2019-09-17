﻿# -*- coding: utf-8 -*-
#
# Generated by App framework
#
# WARNING! All changes made outside the custom sections may be lost

import traceback
from PySide2 import QtCore, QtGui, QtWidgets
from ui_mainform import Ui_MainForm
# import apps
# import AME
# import amepyplot
import numpy as np
# import glob, cPickle
from functools import partial
from plant_widgets import *
from tuning_widgets import *
from utils import *

"""
DESCRIPTION: PID tuner, Main window

DATE OF CREATION/AUTHOR : 16/10/2018 B.Lecointre

Siemens Industry Software SAS
7 place des Minimes
42300 Roanne - France
tel: (33).04.77.23.60.30
fax: (33).04.77.23.60.31
www.siemens.com/plm

Copyright 2018 Siemens Industry Software NV
"""


# def runApp(*args, **kwargs):
#     apps.createEmbeddedApp(MainForm, *args, **kwargs)

class MainForm(QtWidgets.QMainWindow, Ui_MainForm):
    """
    The MainForm class defines the app window
    """

    # >>>>>>> Extra Class variables declaration here
    # <<<<<<< End of class variables declaration

    def __init__(self, appObject, *args, **kwargs):
        """
        Default constructor
        """
        super(MainForm, self).__init__(*args, **kwargs)

        self.appObject = appObject
        self.setupUi(self)
        self.doAutoAssociations(appObject)

        # >>>>>>> Extra initialization declarations here
        self.filename = self.appObject.circuitFilePath()
        self.resize(700,300)

        # Upper banner with workflow and option widgets
        labels = ["Plant identification", "PID tuning"]
        self.workflowViewer = WorkflowViewerLight(labels)
        self.workflowViewer.setAvailables([1, 1])
        self.workflowViewer.setSelected(0)          # initialize selection
        iconParam = QtGui.QPixmap(os.path.dirname(__file__) + "/images/options_pix16.png")
        self.optionsButton = QtWidgets.QPushButton(iconParam, "Options")
        self.optionsButton.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        topLayout = QtWidgets.QHBoxLayout()
        topLayout.addWidget(self.workflowViewer)
        topLayout.addWidget(QtWidgets.QFrame())  # alternative to stretch which is not compatible with the workflow widget
        topLayout.addWidget(QtWidgets.QFrame())
        topLayout.addWidget(QtWidgets.QFrame())
        topLayout.addWidget(QtWidgets.QFrame())
        topLayout.addWidget(self.optionsButton)

        # Tabs
        self.tabModel = QtWidgets.QTabWidget()
        self.tabTune = QtWidgets.QTabWidget()

        # Tab: "plant model" / Open-loop plots
        self.plantLin = PlantLin(self)
        self.plotPlant = PlotPlant()
        self.modelFit = ModelFit()

        # Tab: "pid tuning
        self.tuning = Tuning(self)

        # Status bar
        self.helpButton = QtWidgets.QPushButton("Help")
        self.backButton = QtWidgets.QPushButton("Back")
        self.nextButton = QtWidgets.QPushButton("Next")
        self.applyButton = QtWidgets.QPushButton("Apply")
        self.cancelButton = QtWidgets.QPushButton("Cancel")

        # Tab 1: "plant model"
        tabLayout = QtWidgets.QGridLayout()
        tabLayout.addWidget(self.plantLin, 0, 0)
        tabLayout.addWidget(self.plotPlant, 0, 1, 2, 1)
        tabLayout.addWidget(self.modelFit, 1, 0)
        tabLayout.setColumnStretch(1, 1)
        tabLayout.setColumnStretch(1, 1)
        tabPlant = QtWidgets.QWidget()
        tabPlant.setLayout(tabLayout)

        # Lower banner
        bannerLayout = QtWidgets.QHBoxLayout()
        bannerLayout.addWidget(self.helpButton)
        bannerLayout.addStretch(1)
        bannerLayout.addWidget(self.backButton)
        bannerLayout.addWidget(self.nextButton)
        bannerLayout.addWidget(self.applyButton)
        bannerLayout.addWidget(self.cancelButton)

        # Tab 2: "pid tuning"
        tabPID = self.tuning


        # Main window (assemble tabs)
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.tabBar().setVisible(False)
        self.tabs.addTab(tabPlant, "plant identification")
        self.tabs.addTab(tabPID, "pid tuning")
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(topLayout)
        mainLayout.addWidget(self.tabs)
        mainLayout.addLayout(bannerLayout)
        self.setWindowTitle("PID tuner")

        # central widget of QMainWindow
        centralWidget = QtWidgets.QDialog()
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)

        # initialize all widgets (before connecting them together)
        self.options = AppOptions()
        self.options.initUI(self)
        self.plantLin.initUI()
        self.modelFit.initUI()
        self.updatePlotPlant()
        self.tuning.modelUpdate()
        self.manageTabs(0)

        # Slots and signals (connect buttons and widgets together)
        self.optionsButton.clicked.connect(self.setOptions)
        self.workflowViewer.clicked.connect(self.manageWorkflowSignal)

        self.plantLin.plotRequest.connect(self.updatePlotPlant)
        self.modelFit.plotRequest.connect(self.updatePlotPlant)
        self.plantLin.plotRequest.connect(self.tuning.modelUpdate)
        self.modelFit.plotRequest.connect(self.tuning.modelUpdate)

        self.applyButton.clicked.connect(self.tuning.applyGains)

        self.backButton.clicked.connect(partial(self.manageTabs, -1))
        self.nextButton.clicked.connect(partial(self.manageTabs, 1))
        self.plantLin.plotRequest.connect(partial(self.manageTabs, 0))
        self.modelFit.plotRequest.connect(partial(self.manageTabs, 0))

        self.cancelButton.clicked.connect(self.onCancel)
        self.helpButton.clicked.connect(self.showHelp)

        # Default values
        self.tol = 1.0e-9  # tolerance for simplification (threshold corresponding to zero)
        self.saveOnClose = True

        # tooltips
        self.applyButton.setToolTip("Apply PID parameters to PID submodel")

    # def showHelp(self):
    #     """ link to help page """
    #     apps.utils.showHelpKeyword("pidTuner")

    def updatePlotPlant(self):
        # update model estimate fitting options (before plot to have the match index)
        if self.plantLin.status > 0:
            self.modelFit.findBestButton.setEnabled(True)
            if self.modelFit.fitType.currentIndex() > 0:
                self.modelFit.fitParButton.setEnabled(True)
            else:
                self.modelFit.fitParButton.setEnabled(False)
        else:
            self.modelFit.fitParButton.setEnabled(False)
            self.modelFit.findBestButton.setEnabled(False)

        # update plots
        self.plotPlant.updateUI()

    def setOptions(self):
        """ Show option widget """
        tmp = self.options.exec_()

        # refresh plots
        self.updatePlotPlant()
        self.tuning.updateUI()

    def manageWorkflowSignal(self, val):
        """ convert selected step for use in manageTabs """
        currentStep = self.tabs.currentIndex()
        if val == 0 and currentStep == 1:
            self.manageTabs(-1)
        elif val == 1 and currentStep == 0:
            self.manageTabs(1)
        else:
            return

    def manageTabs(self, step=0):
        """
        Manage workflow between tabs
        Optional step input is request to move to next tab (+1) or previous tab (-1)
        Step = 0 is used for signals that trigger change in button status
        """
        # manage on/off status
        if self.tabs.currentIndex() == 0:
            self.backButton.setEnabled(False)
            self.applyButton.setEnabled(False)
            if self.plantLin.status >= 1 or self.modelFit.status == 1:
                self.nextButton.setEnabled(True)
            else:
                self.nextButton.setEnabled(False)
        elif self.tabs.currentIndex() == 1:
            self.backButton.setEnabled(True)
            self.nextButton.setEnabled(False)
            self.applyButton.setEnabled(True)

        # change tab
        if self.nextButton.isEnabled() and step == 1:
            # move to tab 2
            self.tabs.setCurrentIndex(1)
            self.tabs.setTabEnabled(0, False)
            self.tabs.setTabEnabled(1, True)
            self.workflowViewer.setSelected(1)
            self.manageTabs(0)
        if self.backButton.isEnabled() and step == -1:
            # move to tab 1
            self.tabs.setCurrentIndex(0)
            self.tabs.setTabEnabled(0, True)
            self.tabs.setTabEnabled(1, False)
            self.workflowViewer.setSelected(0)
            self.manageTabs(0)

    def onCancel(self):
        """ Close app """
        self.saveOnClose = True
        MainForm.close(self)

    def close_gui(self):
        """
        Close the GUI on click
        """
        MainForm.close(self)

    def onLaunch(self):
        """
        Executed just before the form is made visible.
        Returns whether the window can be launched.
        """
        accept_launch = True
        # >>>>>>> Custom code here

        # <<<<<<< End of custom code
        return accept_launch

    def onClose(self):
        """
        Executed just before closing the form.
        Returns whether the window can be closed.
        - resultCode: dialog's results code when closing the form,
                      can be MainForm.Accepted (1) or MainForm.Rejected (0)
        """
        if self.saveOnClose == False :
            # exit without saving (not active in this version of the App)
            accept_close = True
            return accept_close

        # save current user settings for reloading at next opening
        # from plantLin widget
        settings = dict()
        settings["inputItem"] = self.plantLin.inputList.currentIndex()
        settings["outputItem"] = self.plantLin.outputList.currentIndex()
        settings["resItem"] = self.plantLin.resList.currentIndex()
        settings["tLinItem"] = self.plantLin.tLinList.currentIndex()
        s = cPickle.dumps(settings)
        self.appObject.saveAttribute("plantLinSettings", str(s))

        # from modelFit widget
        settings = dict()
        settings["fitItem"] = self.modelFit.fitType.currentIndex()
        settings["modParam"] = self.modelFit.modParam
        s = cPickle.dumps(settings)
        self.appObject.saveAttribute("modelFitSettings", str(s))

        # from tuning widget
        settings = dict()
        settings["fPid"] = self.tuning.fPid.text()
        s = cPickle.dumps(settings)
        self.appObject.saveAttribute("tuningSettings", str(s))

        # for options widget
        settings = self.options.values
        s = cPickle.dumps(settings)
        self.appObject.saveAttribute("optionsSettings", str(s))

        accept_close = True
        return accept_close

if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    ex = MainForm()
    ex.show()
    sys.exit(app.exec_()) 