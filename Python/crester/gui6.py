import sys, os
from PyQt5.QtCore import *
from  PyQt5.QtGui import *
from  PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np
from theory6 import *

pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

class crester(QMainWindow):
    def __init__(self, parent = None):
        super(crester, self).__init__(parent)
        self.acc = accelerator()

        stdicon = self.style().standardIcon
        style = QStyle
        self.setWindowTitle("Multi-Knob Control")

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)
        fileMenu.addAction(exitAction)

        self.timer = QTimer()
        self.timer.timeout.connect(self.acc.step)

        self.layout = QGridLayout()
        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        self.newButton = QPushButton('Reset')
        self.newButton.clicked.connect(self.newAcc)
        # self.cavitySelection = QComboBox()
        # self.cavitySelection.addItems([str(i) for i in range(6)])
        # self.cavitySelection.currentIndexChanged.connect(self.changeCavity)
        # self.cavitySelection.setCurrentIndex(0)
        self.cavityNumber = 0
        self.crestButton = QPushButton('Crest')
        self.crestButton.clicked.connect(self.autocrest)
        self.gradientWidget = QLineEdit('Gradient')
        self.gradientWidget.setReadOnly(True)
        self.calculatedCrestWidget = QLineEdit('Crest Phase')
        self.calculatedCrestWidget.setReadOnly(True)
        self.crestWidget = QLineEdit('Crest Phase')
        self.crestWidget.setReadOnly(False)
        self.crestWidget.editingFinished.connect(self.setCrest)
        self.acc.newGradient.connect(self.check_autocrest)

        self.controlLayout = QHBoxLayout()

        self.controlLayout.addWidget(self.newButton)
        # self.controlLayout.addWidget(self.cavitySelection)
        self.controlLayout.addWidget(self.crestButton)
        self.controlLayout.addWidget(self.gradientWidget)
        self.controlLayout.addWidget(self.crestWidget)
        self.controlLayout.addWidget(self.calculatedCrestWidget)
        self.layout.addLayout(self.controlLayout,0,0,1,6)
        self.plotWidget = range(6)
        for i in range(6):
            self.plotWidget[i] = plot(cavity=i)
            row = 1 if i < 3 else 2
            col = 2*np.mod(i,3)
            print 'row, col = ', row, col
            self.layout.addWidget(self.plotWidget[i],row,col,1,2)
            self.acc.newBPMReading.connect(self.plotWidget[i].newBPMReading)

        self.newAcc()

    def changeCavity(self):
        self.cavityNumber = self.cavitySelection.currentIndex()
        self.acc.cavityNumber = self.cavityNumber
        self.crestWidget.setText(str(self.acc.crest))

    def setCrest(self):
        self.acc.crest = float(str(self.crestWidget.text()))

    def newAcc(self):
        for i in range(6):
            self.acc.cavityNumber = i
            self.acc.crest = 360.0*np.random.random()
            self.acc.turnOffCavity()
        self.acc.cavityNumber = 0
        self.crestWidget.setText(str(self.acc.crest))
        self.acc.B = 0.05
        for i in range(6):
            self.plotWidget[i].data = np.empty((0,2),int)
        self.acc.reset()

    def autocrest(self):
        self.crestButton.clicked.disconnect(self.autocrest)
        self.crestButton.clicked.connect(self.stopCrest)
        self.cavityNumber = 0
        self.acc.cavityNumber = self.cavityNumber
        self.acc.turnOnCavity()
        self.acc.reset()
        self.acc.findCrest(0)
        self.crestButton.setText('Stop')
        self.timer.start(100)

    def check_autocrest(self, phasesign, gradient):
        self.gradientWidget.setText(str(gradient))
        fitting_params = self.acc.calculate_crest()
        self.calculatedCrestWidget.setText(str(self.acc.crest - np.mod(fitting_params[2],360)))
        self.plotWidget[self.cavityNumber].newFittedReading(self.acc.fittedData())
        if not phasesign * gradient > -1:
            if self.cavityNumber < 5:
                self.cavityNumber += 1
                self.acc.cavityNumber = self.cavityNumber
                self.acc.turnOnCavity()
                self.acc.reset()
                self.acc.findCrest(0)
            else:
                self.stopCrest()

    def stopCrest(self):
        self.timer.stop()
        self.crestButton.setText('Crest')
        self.crestButton.clicked.disconnect(self.stopCrest)
        self.crestButton.clicked.connect(self.autocrest)

class plot(pg.PlotWidget):
    def __init__(self, parent=None, cavity=0):
        super(plot, self).__init__(parent)
        self.cavity = cavity
        self.plotItem = self.getPlotItem()
        self.data = np.empty((0,2),int)
        self.bpmPlot = self.plotItem.plot(symbol='+', symbolPen='r')
        self.fittedPlot = self.plotItem.plot(pen='b')
        self.plotItem.showGrid(x=True, y=True)

    def newBPMReading(self, cavityNumber, data):
        if cavityNumber == self.cavity:
            self.data = np.append(self.data, [data], axis=0)
            self.bpmPlot.setData(self.data)

    def newFittedReading(self, data):
        self.fittedPlot.setData(np.array(data))

def main():
   app = QApplication(sys.argv)
   ex = crester()
   ex.show()
   # ex.testSleep()
   sys.exit(app.exec_())

if __name__ == '__main__':
   main()
