import os
from widgets.scheme_widget import SchemeWidget

from widgets.point_map_widget import PointContent
from base_tool_qt import BaseFrameworkQT
from PyQt5.QtWidgets import QWidget, QGridLayout, QSlider, QHBoxLayout, QGraphicsScene, QGraphicsPixmapItem, \
    QGraphicsView, QMenu, QAction, QFileDialog
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter


class MotorSchemeCreatorWidget(SchemeWidget):
    def __init__(self, parent, *args, **kwargs):
        SchemeWidget.__init__(self, *args, parent=parent, content_type=MotorPointContent, **kwargs)
        self.menu_name = None

    def init_menu(self):
        self.menu_name = "Motor scheme"
        hello_action = QAction("Hello")
        hello_action.triggered.connect(lambda: print("HELLO"))
        self.menu.append(hello_action)

        create_action = QAction("Create")
        create_action.triggered.connect(self.create)
        self.file_menu.append(create_action)

        save_action = QAction("Save")
        save_action.triggered.connect(self.save)
        self.file_menu.append(save_action)

        load_action = QAction("Load")
        load_action.triggered.connect(lambda x: self.load())
        self.file_menu.append(load_action)



if __name__ == "__main__":
    framework = BaseFrameworkQT(custom_widget_type=MotorSchemeCreatorWidget,
                                scheme_path="/home/laptop/work/powerpoof/powerpoof_qt/data/motor_schemes/scheme1",
                                auto_expand=False, manual_add=True, point_radius=15)
    framework.run()
