import os, sys

sys.path.append(os.path.join(sys.path[0], "powerpoof_tools"))
sys.path.append(os.path.join(sys.path[-1], "powerpoof_control"))
from powerpoof_tools.motor_calibration import MotorCalibratorView
from base_tool_qt import BaseFrameworkQT, change_value_without_signal
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QMessageBox
from PyQt5 import uic
from PyQt5.QtCore import Qt, QPoint
from motor_calibration_scheme_widget import MotorCalibrationSchemeWidget, CalibrationContent
from widgets.click_slider import ClickSlider


class MotorPositionPoPUpWidget(QWidget):
    def __init__(self, parent, id, controller, **kwargs):
        QWidget.__init__(self,parent=parent, **kwargs)
        self.controller = controller
        self.id = id
        self.parent_widget=parent
        uic.loadUi(os.path.join(os.path.join(self.controller.root_base.model.ui_path), "motor_calibration",
                                "position_popup_widget.ui"), self)
        config_motor = self.controller.root_base.model.robot_config[self.id]
        self.min = config_motor["min"]
        self.max = config_motor["max"]
        self.current_value = self.controller.model.positions[self.id]
        self.min_lb.setText(str(self.min))
        self.max_lb.setText(str(self.max))

        self.position_slider.setMinimum(self.min)
        self.position_slider.setMaximum(self.max)

        self.increase_bn.clicked.connect(lambda x: self.value_changed(self.current_value + 1))
        self.decrease_bn.clicked.connect(lambda x: self.value_changed(self.current_value - 1))
        self.current_tb.textChanged.connect(lambda x: self.value_changed(int(x) if x.isdigit() else 0))

        self.position_slider.valueChanged.connect(self.value_changed)

        self.hide()

    def value_changed(self, value):
        if not (self.min <= value <= self.max):
            if value < self.min:
                value = self.min
            else:
                value = self.max
        self.controller.change_motor_position(self.id, value)

    def update_content(self):
        self.current_value = self.controller.model.positions[self.id]
        change_value_without_signal(self.position_slider, self.current_value)
        change_value_without_signal(self.current_tb, self.current_value)

    def showEvent(self, event):
        QWidget.showEvent(self, event)

        #self.parent_widget.window().setEnabled(False)


class MotorCalibratorMotorSliderWidget(QWidget):
    def __init__(self, id, current, min, max, controller, parent=None):
        QWidget.__init__(self, parent)
        self.controller = controller
        uic.loadUi(
            os.path.join(os.path.join(self.controller.root_base.model.ui_path), "motor_calibration",
                         "motor_calibrator_motor_slider_widget.ui"),
            self)
        self.current = current
        self.id = id
        self.slider = ClickSlider(orientation=Qt.Horizontal)
        self.slider_container_layout.addWidget(self.slider)
        self.motor_name_lb.setText(
            "{}, Id: {}".format(self.controller.root_base.model.motor_names[self.id]["names"]["russian"], id))
        self.motor_offset_sb.setMinimum(min)
        self.motor_offset_sb.setMaximum(max)
        self.slider.setMinimum(min)
        self.slider.setMaximum(max)
        self.min_lb.setText(str(min))
        self.max_lb.setText(str(max))
        self.slider.valueChanged.connect(self.set_value)
        self.motor_offset_sb.valueChanged.connect(self.set_value)
        self.position_bn.clicked.connect(self.open_position_popup)
        self.set_value(self.current)

        self.position_widget = MotorPositionPoPUpWidget(self.controller.root_base.view,self.id, self.controller)
        self.position_widget.setWindowFlags(Qt.FramelessWindowHint)
        self.position_widget_opened = False

    def set_value(self, value, with_controller=True):
        change_value_without_signal(self.motor_offset_sb, value)
        change_value_without_signal(self.slider, value)
        if with_controller:
            self.controller.change_motor_offset(self.id, value)

    def set_position(self, value):
        pass

    def update_content(self, *args, **kwargs):
        # self.set_value(kwargs.get("offsets")[self.id], with_controller=False)
        self.set_value(self.controller.model.offsets[self.id], with_controller=False)
        self.position_widget.update_content()

    def open_position_popup(self, checked):
        if checked:
            # info = self.controller.root_base.robot.get_motor_info(self.id)
            # self.position_widget.set_value(info.position)
            p = self.position_bn.mapToGlobal(QPoint(0, 0))-self.controller.root_base.view.mapToGlobal(QPoint(0,0))
            self.position_widget.move(p)
            self.position_widget.move(p.x() - self.position_widget.width() / 2 + self.position_bn.width() / 2,
                                      p.y() - self.position_bn.height() + self.position_widget.height() / 2 + 4)
            self.position_widget.show()
        else:
            self.position_widget.hide()


class MotorCalibratorWidget(MotorCalibratorView, QWidget):
    def __init__(self, parent=None, *args, **kwargs):
        MotorCalibratorView.__init__(self, parent)
        QWidget.__init__(self, parent)
        uic.loadUi(
            os.path.join(self.controller.root_base.model.ui_path, "motor_calibration", "motor_calibrator_widget.ui"),
            self)
        self.update_config_bn.clicked.connect(self.controller.update_config)
        self.zero_position_bn.clicked.connect(self.controller.to_zero_position_all)
        self.motor_sliders = dict()
        self.motor_scheme = MotorCalibrationSchemeWidget(self,
                                                         scheme_path=os.path.join(
                                                             self.controller.root_base.model.data_path,
                                                             "motor_schemes/scheme1"),
                                                         removable_points=False, controller=self.controller,
                                                         point_radius=15, **kwargs)
        self.right_frame_layout.addWidget(self.motor_scheme)
        self.init_motor_sliders()

    def showEvent(self, event):
        QWidget.showEvent(self, event)
        self.motor_scheme.set_point_changed_callback(self.points_values_changed)

    def points_values_changed(self, *args, **kwargs):
        pass

    def update(self):
        self.motor_scheme.update_controls(offsets=self.model.offsets)
        for k, v in self.motor_sliders.items():
            v.update_content(offsets=self.model.offsets)
        QWidget.update(self)

    def init_motor_sliders(self):
        config = self.model.base.robot_config
        pairs = [(18,), (10, 14), (11, 15), (12, 16), (13, 17), (4, 9), (3, 8), (2, 7), (1, 6), (0, 5)]
        for p in pairs:
            layout = QHBoxLayout()
            for id in p:
                #self.motor_sliders[id] = MotorCalibratorMotorSliderWidget(id, config[id]["offset"], config[id]["min"],
                                                                         # config[id]["max"], self.controller)
                offset = config[id]["offset"]
                range = config[id]["calibration_range"]
                self.motor_sliders[id] = MotorCalibratorMotorSliderWidget(id, offset, offset-range,offset+range, self.controller)
                layout.addWidget(self.motor_sliders[id])

            self.offsets_layout.addLayout(layout)

    def update_config_confirm_dialog(self, text):
        return QMessageBox.question(self, "", text, QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes


if __name__ == "__main__":
    calibrator = BaseFrameworkQT(custom_widget_type=MotorCalibratorWidget, detailed_content=CalibrationContent)
    calibrator.run()
