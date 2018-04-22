from pv import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from positionWidget import *
from intensityWidget import *
from phaseWidget import *

class bpmWidget(QWidget):
    def __init__(self, parent=None):
        super(bpmWidget, self).__init__(parent)
        self._x = 0
        self._y = 0
        self._I = 0
        self._I_ref = 1
        self._ph = 0
        self.resize(250,600)
        self.positionWidget = positionWidget()
        self.phaseWidget = phaseWidget()
        self.intensityWidget = intensityWidget()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.positionWidget,2)
        self.layout.addWidget(self.phaseWidget,2)
        self.layout.addWidget(self.intensityWidget,1)

    @property
    def x(self):
        return self._x
    @x.setter
    def x(self, value):
        self._x = value
        self.updatePosition()
    @property
    def y(self):
        return self._y
    @y.setter
    def y(self, value):
        self._y = value
        self.updatePosition()

    def updatePosition(self):
        self.positionWidget.setValue([self.x, self.y])

    def setPositionScale(self, scale):
        self.positionWidget.setScale(scale)

    @property
    def I(self):
        return self._I
    @I.setter
    def I(self, value):
        self._I = value
        self.updateIntensity()

    def updateIntensity(self):
        self.intensityWidget.setValue(self.I)

    @property
    def I_ref(self):
        return self._I_ref
    @I_ref.setter
    def I_ref(self, value):
        self._I_ref = value
        self.updateReferenceIntensity()

    def updateReferenceIntensity(self):
        self.intensityWidget.setReferenceValue(self.I_ref)

    @property
    def phase(self):
        return self._ph
    @phase.setter
    def phase(self, value):
        self._ph = value
        self.updatePhase()

    def updatePhase(self):
        self.phaseWidget.setValue(self.phase)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = QMainWindow()
    mw.resize(1.25*250,1.25*600)
    bpm = bpmWidget()
    bpm.setPositionScale(20)
    bpm.x = 3
    bpm.y = 7
    bpm.I = 0.43
    bpm.phase = 165
    mw.setCentralWidget(bpm)
    mw.show()
    sys.exit(app.exec_())
