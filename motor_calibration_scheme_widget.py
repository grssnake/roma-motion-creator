import os
from widgets.scheme_widget import SchemeWidget, MotorPointContent, PointContent

from base_tool_qt import BaseFrameworkQT, change_value_without_signal
from PyQt5.QtWidgets import QWidget, QGridLayout, QSlider, QHBoxLayout, QGraphicsScene, QGraphicsPixmapItem, \
    QGraphicsView, QMenu, QAction, QFileDialog
from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter


class CalibrationContent(PointContent):
    def __init__(self, *args, **kwargs):
        self.base_content = kwargs.get("parent")
        PointContent.__init__(self, parent=self.base_content)
        self.controller = kwargs.get("controller")
        uic.loadUi(os.path.join(self.controller.root_base.model.ui_path, "motor_calibration",
                                "motor_calibration_point_content.ui"),
                   self)
        motor = kwargs["motor"]
        self.min = 0
        self.max = motor["max"]-motor["min"]
        self.current_value = 0
        self.min_lb.setText(str(0))
        self.max_lb.setText(str(self.max))
        self.offset_slider.setMinimum(0)
        self.offset_slider.setMaximum(self.max)
        self.offset_slider.valueChanged.connect(self.value_changed)
        self.current_tb.textChanged.connect(lambda x: self.value_changed(int(x) if x.isdigit() else 0))
        self.increase_bn.clicked.connect(lambda x: self.value_changed(self.current_value + 1))
        self.decrease_bn.clicked.connect(lambda x: self.value_changed(self.current_value - 1))
        self.value_changed(0, False)

    def value_changed(self, value, with_controller=True):
        if not (self.min <= value <= self.max):
            if value<self.min:
                value=self.min
            else:
                value=self.max

        self.current_value = value
        # self.base_content.point.map.value_changed(id=self.base_content.id, offset=value)
        change_value_without_signal(self.offset_slider, value)
        change_value_without_signal(self.current_tb, value)
        if with_controller:
            self.controller.change_motor_offset(self.base_content.id, value)

    def update_content(self, *args, **kwargs):
        self.value_changed(kwargs.get("offsets")[self.base_content.id], with_controller=False)


class MotorCalibrationSchemeWidget(SchemeWidget):
    def __init__(self, parent, scheme_path=None, **kwargs):
        image_path = os.path.join(scheme_path, "image.png")
        SchemeWidget.__init__(self, parent=parent, image_path=image_path, **kwargs)
        self.menu_name = None
        self.scheme_path = scheme_path

    def update_controls(self, *args, **kwargs):
        for p in self.points:
            p.update(*args, **kwargs)

    def showEvent(self, event):
        self.load(path=self.scheme_path)

    def point_value_changed(self, point, *args, **kwargs):
        pass


if __name__ == "__main__":
    calibrator = BaseFrameworkQT(custom_widget_type=MotorCalibrationSchemeWidget, removable_points=False,
                                 scheme_path="/home/laptop/work/powerpoof/powerpoof_qt/data/motor_schemes/scheme1")
    calibrator.run()
