import pv
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

testpv = PVBuffer('VA1IGA01_P')
print (testpv)
exit()

class testPV(QMainWindow):
    def __init__(self, parent = None):
        super(testPV, self).__init__(parent)
        self.testpv = PVBuffer('VA1IGA01_P')

        stdicon = self.style().standardIcon
        style = QStyle
        self.setWindowTitle("RF Cavity Cresting Application")

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)
        fileMenu.addAction(exitAction)

        self.layout = QGridLayout()
        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        self.pvWidget = epicsTextWidget(self.pv)
        self.layout.addWidget(self.pvWidget,0,0)

class epicsTextWidget(QWidget):
    def __init__(self, pv=None, parent = None):
        super(epicsTextWidget, self).__init__(parent)
        self.pv = pv

        self.widget = QWidget()
        self.layout = QHBoxLayout()
        self.widget.setLayout(self.layout)

        self.label = QLabel(self.pv.name)
        self.textBox = QLineEdit()
        self.textBox.setReadOnly(True)

        self.pv.newValue.connect(self.updateValue)

    def self.updateValue(self, time, value):
        self.textBox.setText(str(value))


def main():
   app = QApplication(sys.argv)
   ex = testPV()
   ex.show()
   sys.exit(app.exec_())
