from PyQt5.QtCore import QPoint, Qt, QTime, QTimer, QRectF
from PyQt5.QtGui import QColor, QPainter, QPolygon, QPen
from PyQt5.QtWidgets import QApplication, QWidget
import random

class positionWidget(QWidget):

    color = QColor(139, 177, 239)
    ref_color = QColor(63, 82, 114)

    def __init__(self, parent=None):
        super(positionWidget, self).__init__(parent)
        self.resize(200, 200)
        self.pointWidth = 5
        self.value = [0, 0]
        self.refValue = [0,0]
        self.scale = 10

    def setValue(self, value):
        self.value = value

    def setReferenceValue(self, value):
        self.refValue = value

    def setScale(self, scale):
        self.scale = scale

    def paintEvent(self, event=None):
        side = min(self.width(), self.height())
        pos = self.value
        ref_pos = self.refValue

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(side / 230.0, side / 230.0)

        painter.setBrush(Qt.NoBrush)
        painter.setPen(QColor(0, 0, 0))

        painter.drawRect(-100,-100, 2*100, 2*100)

        painter.drawLine(-100,0,100,0)
        painter.drawLine(-100,50,100,50)
        painter.drawLine(-100,-50,100,-50)
        painter.drawLine(-50,-100,-50, 100)
        painter.drawLine(50, 100,50, -100)
        painter.drawLine(0,-100, 0, 100)

        painter.setBrush(self.ref_color)
        painter.setPen(self.ref_color)
        painter.drawEllipse((ref_pos[0] * (100/self.scale)) - self.pointWidth, (ref_pos[1] * -(100/self.scale)) - self.pointWidth,
        2*self.pointWidth, 2*self.pointWidth)

        painter.setBrush(self.color)
        painter.drawEllipse((pos[0] * (100/self.scale)) - self.pointWidth, (pos[1] * -(100/self.scale)) - self.pointWidth,
        2*self.pointWidth, 2*self.pointWidth)

        painter.save()
        painter.setPen(QColor(0,0,0))
        painter.rotate(90)
        for i in range(2):
            painter.drawLine((pos[0] * (100/self.scale)) - self.pointWidth/2, (pos[1] * -(100/self.scale)) - self.pointWidth/2,
            (pos[0] * (100/self.scale)) + self.pointWidth/2, (pos[1] * -(100/self.scale)) + self.pointWidth/2)
            painter.rotate(90)
        painter.restore()

        painter.setPen(QColor(0,0,0))
        font = painter.font()
        font.setPointSize(font.pointSize() * 1.2)
        painter.setFont(font)
        painter.drawText(QRectF(-110, 100, 30, 20), str(-1*self.scale))
        painter.drawText(QRectF(92, 100, 30, 20), str(1*self.scale))

def spin(*args, **kwargs):
    spinValue = [20*random.random() - 10, 20*random.random() - 10]
    pw.setValue(0, list(spinValue))
    pw.update()

if __name__ == '__main__':
    import sys
    global pw
    app = QApplication(sys.argv)
    pw = positionWidget()
    pw.setValue(0, [0, 5])
    pw.show()
    timer = QTimer()
    timer.timeout.connect(spin)
    timer.start(10)
    sys.exit(app.exec_())
