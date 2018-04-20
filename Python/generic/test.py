from pv import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class testPV(QMainWindow):
    def __init__(self, parent = None):
        super(testPV, self).__init__(parent)
        PVs = ['MS1QUA03_cmd', 'MS1QUA04_cmd']

        stdicon = self.style().standardIcon
        style = QStyle
        self.setWindowTitle("Testing PVs Application")

        self.stylesheet = "stylesheet.qss"
        with open(self.stylesheet,"r") as fh:
            self.setStyleSheet(fh.read())

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

        self.groupBox = groupBox()
        self.layout.addWidget(self.groupBox)

        for pv in PVs:
            self.groupBox.addWidget(epicsSliderWidget(PVBuffer(pv)))

class epicsWidget(QWidget):
    def __init__(self, pv=None, parent = None):
        super(epicsWidget, self).__init__(parent=parent)
        self.setMaximumHeight(200)
        self.pv = pv

    def changeValue(self, value):
        print ('new value ', self.pv.name, ' = ', value)

    @property
    def lineEditChildren(self):
        return self.findChildren(epicsTextWidget)

    def pauseUpdating(self):
        for child in self.lineEditChildren:
            self.pv.newValue.disconnect(child.updateValue)

    def startUpdating(self):
        for child in self.lineEditChildren:
            self.pv.newValue.connect(child.updateValue)

    def updateValue(self, value):
        pass

class epicsTextWidget(epicsWidget):
    def __init__(self, pv=None, parent = None):
        super(epicsTextWidget, self).__init__(pv=pv, parent=parent)
        self.pv.newValue.connect(self.updateValue)

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel(self.pv.name)
        self.textBox = QLineEdit()
        self.textBox.setText("{0:.3f}".format(self.pv.lastValue()))
        self.textBox.setReadOnly(True)
        self.textBox.setMinimumWidth(40)
        self.textBox.setMaximumWidth(60)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.textBox)

    def updateValue(self, time, value):
        self.textBox.setText("{0:.3f}".format(value))

class epicsSliderWidget(epicsWidget):
    def __init__(self, pv=None, multiplier=100, parent = None):
        super(epicsSliderWidget, self).__init__(pv=pv, parent=parent)
        self.multiplier = multiplier
        self.setMouseTracking(True)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.textWidget = epicsTextWidget(pv)

        self.slider = QDoubleSlider(self.multiplier, Qt.Horizontal)
        self.slider.setFocusPolicy(Qt.StrongFocus);

        self.slider.setTickPosition(QSlider.TicksBothSides);
        self.slider.setTickInterval(1);
        self.slider.setSingleStep(0.01);
        self.slider.setPageStep(0.1)
        self.slider.setRange(-10,10)
        self.slider.setTracking(False)
        self.slider.valueChanged.connect(self.changeValue)
        self.slider.sliderPressed.connect(self.pauseUpdating)
        self.slider.sliderReleased.connect(self.startUpdating)

        self.groupBox = highlightingGroupBox(pv.name, self.slider)
        self.groupBoxLayout = QVBoxLayout()
        self.groupBox.setLayout(self.groupBoxLayout)

        self.groupBoxLayout.addWidget(self.textWidget)
        self.groupBoxLayout.addWidget(self.slider)

        self.layout.addWidget(self.groupBox)


    def changeValue(self, value):
        value = float(self.slider.value()) / self.multiplier
        print ('new value ', self.pv.name, ' = ', value)

    def updateValue(self, time, value):
        self.slider.setValue(value*multiplier)

class highlightingGroupBox(QGroupBox):
    """group box with highlighting"""
    def __init__(self, label = None, focus = None, parent = None):
        super(highlightingGroupBox, self).__init__(parent)
        self.focusWidget = focus
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        self.focusWidget.setFocus()
        self.setStyleSheet("""
               QGroupBox 
               { 
                   background-color: rgb(255, 255,255); 
                   border:1px solid rgb(50, 50, 50);
                   border-radius: 9px;
                   margin-top: 0.5em;
               }
               """
        )

    def leaveEvent(self, event):
        self.setStyleSheet("")

class groupBox(QGroupBox):
    """group box."""
    def __init__(self, parent = None):
        super(groupBox, self).__init__(parent)
        self.table = QGridLayout()
        self.table.setRowStretch(0,0)
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

    def addWidget(self, widget):
        self.knobs[self.row] = widget
        self.table.addWidget(widget, self.row, 0)
        self.row += 1

class QDoubleSlider(QSlider):

    def __init__(self, multiplier=100, *args, **kwargs):
        super(QSlider, self).__init__(*args, **kwargs)
        self.multiplier = multiplier
      
    def setRange(self, min, max):
        super(QDoubleSlider, self).setRange(self.multiplier*min, self.multiplier*max)

    def setPageStep(self, step):
        super(QDoubleSlider, self).setPageStep(self.multiplier*step)

    def setSingleStep(self, step):
        super(QDoubleSlider, self).setSingleStep(self.multiplier*step)

    def setTickInterval(self, interval):
        super(QDoubleSlider, self).setTickInterval(self.multiplier*interval)

def main():
   app = QApplication(sys.argv)
   ex = testPV()
   ex.show()
   sys.exit(app.exec_())

if __name__ == '__main__':
   main()
