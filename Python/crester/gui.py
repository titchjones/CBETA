import sys, os
from PyQt5.QtCore import *
from  PyQt5.QtGui import *
from  PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np
from theory import *

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

        self.plotWidget = plot()

        self.layout.addWidget(self.newButton,0,0)
        self.layout.addWidget(self.crestButton,0,1)
        self.layout.addWidget(self.gradientWidget,0,2)
        self.layout.addWidget(self.crestWidget,0,3)
        self.layout.addWidget(self.calculatedCrestWidget,0,4)
        self.layout.addWidget(self.plotWidget,1,0,1,10)

        self.acc.newBPMReading.connect(self.plotWidget.newBPMReading)

        self.newAcc()

    def setCrest(self):
        self.acc.crest = float(str(self.crestWidget.text()))

    def newAcc(self):
        self.acc.crest = 360.0*np.random.random()
        self.crestWidget.setText(str(self.acc.crest))
        self.acc.amplitude = 20e6
        self.acc.B = 0.327
        self.plotWidget.data = np.empty((0,2),int)
        self.acc.reset()

    def autocrest(self):
        self.acc.findCrest(0)
        self.crestButton.setText('Stop')
        self.crestButton.clicked.disconnect(self.autocrest)
        self.crestButton.clicked.connect(self.stopCrest)
        self.timer.start(100)

    def check_autocrest(self, phasesign, gradient):
        self.gradientWidget.setText(str(gradient))
        fitting_params = self.acc.calculate_crest()
        self.calculatedCrestWidget.setText(str(self.acc.crest - np.mod(fitting_params[2],360)))
        self.plotWidget.newFittedReading(self.acc.fittedData())
        if not phasesign * gradient > -1:
            self.stopCrest()

    def stopCrest(self):
        self.timer.stop()
        self.crestButton.setText('Crest')
        self.crestButton.clicked.disconnect(self.stopCrest)
        self.crestButton.clicked.connect(self.autocrest)

class plot(pg.PlotWidget):
    def __init__(self, parent = None):
        super(plot, self).__init__(parent)
        self.plotItem = self.getPlotItem()
        self.data = np.empty((0,2),int)
        self.bpmPlot = self.plotItem.plot(symbol='+', symbolPen='r')
        self.fittedPlot = self.plotItem.plot(pen='b')
        self.plotItem.showGrid(x=True, y=True)

    def newBPMReading(self, data):
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
