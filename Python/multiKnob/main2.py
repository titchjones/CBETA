import sys, os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import numpy as np
from collections import OrderedDict
import yaml
sys.path.append(os.path.dirname( os.path.abspath(__file__)) + "/../")
from generic.pv import *
import argparse


_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG

def dict_representer(dumper, data):
    return dumper.represent_dict(data.items())

def dict_constructor(loader, node):
    return OrderedDict(loader.construct_pairs(node))

yaml.add_representer(OrderedDict, dict_representer)
yaml.add_constructor(_mapping_tag, dict_constructor)

with open(os.path.dirname( os.path.abspath(__file__))+'/pv_names.yaml', 'r') as infile:
    pv_names = yaml.load(infile)

with open(os.path.dirname( os.path.abspath(__file__))+'/knobs.yaml', 'r') as infile:
    knobs = yaml.load(infile)

class multiKnob_GroupBox(QGroupBox):
    """Multiknob group box."""
    def __init__(self, parent = None):
        super(multiKnob_GroupBox, self).__init__(parent)
        self.setTitle('Multi-Knobs')
        self.table = QGridLayout()
        self.table.setRowStretch(0,0)
        for c,h in enumerate(['On', 'PV Name','Multiplier','Current Value']):
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
        self.row = 1
        self.knobs = {}

    def addRow(self, knob):
        row = self.row + 1
        self.knobs[row] = knob
        widgets = knob.widgets
        for c, w in enumerate(widgets):
            self.table.addWidget(w, row, c)
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
        self.multiplier = 0

        self.displayLabel = QLabel('Step Size')
        f = QFont( "Arial", 20, QFont.Bold)
        self.displayLabel.setFont(f)
        self.displayLabel.setAlignment(Qt.AlignCenter);
        self.displayLabel.setMaximumHeight(20)

        self.multiplierDisplay = QLineEdit()
        self.multiplierDisplay.setReadOnly(True)
        f = self.multiplierDisplay.font()
        f.setPointSize(27) # sets the size to 27
        self.multiplierDisplay.setFont(f)

        self.display = QDoubleSpinBox()
        self.display.setDecimals(3)
        self.display.setMinimum(0)
        self.display.setMaximum(0.1)
        self.display.setValue(0.001)
        self.display.setSingleStep(0.001)
        f = self.display.font()
        f.setPointSize(27) # sets the size to 27
        self.display.setFont(f)

        self.leftrightLayout = QHBoxLayout()
        self.leftButton = QPushButton()
        self.leftButton.clicked.connect(self.multiplierDown)
        self.leftButton.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_ArrowLeft')))
        self.rightButton = QPushButton()
        self.rightButton.clicked.connect(self.multiplierUp)
        self.rightButton.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_ArrowRight')))
        self.leftrightLayout.addWidget(self.leftButton)
        self.leftrightLayout.addWidget(self.rightButton)

        self.layout.addWidget(self.multiplierDisplay)
        self.layout.addWidget(self.displayLabel)
        self.layout.addWidget(self.display)
        self.layout.addLayout(self.leftrightLayout)

    def multiplierUp(self):
        self.multiplier += self.display.value()
        self.emitSignal()

    def multiplierDown(self):
        self.multiplier -= self.display.value()
        self.emitSignal()

    def emitSignal(self):
        self.multiplierDisplay.setText("{0:.3f}".format(1+self.multiplier))
        self.knobChanged.emit(self.multiplier)

    def reset(self):
        self.multiplier = 0
        self.emitSignal()

    def setZero(self):
        #self.blockSignals(True)
        self.multiplier = 0
        #self.blockSignals(False)

