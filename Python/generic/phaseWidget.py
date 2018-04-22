from PyQt5.QtCore import QPoint, Qt, QTime, QTimer, QRectF
from PyQt5.QtGui import QColor, QPainter, QPolygon
from PyQt5.QtWidgets import QApplication, QWidget


class phaseWidget(QWidget):
    hand = QPolygon([
        QPoint(4, 0),
        QPoint(-4, 0),
        QPoint(-1, -80),
        QPoint(1, -80)
    ])

    color = QColor(0, 0, 0)

    def __init__(self, parent=None):
        super(phaseWidget, self).__init__(parent)
        self.resize(200, 200)
        self.value = 0

    def setValue(self, value):
        self.value = value

    def paintEvent(self, event):
        side = 0.8 * min(self.width(), self.height())

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2 / 0.95)
        painter.scale(side / 200.0 * 0.9, side / 200.0 * 0.9)

        painter.setPen(Qt.NoPen)
        painter.setBrush(self.color)

        painter.save()
        painter.rotate(180 + self.value)
        painter.drawConvexPolygon(self.hand)
        painter.restore()
        painter.save()
        painter.setPen(self.color)

        for i in range(12):
            painter.drawLine(88, 0, 96, 0)
            painter.rotate(30.0)

        painter.restore()

        painter.setPen(self.color)
        font = painter.font()
        font.setPointSize(font.pointSize() * 1.2)
        painter.setFont(font)
        painter.drawText(QRectF(-5, 100, 30, 20), '0°')
        painter.drawText(QRectF(-12.5, -130, 35, 20), '180°')
        painter.drawText(QRectF(-125, -10, 30, 20), '90°')
        painter.drawText(QRectF(105, -10, 35, 20), '270°')


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    pw = phaseWidget()
    pw.setValue(0, 168)
    pw.show()
    sys.exit(app.exec_())
