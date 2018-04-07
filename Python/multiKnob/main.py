import sys, os
from PyQt4.QtCore import *
from  PyQt4.QtGui import *
import pyqtgraph as pg
import numpy as np
from epics import caget, caput, cainfo, PV
from collections import OrderedDict
import yaml

_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG

def dict_representer(dumper, data):
    return dumper.represent_dict(data.iteritems())

def dict_constructor(loader, node):
    return OrderedDict(loader.construct_pairs(node))

yaml.add_representer(OrderedDict, dict_representer)
yaml.add_constructor(_mapping_tag, dict_constructor)

with open(os.path.dirname( os.path.abspath(__file__))+'/pv_names.yaml', 'r') as infile:
    pv_names = yaml.load(infile)

class fakePV(QObject):

    emitSignal = pyqtSignal(str, float)

    def __init__(self, name):
        super(fakePV, self).__init__()
        self.name = name
        self.readPV = PV(self.name+':SETI')
        self.readPV.connect()
        # self.readPV.add_callback(self.valueChanged, type='value')
        self.writePV = PV(self.name+':SETI')
        self.writePV.connect()
        self.statusPV = PV(self.name+':Sta')
        # self.statusPV.add_callback(self.valueChanged, type='status')
        self.statusPV.connect()
        self.timer = QTimer()
        self.timer.timeout.connect(self.Update)
        self.timer.start(100)

    def stop(self):
        self.timer.stop()

    @property
    def value(self):
        return self.readPV.get()

    def setValue(self, val):
        self.writePV.put(val)

    @property
    def status(self):
        return self.statusPV.get()

    @property
    def get(self):
        return self.value

    def Update(self):
        # self.readPV.run_callbacks()
        # self.statusPV.run_callbacks()
        self.valueChanged(type='value', value=self.value)
        self.valueChanged(type='status', value=self.status)

    def valueChanged(self, **kwargs):
        self.emitSignal.emit(kwargs['type'], kwargs['value'])

class multiKnob_GroupBox(QGroupBox):
    """Multiknob group box."""
    def __init__(self, parent = None):
        super(multiKnob_GroupBox, self).__init__(parent)
        self.setTitle('Multi-Knobs')
        self.table = QGridLayout()
        self.table.setRowStretch(0,0)
        for c,h in enumerate(['Enabled','Status', 'PV Name','Multiplier','Current Value']):
            label = QLabel(h)
            label.setMaximumHeight(100)
            self.table.addWidget(label,0,c)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True) # CRITICAL
        inner = QFrame(scroll)
        inner.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))
        inner.setLayout(self.table)
        scroll.setWidget(inner) # CRITICAL
        gLayout = QVBoxLayout()
        gLayout.addWidget(scroll)
        self.setLayout(gLayout)
        self.row = 0
        self.knobs = {}

    def addRow(self, knob):
        row = self.row + 1
        self.knobs[row] = knob
        widgets = knob.widgets
        for c, w in enumerate(widgets):
            self.table.addWidget(w, self.row, c)
        knob.deleteKnob.connect(lambda: self.deleteRow(row))
        self.row += 1

    def deleteRow(self, row):
        knob = self.knobs[row]
        for w in knob.widgets:
            self.table.removeWidget(w)
            w.deleteLater()
            del w
        knob.deleteLater()
        del knob
        del self.knobs[row]

class combinedKnob_GroupBox(QGroupBox):

    knobChanged = pyqtSignal('float')

    """combinedKnob group box."""
    def __init__(self, parent = None):
        super(combinedKnob_GroupBox, self).__init__(parent)
        self.setTitle('Combined Knob')
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.display = QDoubleSpinBox()
        self.display.setMinimum(-100)
        self.display.setMaximum(100)
        self.display.setValue(0)
        self.display.setSingleStep(0.1)
        f = self.display.font()
        f.setPointSize(27) # sets the size to 27
        self.display.setFont(f)
        self.display.valueChanged.connect(self.emitSignal)

        self.layout.addWidget(self.display)

    def emitSignal(self):
        self.knobChanged.emit(self.display.value())

    def setZero(self):
        self.blockSignals(True)
        self.display.setValue(0)
        self.blockSignals(False)

