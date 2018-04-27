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
import signal
import sys

def signal_handler(signal, frame):
    global ex
    ex.saveData()
    print('You pressed Ctrl+C!')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
print('Press Ctrl+C')

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

class modelIndependentAnalysis(QObject):
    def __init__(self, parent = None):
        super(modelIndependentAnalysis, self).__init__(parent)
        print ('Starting up...')
        self.plots = {}
        self.monitor = multiMonitor(monitors)
        for i,m in enumerate(monitors):
            print ('Adding PV ', m)
            plot = responsePlotterTab(m,i)
            self.plots[m] = plot
            self.monitor.record.signal.timer.dataReady.connect(plot.plot.newBPMReading)
        # self.timer = QTimer()
        # self.timer.timeout.connect(self.saveData)
        # self.timer.start(60*1000)
        # print ('Starting save timer')

    def saveData(self):
        print ('Saving data...')
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

class responsePlotterTab(QObject):
    def __init__(self, monitorName=None, pos=0, parent=None):
        super(responsePlotterTab, self).__init__(parent)
        self.pos = pos
        self.plot = plot(self.pos)


class plot(QObject):
    def __init__(self, pos=0, parent=None):
        super(plot, self).__init__(parent)
        self.pos = pos
        self.color = 0
        self.eigenMode = 0
        self.data = np.empty((0,2),int)

    def reset(self):
        self.data = np.empty((0,2),int)

    def newBPMReading(self, data):
        if isinstance(data[1][self.pos],(int, float)):
            self.data = np.append(self.data, [[data[0], data[1][self.pos]]], axis=0)

def main():
    global app, ex
    app = QCoreApplication(sys.argv)
    ex = modelIndependentAnalysis()
    sys.exit(app.exec_())

if __name__ == '__main__':
   main()
