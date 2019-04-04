import sys, os
from base_tool_qt import BaseFrameworkQT
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QSlider, QCheckBox, QSpinBox, QComboBox, QLabel, \
    QGraphicsScene, QGraphicsPixmapItem, QGraphicsView
from PyQt5 import uic
from PyQt5.QtGui import QPixmap, QPainter, QResizeEvent
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QResizeEvent, QColor, QFont, QBrush, QPen
from PyQt5.QtCore import Qt


class ImageViewWidget2(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        uic.loadUi(os.path.join(BaseFrameworkQT.ui_path, "image_view", "image_view_widget.ui"), self)

        self.pic = QPixmap("/home/laptop/work/catkin/src/powerpoof_description/motor_scheme/image.png")
        self.ratio = self.pic.height() / self.pic.width()

    def resizeEvent(self, event):
        width = event.size().width()
        height = width * self.ratio
        pic = self.pic.scaled(width, height, Qt.KeepAspectRatio, Qt.FastTransformation)
        scene = QGraphicsScene()
        scene.setSceneRect(0, 0, pic.width(), pic.height())
        scene.addItem(QGraphicsPixmapItem(pic))
        self.image_gv.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.image_gv.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.image_gv.setScene(scene)
        self.image_gv.setRenderHint(QPainter.Antialiasing)
        self.image_gv.resize(width, height)
        self.setMinimumHeight(height)
        parent = self.parent()
        while parent.parent() is not None:
            parent = parent.parent()
        parent.resize(parent.width(), height + (parent.height() - height))
        parent.setMaximumHeight(height)


class ImageViewWidget3(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        uic.loadUi(os.path.join(BaseFrameworkQT.ui_path, "image_view", "image_view_widget.ui"), self)

        self.pic = QPixmap("/home/laptop/work/catkin/src/powerpoof_description/motor_scheme/image.png")
        self.ratio = self.pic.height() / self.pic.width()
        self.image_gv.mousePressEvent = self._on_image_click
        self.img_pos = ()
        self.img_size = ()

    def resizeEvent(self, event):
        pic = self.pic.scaled(self.image_gv.width(), self.image_gv.height(), Qt.KeepAspectRatio, Qt.FastTransformation)
        x = (self.image_gv.width() - pic.width()) / 2
        y = (self.image_gv.height() - pic.height()) / 2
        scene = QGraphicsScene()
        scene.setSceneRect(-x, -y, pic.width(), pic.height())
        self.img_pos = (x, y)
        self.img_size = (pic.width(), pic.height())
        scene.addItem(QGraphicsPixmapItem(pic))
        self.image_gv.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.image_gv.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.image_gv.setScene(scene)
        self.image_gv.setRenderHint(QPainter.Antialiasing)
        # self.resize(width, height)

    def _on_image_click(self, event):
        x, y = self.img_pos
        w, h = self.img_size
        ex = event.x()
        ey = event.y()
        if (x <= ex <= x + w) and (y <= ey <= y + h):
            type(self).on_image_click(self, event)


class ImageViewWidget(QGraphicsView):
    def __init__(self, image_path=None, parent=None):
        QGraphicsView.__init__(self, parent=parent)
        self.image_path = image_path
        self.pic = None
        self.ratio = None
        self.img_pos = ()
        self.img_size = ()
        self.__rescaled = None
        self.inited = False

    def rescale_image(self):
        pic = self.pic.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.FastTransformation)
        x = (self.width() - pic.width()) / 2
        y = (self.height() - pic.height()) / 2
        scene = QGraphicsScene()
        scene.setSceneRect(0, 0, pic.width(), pic.height())
        self.img_pos = (x, y)
        self.img_size = (pic.width(), pic.height())
        scene.addItem(QGraphicsPixmapItem(pic))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setScene(scene)
        self.setRenderHint(QPainter.Antialiasing)

    def resizeEvent(self, event):
        QGraphicsView.resizeEvent(self, event)
        if self.inited:
            self.rescale_image()


    def showEvent(self, event):
        if not self.inited:
            self._init()
            self.init()

    def init(self):
        pass

    def load_image(self, path):
        self.image_path = path
        self.pic = QPixmap(self.image_path)
        self.ratio = self.pic.height() / self.pic.width()
        self.setMinimumWidth(100)
        self.setMinimumHeight(100 * self.ratio)
        self.img_pos = (0,0)
        self.img_size = (self.pic.width(), self.pic.height())
        self.__rescaled = False
        self.setMouseTracking(True)
        self.rescale_image()
        self.inited=True


    def _init(self):
        if self.image_path:
            self.load_image(self.image_path)

    def mouse_under_image(self, event):
        x, y = self.img_pos
        w, h = self.img_size
        ex = event.x()
        ey = event.y()
        return (x <= ex <= x + w) and (y <= ey <= y + h)

    def mousePressEvent(self, event):
        if self.mouse_under_image(event):
            type(self).on_image_click(self, event)

    def mouseMoveEvent(self, event):
        if self.mouse_under_image(event):
            self.on_image_mouse_move(event)

    def on_image_click(self, event):
        pass

    def on_image_mouse_move(self, event):
        pass

    def drawText(self, event, qp):
        qp.setPen(QColor(168, 34, 3))
        qp.setFont(QFont('Decorative', 10))
        qp.drawText(event.rect(), Qt.AlignCenter, self.text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ImageViewWidget(image_path="/home/laptop/work/powerpoof/powerpoof_qt/data/motor_schemes/scheme1/image.png")
    w.show()
    exit(app.exec_())