class relative_knob(QWidget):
    """multiknob knob."""

    deleteKnob = pyqtSignal()

    def __init__(self, start_index=0):
        super(relative_knob, self).__init__()
        self.enabledWidget = QCheckBox()
        self.enabledWidget.setChecked(True)

        self.statusButton = QPushButton()
        # self.statusButton.setReadOnly(True)

        self.nameWidget = QComboBox()
        self.nameWidget.addItems(pv_names)
        self.nameWidget.setCurrentIndex(start_index)
        self.changePV(start_index)
        self.nameWidget.currentIndexChanged.connect(self.changePV)

        self.spinWidget = QDoubleSpinBox()
        self.spinWidget.setMinimum(-100)
        self.spinWidget.setMaximum(100)
        self.spinWidget.setValue(0)
        self.spinWidget.setSingleStep(0.1)

        self.valueWidget = QLineEdit()
        self.valueWidget.setReadOnly(True)

        self.deleteButton = QPushButton('Del')
        self.deleteButton.clicked.connect(self.deleteRow)

    def deleteRow(self):
        self.pv.stop()
        del self.pv
        self.nameWidget.currentIndexChanged.disconnect()
        self.deleteButton.clicked.disconnect()
        self.deleteKnob.emit()

    def changePV(self, index):
        pvname = str(self.nameWidget.itemText(index))
        self.pv = fakePV(pvname)
        self.initialValue = self.pv.value
        self.pv.emitSignal.connect(self.pvEmitted)

    def pvEmitted(self, type, value):
        if type == 'value':
             self.valueWidget.setText(str(value))
        elif type == 'status':
            self.setStatus(value)

    def setStatus(self, status):
        if status is True or status == 'ON':
            col = QColor(Qt.green)
        else:
            col = QColor(Qt.red)
        qss = "background-color:"+col.name()
        self.statusButton.setStyleSheet(qss)

    def setInitialValue(self):
        self.initialValue = self.pv.value

    @property
    def widgets(self):
        return [self.enabledWidget, self.statusButton, self.nameWidget, self.spinWidget, self.valueWidget, self.deleteButton]

    def knobChanged(self, multiplier):
        if self.enabledWidget.isChecked():
            self.pv.setValue(self.initialValue + multiplier * self.spinWidget.value())

class multiknob(QMainWindow):
    def __init__(self, parent = None):
        super(multiknob, self).__init__(parent)

        stdicon = self.style().standardIcon
        style = QStyle
        self.setWindowTitle("Multi-Knob Control")

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        addKnobAction = QAction('Add Knob', self)
        addKnobAction.setStatusTip('Add new Knob')
        addKnobAction.triggered.connect(self.addKnob)
        fileMenu.addAction(addKnobAction)

        reloadSettingsAction = QAction('Reload Settings', self)
        reloadSettingsAction.setStatusTip('Reload Settings YAML File')
        # reloadSettingsAction.triggered.connect(self.signaltable.reloadSettings)
        fileMenu.addAction(reloadSettingsAction)

        saveAllDataAction = QAction('Save Data', self)
        saveAllDataAction.setStatusTip('Save All Data')
        # saveAllDataAction.triggered.connect(self.generalplot.saveAllData)
        fileMenu.addAction(saveAllDataAction)

        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)
        fileMenu.addAction(exitAction)

        self.multiKnobGroup = multiKnob_GroupBox()
        self.combinedKnobGroup = combinedKnob_GroupBox()

        self.layout = QGridLayout()
        self.widget = QWidget()
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        self.layout.addWidget(self.multiKnobGroup,0,0)
        self.layout.addWidget(self.combinedKnobGroup,0,1)
        self.pushButton = QPushButton('Set Base Values')
        self.pushButton.clicked.connect(self.combinedKnobGroup.setZero)
        self.layout.addWidget(self.pushButton,1,0,2,1)

        for i in range(4):
            self.addKnob(i)

    def addKnob(self, i=0):
        knob = relative_knob(i)
        self.combinedKnobGroup.knobChanged.connect(knob.knobChanged)
        self.pushButton.clicked.connect(knob.setInitialValue)
        self.multiKnobGroup.addRow(knob)

def main():
   app = QApplication(sys.argv)
   ex = multiknob()
   ex.show()
   # ex.testSleep()
   sys.exit(app.exec_())

if __name__ == '__main__':
   main()
