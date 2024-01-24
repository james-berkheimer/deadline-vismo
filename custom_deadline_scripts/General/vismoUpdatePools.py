"""
CustomQtDialog.py - Example of how to create a custom Qt dialog in Deadline monitor
Copyright Thinkbox Software 2016
"""

import sys

from System.IO import *
from Deadline.Scripting import *

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import PyQt5.QtCore
import PyQt5.QtWidgets
import PyQt5.QtGui

########################################################################
# Globals
########################################################################
dialog = None

########################################################################
# Custom QDialog with some basic controls.
########################################################################


class CustomQtDialog(QDialog):

    def __init__(self, parent=None):
        super(CustomQtDialog, self).__init__(parent)

        # set the main layout as a vertical one
        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)
        
        # Create lineEdit to add items to QListWidget
        self.addPool = QLineEdit()
        self.addPoolButton = QPushButton("Add")        
        
        # Create layout for addPool
        self.addPoolLayout = QHBoxLayout()
        self.addPoolLayout.addWidget(self.addPool)
        self.addPoolLayout.addWidget(self.addPoolButton)
        self.mainLayout.addLayout(self.addPoolLayout)
        
        # Create pool list
        existingPools = RepositoryUtils.GetPoolNames()
        self.poolList = QListWidget()
        for pool in existingPools:
            if str(pool) != 'none':
                self.poolList.addItem(pool)
        self.mainLayout.addWidget(self.poolList)     
        
        # Up/Down/rRmove buttons
        self.buttonLayout = QHBoxLayout()
        
        self.buttonUp = QPushButton("Up")
        self.buttonLayout.addWidget(self.buttonUp)
        
        self.buttonDown = QPushButton("Down")
        self.buttonLayout.addWidget(self.buttonDown)
        
        self.removePoolButton = QPushButton("Remove")
        self.buttonLayout.addWidget(self.removePoolButton)
        
        self.mainLayout.addLayout(self.buttonLayout)
        
        # label/close layout
        self.labelLayout = QHBoxLayout()
        
        self.displayLabel = QLabel("Edit pool list")        
        self.labelLayout.addWidget(self.displayLabel)
        
        self.applyButton = QPushButton("Apply Changes")
        self.labelLayout.addWidget(self.applyButton)
        
        self.mainLayout.addLayout(self.labelLayout)
        

        # hook up the button signals to our slots
        self.addPoolButton.clicked.connect(self.addPoolButtonPressed)
        self.buttonUp.clicked.connect(self.buttonUpPressed)
        self.buttonDown.clicked.connect(self.buttonDownPressed)
        self.removePoolButton.clicked.connect(self.removePoolButtonPressed)
        self.applyButton.clicked.connect(self.applyChangesPressed)

    @pyqtSlot(bool)
    def addPoolButtonPressed(self, checked):
        newPool = self.addPool.text()
        self.poolList.addItem(newPool)
        self.displayLabel.setText("Adding new pool: " + newPool)
    
    @pyqtSlot(bool)
    def buttonUpPressed(self, checked):
        currentRow = self.poolList.currentRow()
        currentItem = self.poolList.takeItem(currentRow)
        self.poolList.insertItem(currentRow - 1, currentItem)
        self.poolList.setCurrentItem(currentItem)
        self.displayLabel.setText("Moving Up: " + currentItem.text())

    @pyqtSlot(bool)
    def buttonDownPressed(self, checked):
        currentRow = self.poolList.currentRow()
        currentItem = self.poolList.takeItem(currentRow)
        self.poolList.insertItem(currentRow + 1, currentItem)
        self.poolList.setCurrentItem(currentItem)
        self.displayLabel.setText("Moving Down: " + currentItem.text())
        
    @pyqtSlot(bool)
    def removePoolButtonPressed(self, checked):
        currentRow = self.poolList.currentRow()
        currentItem = self.poolList.takeItem(currentRow)
        self.displayLabel.setText("Removing: " + currentItem.text())
        del(currentItem)
        
    @pyqtSlot(bool)
    def applyChangesPressed(self, checked):
        # Delete old pools from Repository
        for pool in RepositoryUtils.GetPoolNames():        
            if str(pool) != 'none':
                RepositoryUtils.DeletePool(str(pool))
        
        ## Add Pools to Repository
        newPoolList = []
        for i in range(self.poolList.count()):
            newPoolList.append(self.poolList.item(i).text()) 
            try:
                RepositoryUtils.AddPool(self.poolList.item(i).text())                
            except:
                print ("Pool %s already exists" % (self.poolList.item(i).text()))        
            
        # Set the slaves pool list
        for slave in RepositoryUtils.GetSlaveNames(True):
            RepositoryUtils.SetPoolsForSlave( slave, newPoolList )
            
        self.displayLabel.setText("Pools Updated!")

    @pyqtSlot(bool)
    def closeButtonPressed(self, checked):
        self.done(0)

########################################################################
# Main Function Called By Deadline
########################################################################


def __main__():
    global dialog

    # Create an instance of our custom dialog, and show it
    dialog = CustomQtDialog()
    dialog.setVisible(True)