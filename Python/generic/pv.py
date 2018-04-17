import time, copy
from epics import caget, caput, cainfo, PV
import numpy as np
from PyQt5.QtCore import *
from  PyQt5.QtGui import *
from  PyQt5.QtWidgets import *
from collections import deque, OrderedDict

def tablePrint(**kwargs):
    print "{:<8} {:<15}".format('Key','Value')
    for k, v in kwargs.items():
        print "{:<8} {:<15}".format(k, v)

class PVObject(QObject):
    def __init__(self, pv, parent=None):
        super(PVObject, self).__init__(parent = parent)
        self.name = pv
        self.pv = PV(self.name, callback=self.callback)
        self.dict = OrderedDict()

    def callback(self, **kwargs):
        self.dict = OrderedDict(kwargs)
        if 'status' in kwargs and 'value' in kwargs and status:
            if not 'timestamp' in kwargs:
                timestamp = time.time()
            self._value = [self.dict['timestamp'], self.dict['value']]

    @property
    def value(self):
        return self._value[1]
    @value.setter
    def value(self, val):
        self.put(val)

    @property
    def time(self):
        return self._value[0]

    def get(self):
        return self._value

    def put(self, value):
        self.pv.put(value)

    def __str__(self):
        tablePrint(self.dict)

class PVBuffer(PVObject):
    def __init__(self, pv, maxlen=1024, parent=None):
        super(PVBuffer, self).__init__(pv=pv, parent = parent)
        self.maxlen = maxlen
        self.buffer = deque(maxlen=self.maxlen)
        self.reset()

    def callback(self, **kwargs):
        super(PVBuffer).callback(**kwargs)
        self.buffer.append(self._value)
        self.length += 1
        self.sum_x1 += val
        self.sum_x2 += val**2
        if self._value[1] < self.minValue:
            self.minValue = float(self._value[1])
        if self._value[1] > self.max:
            self.maxValue = float(self.maxValue[1])

    def lastValue(self):
        return self._value

    def get(self):
        return self.buffer

    @property
    def mean(self):
        return self.sum_x1/length if length > 0 else 0

    @property
    def std(self):
        return math.sqrt((self.sum_x2 / length) - (self.mean*self.mean)) if (self.sum_x2 / length) - (self.mean*self.mean) > 0 else 0

    @property
    def min(self):
        return self.minValue

    @property
    def max(self):
        return self.maxValue

    def reset(self):
        self.length = 0
        self.minValue = sys.maxsize
        self.minValue = -1*sys.maxsize
        self.sum_x1 = 0
        self.sum_x2 = 0

    @property
    def bufferLength(self):
        return self.maxlen
    @bufferLength.setter
    def bufferLength(self, value):
        self.maxlen = value
        _buffer = copy.deepcopy(self.buffer)
        self.buffer = deque(maxlen=self.maxlen)
        for i in _buffer:
            self.buffer.append(i)
