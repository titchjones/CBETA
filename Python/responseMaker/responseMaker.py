import sys, os
from PyQt5.QtCore import *
from  PyQt5.QtGui import *
from  PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np
import random, time
sys.path.append(os.path.dirname( os.path.abspath(__file__)) + "/../")
from generic.pv import *
pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
from collections import OrderedDict
import yaml
import tables as tables


_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG

def dict_representer(dumper, data):
    return dumper.represent_dict(data.iteritems())

def dict_constructor(loader, node):
    return OrderedDict(loader.construct_pairs(node))

yaml.add_representer(OrderedDict, dict_representer)
yaml.add_constructor(_mapping_tag, dict_constructor)

with open(os.path.dirname( os.path.abspath(__file__))+'/responseSettings.yaml', 'r') as infile:
    responseSettings = yaml.load(infile)

monitors = responseSettings['monitors']
actuators = responseSettings['actuators']

class responseMaker(QMainWindow):
    def __init__(self, parent = None):
        super(responseMaker, self).__init__(parent)

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

        self.newButton = QPushButton('Reset')

        self.tabs = QTabWidget()
        for a in actuators:
            self.tabs.addTab(responsePlotterTab(a), a)
        # self.layout.addWidget(self.newButton,0,0)
        self.layout.addWidget(self.tabs,0,0,6,6)

class monitor(PVBuffer):

    emitAverageSignal = pyqtSignal(str, list)

    def __init__(self, pv=None, actuator=None, parent=None):
        super(monitor, self).__init__(pv, parent)
        self.name = pv
        self.actuator = actuator
        #self._value = random.random()-0.5

    def value(self):
        return [self.actuator.name, [self.actuator.value(), self.mean]]

    def emitAverage(self):
        a, v = self.value()
        self.emitAverageSignal.emit(a,v)

#    def reset(self):
#        pass

#    def mean(self):
#        return 0.001*self.actuator.value()**2 * self._value

class corrector(QObject):
    def __init__(self, pv=None, parent=None):
        super(corrector, self).__init__(parent)
        self.name = pv
        self._value = 0

    def value(self):
        return self._value

    def setValue(self, value):
        self._value = value

class recordRMData(tables.IsDescription):
    actuator  = tables.Float64Col()     # double (double-precision)
    monitor  = tables.Float64Col()


class responsePlotterTab(QWidget):
    def __init__(self, actuator=None, parent=None):
        super(responsePlotterTab, self).__init__(parent)
        self.name = actuator
        self.pv = corrector(self.name)

        self.monitors = []
        for m in monitors:
            self.monitors.append(monitor(m, self.pv))

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.buttonLayout = QHBoxLayout()
        self.runButton = QPushButton('Run')
        self.runButton.setMaximumWidth(100)
        self.runButton.clicked.connect(self.runResponse)
        self.buttonLayout.addWidget(self.runButton)
        self.saveButton = QPushButton('Save Data')
        self.saveButton.setMaximumWidth(100)
        self.saveButton.clicked.connect(self.saveData)
        self.buttonLayout.addWidget(self.saveButton)

        self.layout.addLayout(self.buttonLayout)

        self.plotTabs = QTabWidget()
        self.plots = {}
        self.layout.addWidget(self.plotTabs)
        for m in self.monitors:
            plot = responsePlot(actuator)
            self.plots[m.name] = plot
            self.plotTabs.addTab(plot, m.name)
            m.emitAverageSignal.connect(plot.newBPMReading)

    def saveData(self):
        self.h5file = tables.open_file(self.name+'.h5', mode = "w", title = self.name)
        self.rootnode = self.h5file.get_node('/')
        group = self.h5file.create_group('/', 'Data', 'RM Data')
        for m in self.monitors:
            table = self.h5file.create_table(group, m.name, recordRMData, m.name)
            row = table.row
            data = self.plots[m.name].data
            for a, m in data:
                row['actuator'], row['monitor'] = a, m
                row.append()
            table.flush()
        self.h5file.close()

    def runResponse(self):
        min = -0.1#self.pv.pv.lower_disp_limit
        max = 0.1#self.pv.pv.upper_disp_limit
        range = self.generateRange(min, max)
        startValue = self.pv.value()
        for i in range:
            self.pv.setValue(startValue+i)
            for m in self.monitors:
                m.reset()
            length = np.min([m.length for m in self.monitors])
            while length < 1:
                length = np.min([m.length for m in self.monitors])
            for m in self.monitors:
                m.emitAverage()
        self.pv.setValue(0)

    def generateRange(self, min, max):
        data = []
        value = 10.0
        while abs(value) > 0.1:
            data.append(value)
            data.append(-1. * value)
            value = value / np.sqrt(2)
        data.append(0)
        data = np.array(data)
        data = ((data + 10) * ((max-min)/20)) + min
        return list(sorted(data))

class responsePlot(pg.PlotWidget):
    def __init__(self, actuator=None, parent=None):
        super(responsePlot, self).__init__(parent)
        self.actuator = actuator
        self.plotItem = self.getPlotItem()
        self.data = np.empty((0,2),int)
        self.bpmPlot = self.plotItem.plot(symbol='+', symbolPen='r')
        self.fittedPlot = self.plotItem.plot(pen='b')
        self.plotItem.showGrid(x=True, y=True)

    def reset(self):
        self.data = np.empty((0,2),int)
        self.bpmPlot.clear()
        self.fittedPlot.clear()

    def newBPMReading(self, actuator, data):
        if actuator == self.actuator:
            self.data = np.append(self.data, [data], axis=0)
            self.bpmPlot.setData(self.data)

    def newFittedReading(self, data):
        self.fittedPlot.setData(np.array(data))

def main():
   app = QApplication(sys.argv)
   ex = responseMaker()
   ex.show()
   # ex.testSleep()
   sys.exit(app.exec_())

if __name__ == '__main__':
   main()