class relative_knob(QWidget):
    """multiknob knob."""

    deleteKnob = pyqtSignal()

    def __init__(self, actuator=None, strength=0, on=True):
        super(relative_knob, self).__init__()
        self.enabledWidget = QCheckBox()
        self.enabledWidget.setChecked(on)

        self.statusButton = QPushButton()
        #self.statusButton.setReadOnly(True)

        self.nameWidget = QComboBox()
        self.nameWidget.setMinimumWidth(200)
        self.nameWidget.addItems(pv_names)
        if actuator is not None:
            start_index = pv_names.index(actuator)
        else:
            start_index = 0
        self.nameWidget.setCurrentIndex(start_index)

        self.spinWidget = QDoubleSpinBox()
        self.spinWidget.setMinimum(-10)
        self.spinWidget.setMaximum(10)
        self.spinWidget.setValue(1)
        self.spinWidget.setSingleStep(0.1)
        self.spinWidget.setValue(float(strength))
        self.spinWidget.setMaximumWidth(250)

        self.valueWidget = QLineEdit()
        self.valueWidget.setReadOnly(True)
        self.spinWidget.setMaximumWidth(200)

        self.deleteButton = QPushButton()
        self.deleteButton.setIcon(self.style().standardIcon(getattr(QStyle, 'SP_BrowserStop')))
        self.deleteButton.clicked.connect(self.deleteRow)

        self.changePV(start_index)
        self.nameWidget.currentIndexChanged.connect(self.changePV)

    def deleteRow(self):
        del self.pv
        self.nameWidget.currentIndexChanged.disconnect()
        self.deleteButton.clicked.disconnect()
        self.deleteKnob.emit()

    def changePV(self, index):
        pvname = str(self.nameWidget.itemText(index))
        self.pv = PVObject(pvname)
        self.pv.writeAccess = True
        self.initialValue = self.pv.value
        self.valueWidget.setText("{0:.3f}".format(self.initialValue))
        self.pv.newValue.connect(self.pvEmitted)

    def pvEmitted(self, time, value):
        self.valueWidget.setText("{0:.4f}".format(value))

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
        return [self.enabledWidget, self.nameWidget, self.spinWidget, self.valueWidget, self.deleteButton]

    def knobChanged(self, multiplier):
        if self.enabledWidget.isChecked():
            self.pv.setValue(self.initialValue * (1 + multiplier * self.spinWidget.value()))

    def getSettings(self):
        return {'on': self.enabledWidget.isChecked(), 'actuator': self.nameWidget.currentText(), 'value': self.spinWidget.value()}

class multiknob(QMainWindow):
    def __init__(self, inputfile=None, parent = None):
        super(multiknob, self).__init__(parent)

        stdicon = self.style().standardIcon
        style = QStyle
        self.setWindowTitle("Multi-Knob Control")

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        addTabAction = QAction('Add Tab', self)
        addTabAction.setShortcut('Ctrl+T')
        addTabAction.setStatusTip('Add new Tab')
        addTabAction.triggered.connect(self.addTab)
        fileMenu.addAction(addTabAction)

        addKnobAction = QAction('Add Knob', self)
        addKnobAction.setShortcut('Ctrl+K')
        addKnobAction.setStatusTip('Add new Knob')
        addKnobAction.triggered.connect(self.addKnob)
        fileMenu.addAction(addKnobAction)

        reloadSettingsAction = QAction('Reload Settings', self)
        reloadSettingsAction.setStatusTip('Reload Settings YAML File')
        reloadSettingsAction.triggered.connect(self.reloadSettings)
        fileMenu.addAction(reloadSettingsAction)

        loadKnobsAction = QAction('Load Data', self)
        loadKnobsAction.setShortcut('Ctrl+L')
        loadKnobsAction.setStatusTip('Load Data File')
        loadKnobsAction.triggered.connect(self.loadSettings)
        fileMenu.addAction(loadKnobsAction)

        saveAllDataAction = QAction('Save Data', self)
        saveAllDataAction.setShortcut('Ctrl+S')
        saveAllDataAction.setStatusTip('Save All Data')
        saveAllDataAction.triggered.connect(self.saveSettings)
        fileMenu.addAction(saveAllDataAction)

        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)
        fileMenu.addAction(exitAction)

        self.tabNo = 0

        self.widget = QTabWidget()
        self.tabBar = clickableTabBar()
        self.tabBar.tabCloseRequested.connect(self.closeTab)
        self.widget.setTabBar(self.tabBar)
        self.setCentralWidget(self.widget)

        if inputfile is not None:
            self.knobsFilename = inputfile
            self.loadSettings(self.knobsFilename)
        else:
            self.knobsFilename = ''

    def closeTab(self, tab):
        self.widget.widget(tab).deleteLater()
        self.widget.removeTab(tab)

    def addTab(self):
        self.tabNo += 1
        self.widget.addTab(knobTab('', parent=self), 'Tab '+str(self.tabNo))

    def addKnob(self):
        self.widget.currentWidget().addKnob()

    def getSettings(self):
        ntabs = self.widget.count()
        settings = OrderedDict([])
        for i in range(ntabs):
            settings[self.widget.tabText(i)] = self.widget.widget(i).getSettings()
        return settings

    def saveSettings(self):
        filename, ok = QFileDialog.getSaveFileName(self, 'Save File')
        if ok:
            settings = self.getSettings()
            with open(str(filename), 'w') as outfile:
                yaml.dump(settings, outfile, default_flow_style=False, explicit_start=False)

    def loadSettings(self, filename=None):
        if filename is None or filename is False:
            self.knobsFilename, ok = QFileDialog.getOpenFileName(self, 'Open File')
        else:
            ok = True
            self.knobsFilename = filename
        if ok and os.path.isfile(self.knobsFilename):
            with open(self.knobsFilename, 'r') as infile:
                knobs = yaml.load(infile)
            self.widget.clear()
            for k,v in knobs.items():
                if not k.lower() == 'general':
                    self.widget.addTab(knobTab(k, **v, parent=self), k)

    def reloadSettings(self):
        global pv_names
        with open(os.path.dirname( os.path.abspath(__file__))+'/pv_names.yaml', 'r') as infile:
            pv_names = yaml.load(infile)
        self.loadSettings(self.knobsFilename)

