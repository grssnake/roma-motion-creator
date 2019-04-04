import sys, os

sys.path.append(os.path.join(sys.path[0], "powerpoof_tools"))
sys.path.append(os.path.join(sys.path[-1], "powerpoof_control"))
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QSlider, QSpinBox, QSizePolicy, QFileDialog, QAction, \
    QCheckBox
from PyQt5 import uic
from PyQt5.QtCore import Qt
from powerpoof_tools.motion_creator import *
from base_tool_qt import BaseFrameworkQT, FrameworkChild, change_value_without_signal
from widgets.click_slider import ClickSlider
from motor_calibration_scheme_widget import PointContent
from widgets.scheme_widget import SchemeWidget


class SchemePointContent(PointContent):
    def __init__(self, *args, **kwargs):
        self.base_content = kwargs.get("parent")
        PointContent.__init__(self, parent=self.base_content)
        self.controller = kwargs.get("controller")
        uic.loadUi(os.path.join(self.controller.root_base.model.ui_path, "motion_creator",
                                "scheme_point_content.ui"),
                   self)
        motor = kwargs["motor"]
        self.id = motor["id"]
        self.min = motor["min"]
        self.max = motor["max"]
        self.current_value = 0
        self.min_lb.setText(str(self.min))
        self.max_lb.setText(str(self.max))
        self.position_slider.setMinimum(self.min)
        self.position_slider.setMaximum(self.max)
        self.position_slider.valueChanged.connect(self.value_changed)
        self.current_tb.textChanged.connect(lambda x: self.value_changed(int(x) if x.isdigit() else 0))
        self.increase_bn.clicked.connect(lambda x: self.value_changed(self.current_value + 1))
        self.decrease_bn.clicked.connect(lambda x: self.value_changed(self.current_value - 1))
        self.value_changed(0, False)

    def value_changed(self, value, with_controller=True):
        if not (self.min <= value <= self.max):
            if value < self.min:
                value = self.min
            else:
                value = self.max

        self.current_value = value
        if with_controller:
            self.controller.change_motor_state(self.base_content.id, value)

    def update_content(self, *args, **kwargs):
        value = self.controller.model.current_step.motors[self.id]
        change_value_without_signal(self.position_slider, value)
        change_value_without_signal(self.current_tb, value)


class MotionCreatorWidget(MotionCreatorView, FrameworkChild):
    def __init__(self, parent=None, *args, **kwargs):
        MotionCreatorView.__init__(self, parent, *args, **kwargs)

        FrameworkChild.__init__(self, parent)
        self.bars = dict()
        self._init_widgets(**kwargs)
        self.controller.start()

    def _init_widgets(self, **kwargs):
        uic.loadUi(os.path.join(self.controller.root_base.model.ui_path, "motion_creator", "motion_creator_widget.ui"),
                   self)

        scheme_path = os.path.join(self.controller.root_base.model.data_path, "motor_schemes", kwargs.get("scheme"))

        self.scheme = SchemeWidget(self, scheme_path=scheme_path, controller=self.controller, **kwargs)
        self.scheme_layout.addWidget(self.scheme)
        self._init_motor_bars()
        self.steps_sb.setMinimum(0)
        self.steps_sb.setMaximum(0)
        self.add_step_button.clicked.connect(lambda: self.controller.add_step())
        self.steps_sb.valueChanged.connect(lambda x: self.controller.set_step(x))
        self.step_time_sb.valueChanged.connect(self.controller.change_step_delay)
        self.start_bn.clicked.connect(self.controller.start_execution)
        self.stop_bn.clicked.connect(self.controller.stop_execution_thread)
        self.remove_step_bn.clicked.connect(self.controller.remove_step)
        self.set_to_default_bn.clicked.connect(lambda x: self.controller.step_to_default())
        self.copy_bn.clicked.connect(lambda: self.controller.copy_step())
        self.paste_bn.clicked.connect(lambda: self.controller.paste_step())
        self.real_time_control_cb.stateChanged.connect(
            lambda state: self.controller.set_control_in_real_time(state == Qt.Checked))
        self.in_cycle_cb.stateChanged.connect(lambda state: self.controller.set_in_cycle(state == Qt.Checked))

    def closeEvent(self, QCloseEvent):
        self.controller.stop_execution_thread()

    def _init_motor_bars(self):
        pairs = [(18,), (10, 14), (11, 15), (12, 16), (13, 17), (4, 9), (3, 8), (2, 7), (1, 6), (0, 5)]
        for p in pairs:
            layout = QHBoxLayout()
            for id in p:
                motor = self.controller.root_base.model.robot_config[id]
                b = MotorBarWidget(self, id, motor["min"], motor["max"],
                                   name=self.controller.root_base.model.motor_names[id]["names"]["russian"],
                                   with_pair=len(p) == 2)
                layout.addWidget(b)
                self.bars[id] = b
            self.bars_layout.addLayout(layout)

    def update(self):
        steps_count = len(self.model.steps)
        current_step = self.model.current_step
        current_step_index = self.model.steps.index(current_step)
        self.steps_sb.setMaximum(steps_count - 1 if steps_count > 0 else 0)
        change_value_without_signal(self.steps_sb, current_step_index)
        change_value_without_signal(self.step_time_sb, current_step.delay)
        self.paste_bn.setEnabled(self.model.step_to_copy is not None)
        self.update_motor_bars()
        self.scheme.update_content()

    def update_motor_bars(self):
        step = self.model.current_step
        for id, m in self.controller.base.model.robot_config.items():
            # self.bars[id].set_value(self.model.current_step.motors[id])
            self.bars[id].update_content()

    def save_steps_dialog(self):
        return QFileDialog.getSaveFileName()[0]

    def load_steps_dialog(self):
        return QFileDialog.getOpenFileName()[0]

    def init_menu(self):
        self.menu_name = "Motion creator"

        load_action = QAction("Open")
        load_action.triggered.connect(self.controller.load_steps)
        self.file_menu.append(load_action)

        save_action = QAction("Save")
        save_action.triggered.connect(self.controller.save_steps)
        self.file_menu.append(save_action)


