import os, sys
import subprocess
import pexpect
import time
import math
import atexit
import multiprocessing
from PyQt5.QtCore import *
from  PyQt5.QtGui import *
from  PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np

from matplotlib import pyplot as plt

class mainWindow(QMainWindow):
  def __init__(self, parent = None):
        super(mainWindow, self).__init__(parent)
        self.tao = tao()
        self.setCentralWidget(self.tao)

class tao(QWidget):
    def __init__(self, parent = None):
        super(tao, self).__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.resultWindow = QPlainTextEdit()
        self.resultWindow.setReadOnly(True)
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidget(self.resultWindow)
        self.scrollArea.setWidgetResizable(True)

        self.inputWindow = QLineEdit()
        self.inputWindow.editingFinished.connect(self.send_command)
        self.label = QLabel(self)
        self.label.setText("tao> ")
        self.inputWidget = QWidget()
        self.inputWidgetLayout = QHBoxLayout()
        self.inputWidget.setLayout(self.inputWidgetLayout)
        self.inputWidgetLayout.addWidget(self.label)
        self.inputWidgetLayout.addWidget(self.inputWindow)

        self.layout.addWidget(self.scrollArea)
        self.layout.addWidget(self.inputWidget)

        self.start_tao()

    def parse_plot_data_str(self, data_str):

      s = []
      x = []

      if(isinstance(data_str,str)):
        lines = data_str.split(",")
      else:
        lines = data_str

      for line in lines:
        tokens = line.split(";")

        if(len(tokens)==3):
          s.append(tokens[1])
          x.append(tokens[2])

      return(s,x)


    def start_tao(self):

        self.tao = pexpect.spawn("tao -noplot -lat fat.bmad")   # Tao must be in your path, also you should add your lattice file to this too
        self.tao.expect('Tao>')                             # Trap initial prompt, REPLACE THIS WITH "Tao>"

        # Do default setting up here, if not in tao.init
        self.send_command('set global plot_calc_always = T')

    def send_command(self, cmd_str=None):
        if cmd_str is None:
            cmd_str = self.inputWindow.text()
            self.inputWindow.clear()

        self.tao.sendline(cmd_str)
        #tao.expect('CBETA-V>')
        self.tao.expect('Tao>')

        # Gets data from tao and splits on new lines
        lines = self.tao.before.decode(encoding='UTF-8').split("\r\n")

        final_lines = []
        for line in lines:
            if(line.strip() != ''):
                self.resultWindow.appendPlainText(line.strip())

def main():
    ''' this is REQUIRED for Qt applications '''
    app = QApplication(sys.argv)
    ''' run the mainWindow main window'''
    ex = mainWindow()
    ''' show the application - REQUIRED to see anything... '''
    ex.show()
    ''' This is REQUIRED to stop the application from quitting straight away '''
    sys.exit(app.exec_())

if __name__ == '__main__':
   main()