class clickableTabBar(QTabBar):
    def __init__(self, parent = None, **kwargs):
        super(QTabBar, self).__init__(parent, **kwargs)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            newLabel, ok = QInputDialog.getText(self, "Edit Knob Label", "Label:", QLineEdit.Normal, self.tabText(self.currentIndex()))
            if ok:
                self.setTabText(self.currentIndex(), newLabel)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MidButton:
            self.tabCloseRequested.emit(self.tabAt(event.pos()))
        super(QTabBar, self).mouseReleaseEvent(event)

class knobTab(QWidget):

    def __init__(self, label, parent = None, **kwargs):
        super(knobTab, self).__init__(parent)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Horizontal)
        self.multiKnobGroup = multiKnob_GroupBox()
        self.combinedKnobGroup = combinedKnob_GroupBox()
        self.combinedKnobGroup.setMaximumWidth(250)
        self.splitter.addWidget(self.multiKnobGroup)
        self.splitter.addWidget(self.combinedKnobGroup)
        self.layout.addWidget(self.splitter,0,0,4,4)
        self.pushButton = QPushButton('Set Base Values')
        self.pushButton.clicked.connect(self.combinedKnobGroup.setZero)
        self.layout.addWidget(self.pushButton,4,0,1,1)
        self.resetButton = QPushButton('Reset')
        self.resetButton.clicked.connect(self.combinedKnobGroup.reset)
        self.layout.addWidget(self.resetButton,4,1,1,1)
        self.knobs = []

        if 'actuators' in kwargs:
            if 'strengths' not in kwargs:
                kwargs['strengths'] = [1] * len(kwargs['actuators'])
            if 'status' not in kwargs:
                kwargs['status'] = [True] * len(kwargs['actuators'])
            for a, s, on in zip(kwargs['actuators'], kwargs['strengths'], kwargs['status']):
                self.addExistingKnob(a, s, on)

    def addKnob(self):
        knob = relative_knob()
        self.knobs.append(knob)
        self.combinedKnobGroup.knobChanged.connect(knob.knobChanged)
        self.pushButton.clicked.connect(knob.setInitialValue)
        self.multiKnobGroup.addRow(knob)

    def addExistingKnob(self, a, s, on):
        knob = relative_knob(a, s, on)
        self.knobs.append(knob)
        self.combinedKnobGroup.knobChanged.connect(knob.knobChanged)
        self.pushButton.clicked.connect(knob.setInitialValue)
        self.multiKnobGroup.addRow(knob)

    def getSettings(self):
        settings = []
        for knob in self.knobs:
            settings.append(knob.getSettings())
        settings2 = []
        for s in settings:
            settings2.append([s['actuator'], s['value'], s['on']])
        actuators, strengths, status = list(zip(*settings2))
        finalsettings = {'actuators': list(actuators), 'strengths': list(strengths), 'status': list(status)}
        return finalsettings


def main():
    app = QApplication(sys.argv)

    parser = argparse.ArgumentParser(description='Multiknob Control')
    parser.add_argument('-f', '--file', dest='inputfile')
    args = parser.parse_args()
    ex = multiknob(args.inputfile)
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
   main()
