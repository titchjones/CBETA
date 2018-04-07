import time
import numpy as np
from PyQt5.QtCore import *
from  PyQt5.QtGui import *
from  PyQt5.QtWidgets import *
import scipy.constants as constants
from scipy.optimize import curve_fit

degree = constants.pi/180.0
q_e = constants.elementary_charge
c = constants.speed_of_light

p0 = 5e6

class RF_Cavity(object):

    def __init__(self, name, crest):
        super(RF_Cavity, self).__init__()
        self.name = name
        self._crest = 0
        self._phase = 0
        self._amplitude = 0

    @property
    def phase(self):
        return self._phase
    @phase.setter
    def phase(self, value):
        self._phase = value

    @property
    def crest(self):
        return self._crest
    @crest.setter
    def crest(self, value):
        self._crest = value

    @property
    def amplitude(self):
        return self._amplitude
    @amplitude.setter
    def amplitude(self, value):
        self._amplitude = value

    @property
    def p(self):
        return p0 + self.amplitude * np.cos((self.crest - self.phase) * degree)

class dipole(object):

    def __init__(self, name, length):
        super(dipole, self).__init__()
        self.name = name
        self.length = length
        self.field = 0

    @property
    def B(self):
        return self.field
    @B.setter
    def B(self, value):
        self.field = value

    @property
    def p(self):
        return self._p
    @p.setter
    def p(self, value):
        self._p = value

    @property
    def Brho(self):
        return self.p / c

    @property
    def angle(self):
        return self.field * self.length / self.Brho

class bpm(object):

    def __init__(self, name, length, angle=(45*degree)):
        super(bpm, self).__init__()
        self.name = name
        self.length = length
        self.angle = angle
        self._dipole_angle = 0

    @property
    def dipole_angle(self):
        return self._dipole_angle
    @dipole_angle.setter
    def dipole_angle(self, value):
        self._dipole_angle = value

    @property
    def x(self):
        return np.mean([self.length*(self.angle - self.dipole_angle) + 0.0001*np.random.randn() for i in range(5)])

class accelerator(QObject):

    newBPMReading = pyqtSignal(list)
    newGradient = pyqtSignal(int, float)

    def __init__(self):
        super(accelerator, self).__init__()
        self.cav = RF_Cavity('cav1', 0)
        self.dip = dipole('dip1', 0.2)
        self.bpm = bpm('bpm1', 0.2)
        self.bpmReadings = np.empty((0,2),int)
        self.offset = 0

    @property
    def crest(self):
        return self.cav.crest
    @crest.setter
    def crest(self, value):
        self.cav.crest = value

    @property
    def phase(self):
        return self.cav.phase
    @phase.setter
    def phase(self, value):
        self.cav.phase = value

    @property
    def amplitude(self):
        return self.cav.amplitude
    @amplitude.setter
    def amplitude(self, value):
        self.cav.amplitude = value

    @property
    def p(self):
        return self.cav.p

    @property
    def B(self):
        return self.dip.B
    @B.setter
    def B(self, value):
        self.dip.B = value

    @property
    def x(self):
        self.dip.p = self.cav.p
        self.bpm.dipole_angle = self.dip.angle
        return 1e3*self.bpm.x

    def bpmReading(self):
        self.bpmReadings = np.append(self.bpmReadings, [[self.phase, self.x + self.offset]], axis=0)

    def findStartingPhase(self, phase=0):
        self.phase = phase
        self.B = 0.3
        bpmpos = self.x
        while((self.x > 10 or self.x < -10) and self.phase < 355):
            self.phase += 5

    def gradient(self):
        return np.polyfit(x=self.bpmReadings[-5:,0], y=self.bpmReadings[-5:,1], deg=1)[0]

    def initialPoints(self):
        for i in range(5):
            self.phase += 1
            self.bpmReading()

    def center_beam(self):
        startx = self.x
        if self.x > 0:
            while(self.x > 0):
                self.B += 0.05
        else:
            while(self.x < 0):
                self.B -= 0.05
        self.offset += startx - self.x
        self.bpmReading()

    def guess_crest(self):
        return self.bpmReadings[:,0][list(self.bpmReadings[:,1]).index(np.max(self.bpmReadings[:,1]))]

    def reset(self):
        self.phasesign = 1
        self.offset = 0
        self.bpmReadings = np.empty((0,2),int)

    def findCrest(self, phase=0):
        self.offset = 0
        self.findStartingPhase(phase)
        self.initialPoints()
        if self.gradient() < 0:
            self.phasesign = -1*self.phasesign

    def optimise(self):
        while((self.phasesign * self.gradient()) > -1):
            self.step()

    def calculate_crest(self):
        fit = self.fit_curve()
        self.calculated_crest = fit[2]
        return fit

    def step(self):
        if((self.phasesign * self.gradient()) > -1):
            self.phase += self.phasesign * np.max([2, 5*np.abs(self.gradient())])
            self.center_beam()
            self.newBPMReading.emit([self.phase, self.x + self.offset])
        self.newGradient.emit(self.phasesign, self.gradient())
        # self.set_on_phase(self.calculated_crest)

    def set_on_phase(self, crest):
        while(np.abs(crest - self.phase) > 1):
            phasesign = np.sign(crest - self.phase)
            self.phase += phasesign*np.max([10, 5*np.abs(crest - self.phase)])
            self.center_beam()

    def fitting_equation(self, x, a, b, crest):
        return a + b * np.cos((crest - x) * degree)

    def fit_curve(self):
        popt, pcov = curve_fit(self.fitting_equation, self.bpmReadings[:,0], self.bpmReadings[:,1], p0=[1,4,self.guess_crest()], bounds=([-np.inf, -np.inf, self.guess_crest()-20],[np.inf,np.inf,self.guess_crest()+20]))
        return popt

    def fittedData(self):
        minx = np.min(self.bpmReadings[:,0])
        maxx = np.max(self.bpmReadings[:,0])
        fitting_params = self.fit_curve()
        fittedData = [[x, self.fitting_equation(x, *fitting_params)] for x in np.arange(minx, maxx, 0.1)]
        return fittedData

def main():
   acc = accelerator()
   for i in range(20):
       acc.crest = 360.0*np.random.random()
       acc.amplitude = 20e6
       acc.B = 0.327
       # acc.findStartingPhase()
       acc.reset()
       acc.findCrest(0)
       acc.optimise()
       acc.calculate_crest()
       acc.set_on_phase(acc.calculated_crest)
       print i, acc.crest - np.mod(acc.phase,360)

if __name__ == '__main__':
   main()
