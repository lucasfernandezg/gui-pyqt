from PyQt5 import QtWidgets
import sys
from PyQt5.QtCore import Qt,pyqtSignal
from PyQt5.QtWidgets import QApplication


class MyWidget(QtWidgets):

    rightClicked = pyqtSignal()

    def __init__(self):
        super(MyWidget, self).__init__()

    def onRightClick(self):
        self.rightClicked.emit()

    def mousePressEvent(self, QMouseEvent):
        if QMouseEvent.button() == QtCore.Qt.LeftButton:
            self.onClicked()
        elif QMouseEvent.button() == QtCore.Qt.RightButton:
            #do what you want here
            self.onRightClick()
