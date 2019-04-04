from PyQt5.QtWidgets import QSlider
from PyQt5.QtCore import Qt


class ClickSlider(QSlider):
    def __init__(self, *args, **kwargs):
        QSlider.__init__(self, *args, **kwargs)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.orientation() == Qt.Vertical:
                self.setValue(
                    self.minimum() + ((self.maximum() - self.minimum()) * (self.height() - event.y())) / self.height())
            else:
                self.setValue(
                    self.minimum() + (self.maximum() - self.minimum() + 1) * (float(event.x()) / float(self.width())))

            event.accept();
        QSlider.mousePressEvent(self, event)