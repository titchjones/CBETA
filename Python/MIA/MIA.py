import sys, os
from PyQt5.QtCore import *
from  PyQt5.QtGui import *
from  PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np
import random, time, datetime
sys.path.append(os.path.dirname( os.path.abspath(__file__)) + "/../")
from generic.pv import *
from dataRecorder.signalRecord import *
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

with open(os.path.dirname( os.path.abspath(__file__))+'/MIASettings.yaml', 'r') as infile:
    responseSettings = yaml.load(infile)

monitors = responseSettings['monitors']

class modelIndependentAnalysis(QMainWindow):
    def __init__(self, parent = None):
        super(modelIndependentAnalysis, self).__init__(parent)

        stdicon = self.style().standardIcon
        style = QStyle
        self.setWindowTitle("Model Independent Analysis Application")

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)
        fileMenu.addAction(exitAction)

        startUpdating = QAction('&Save Data', self)
        startUpdating.setShortcut('Ctrl+S')
        startUpdating.setStatusTip('Save all data')
        startUpdating.triggered.connect(self.saveData)
        fileMenu.addAction(startUpdating)

        self.layout = QGridLayout()
        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        self.plots = {}
        self.tabs = QTabWidget()
        self.monitor = multiMonitor(monitors)
        self.svdmonitor = reconstructData()
        self.monitor.record.signal.timer.dataReady.connect(self.svdmonitor.newBPMReading)
        for i,m in enumerate(monitors):
            plot = responsePlotterTab(m,i)
            self.tabs.addTab(plot, m)
            self.plots[m] = plot
            self.monitor.record.signal.timer.dataReady.connect(plot.plot.newBPMReading)
        self.layout.addWidget(self.tabs,0,0,6,6)

    def saveData(self):
        prefix = str(datetime.datetime.now().date()) + '_' + str(datetime.datetime.now().time()).replace(':', '.')
        self.h5file = tables.open_file(prefix+'_MIA_data.h5', mode = "w")
        self.rootnode = self.h5file.get_node('/')
        group = self.h5file.create_group('/', 'MIA' ,'MIA Data')
        for m in self.plots:
            table = self.h5file.create_table(group, m, recordRMData, m+' Data')
            row = table.row
            data = self.plots[m].plot.data
            self.saveRow(row, data)
            table.flush()
        self.h5file.close()

    def saveRow(self, row, data):
        for a, m in data:
            row['actuator'], row['monitor'] = a, m
            row.append()

    def closeEvent(self, event):
        self.saveData()
        event.accept() # let the window close

    def printData(self, data):
        print (data)

class fakePVObject(QObject):

    def __init__(self, pv=None, parent=None):
        super(fakePVObject, self).__init__(parent)
        self.name = pv

    def get(self):
        return random.random()

class multiMonitor(QObject):

    def __init__(self, pvs=None, parent=None):
        super(multiMonitor, self).__init__(parent)
        self.names = pvs
        self.pvs = OrderedDict([])
        self.records = {}
        for m in self.names:
            self.addMonitor(m)
        self.record = signalRecord(self.records, 'multiMonitor', QColor(0,0,0), 1./5., 2**8, self.get)
        self.record.start()

    def addMonitor(self, name):
        self.pvs[name] = PVObject(name)

    def get(self):
        return [self.pvs[m].get()[1] for m in self.pvs]

class recordRMData(tables.IsDescription):
    actuator  = tables.Float64Col()     # double (double-precision)
    monitor  = tables.Float64Col()

class responsePlotterTab(QWidget):
    def __init__(self, monitorName=None, pos=0, parent=None):
        super(responsePlotterTab, self).__init__(parent)
        self.pos = pos
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.buttonLayout = QHBoxLayout()
        self.updateButton = QPushButton('Update Plot')
        self.updateButton.setMaximumWidth(100)
        self.buttonLayout.addWidget(self.updateButton)
        self.layout.addLayout(self.buttonLayout)

        self.plot = plot(self.pos)
        self.updateButton.clicked.connect(self.plot.updateBPMPlot)
        self.layout.addWidget(self.plot)

class HAxisTime(pg.AxisItem):
    def __init__(self, orientation=None, pen=None, linkView=None, parent=None, maxTickLength=-5, showValues=True):
        super(HAxisTime, self).__init__(parent=parent, orientation=orientation, linkView=linkView)
        self.dateTicksOn = True
        self.autoscroll = True

    def updateTimeOffset(self,time):
        self.timeOffset = time
        self.resizeEvent()
        self.update()

    def tickStrings(self, values, scale, spacing):
        if not hasattr(self, 'fixedtimepoint'):
            self.fixedtimepoint = round(time.time(),2)
        if self.dateTicksOn:
            if self.autoscroll:
                reftime = round(time.time(),2)
            else:
                reftime = self.fixedtimepoint
            try:
                ticks = [time.strftime("%H:%M:%S", time.localtime(x)) for x in values]
            except:
                ticks = []
            return ticks
        else:
            places = max(0, np.ceil(-np.log10(spacing*scale)))
            strings = []
            for v in values:
                vs = v * scale
                if abs(vs) < .001 or abs(vs) >= 10000:
                    vstr = "%g" % vs
                else:
                    vstr = ("%%0.%df" % places) % vs
                strings.append(vstr)
            return strings

class plot(pg.PlotWidget):
    def __init__(self, pos=0, parent=None):
        super(plot, self).__init__(parent, axisItems={'bottom': HAxisTime(orientation = 'bottom')})
        self.pos = pos
        self.plotItem = self.getPlotItem()
        self.plotItem.showGrid(x=True, y=True)
        self.data = np.empty((0,2),int)
        self.bpmPlot = self.plotItem.plot(pen='b')
        self.reconstructedPlot = self.plotItem.plot(pen='r')
        self.color = 0
        self.eigenMode = 0

    def reset(self):
        self.data = np.empty((0,2),int)
        self.bpmPlot.clear()
        self.fittedPlot.clear()

    def newBPMReading(self, data):
        if isinstance(data[1][self.pos],(int, float)):
            self.data = np.append(self.data, [[data[0], data[1][self.pos]]], axis=0)

    def updateBPMPlot(self):
        if self.isVisible():
            try:
                if len(self.data) > 10:
                    self.bpmPlot.setData(self.data)
            except:
                pass
        # self.updateReconstructedPlot()

    # def updateReconstructedPlot(self):
        # self.reconstructedPlot.setData(np.array(self.reconstructData(self.eigenMode)))

class reconstructData(QObject):
    def __init__(self, parent=None):
        super(reconstructData, self).__init__(parent)
        self.data = np.empty((0,len(monitors)),int)
        self.time = []

    def newBPMReading(self, data):
        self.data = self.data + [data[1]]
        self.time = self.time + [data[0]]
        # self.reconstructData()

    def reconstructData(self, e=0):
        u, s, vh = np.linalg.svd(self.data, full_matrices=False)
        news = np.zeros((len(s),))
        news[e] = s[e]
        print (s, news)
        return np.dot(u * news, vh)

def main():
    global app
    app = QApplication(sys.argv)
    ex = modelIndependentAnalysis()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
   main()