class MotorBarWidget(QWidget):
    def __init__(self, parent, m_id, minimum, maximum, name=None, with_pair=False):
        """
        :param parent:
        :param m_id:
        :param minimum:
        :param maximum:
        :param name:
        :type parent MotionCreatorWindow
        """
        QWidget.__init__(self)
        self.parent = parent
        uic.loadUi(
            os.path.join(os.path.join(self.parent.controller.root_base.model.ui_path), "motion_creator",
                         "motion_creator_motor_slider_widget.ui"),
            self)
        self.id = m_id
        self.min = minimum
        self.max = maximum
        self.with_pair = with_pair
        self.min_lb.setText(str(self.min))
        self.max_lb.setText(str(self.max))
        self.motor_name_lb.setText("{}, id: {}".format(name, self.id))
        self.slider = ClickSlider(orientation=Qt.Horizontal)
        self.slider_container_layout.addWidget(self.slider)
        self.motor_position_sb.setMinimum(self.min)
        self.motor_position_sb.setMaximum(self.max)
        self.slider.setMinimum(self.min)
        self.slider.setMaximum(self.max)
        self.slider.valueChanged.connect(self.set_value)
        self.motor_position_sb.valueChanged.connect(self.set_value)

        if self.with_pair:
            self.synchronous_cb = QCheckBox()
            self.synchronous_cb.setTristate(False)
            self.cb_layout.addWidget(self.synchronous_cb)
            # self.synchronous_cb.stateChanged.connect(lambda state: self.set_synchronous(state == Qt.Checked))
            self.synchronous_cb.stateChanged.connect(self.set_synchronous)

    def set_value(self, value):
        self.parent.controller.change_motor_state(self.id, value)

    def update_content(self):
        value = self.parent.controller.model.current_step.motors[self.id]
        change_value_without_signal(self.motor_position_sb, value)
        change_value_without_signal(self.slider, value)
        if self.with_pair:
            for b in self.parent.model.connected_motors:
                if self.id in b:
                    change_value_without_signal(self.synchronous_cb, Qt.Checked)
                    return
            change_value_without_signal(self.synchronous_cb, Qt.Unchecked)

    def set_synchronous(self, state):
        if self.with_pair:
            self.parent.controller.set_motors_connected(self.id, state)


if __name__ == "__main__":
    calibrator = BaseFrameworkQT(custom_widget_type=MotionCreatorWidget, scheme="scheme1",
                                 detailed_content=SchemePointContent)
    calibrator.run()
