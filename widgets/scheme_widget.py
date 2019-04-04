import os, yaml
from widgets.point_map_widget import PointMapWidget, PointContent
from base_tool_qt import BaseFrameworkQT, FrameworkChild
from PyQt5.QtWidgets import QWidget, QFileDialog, QAction
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic


class BaseMotorPointContent(PointContent):
    def __init__(self, point, parent, *args, **kwargs):
        PointContent.__init__(self, point, parent)
        self.id = kwargs.get("id")

    def value_changed(self, *args, **kwargs):
        self.point.value_changed(*args, **kwargs)


class MotorPointContent(BaseMotorPointContent):
    def __init__(self, point, parent, **kwargs):
        BaseMotorPointContent.__init__(self, point, parent, **kwargs)
        uic.loadUi(
            os.path.join(kwargs.get("controller").root_base.model.ui_path, "motor_scheme", "point_state_content_ex.ui"),
            self)
        self.name = kwargs.get("name")
        self.pin = kwargs.get("pin")
        self.motor_name_tb.setText(self.name)
        self.pin_lb.setText("Pin: {}".format(self.pin))
        self.id_lb.setText("Id: {}".format(self.id))
        self.content = kwargs.get("detailed_content")(point, parent=self, **kwargs)
        self.content_layout.addWidget(self.content)

    def update_content(self, *args, **kwargs):
        self.content.update_content(*args, **kwargs)


class SchemeWidget(PointMapWidget):
    def __init__(self, parent, *args, **kwargs):
        self.scheme_path = kwargs.get("scheme_path")
        PointMapWidget.__init__(self, parent=parent, content_type=MotorPointContent, *args, **kwargs)
        self.point_radius = kwargs.get("point_radius")
        self.controller=kwargs.get("controller")

    def init(self):
        if self.scheme_path:
            self.load(self.scheme_path)

    def update_content(self, *args, **kwargs):
        for p in self.points:
            p.update(*args, **kwargs)

    def __create_image(self, image_path=None):
        self.image_path = image_path if image_path else QFileDialog().getOpenFileName()[0]

        self.image_widget_layot.addWidget(self.robot_image)
        self.robot_image.point_value_changed_callback = self.point_value_changed
        self.robot_image.show()

    def __get_robot_config(self):
        with open(os.path.join(BaseFrameworkQT.data_path, "default_robot_config.yaml")) as f:
            return {m["id"]: m for m in yaml.load(f)["motors"]}


    def point_value_changed(self, *args, **kwargs):
        pass

    def set_point_changed_callback(self, new):
        self.point_value_changed_callback = new

    def create(self):
        self.controller.root_base.model.motor_names
        iw, ih = self.robot_image.img_size
        x_step = self.point_radius * 2 / iw
        y_step = self.point_radius * 2 / ih
        x, y = x_step, y_step
        robot_config = self.__get_robot_config()
        for m in model.motor_names.values():
            self.robot_image.add_point(x, y, name=m["names"]["russian"], id=m["id"],
                                       pin=robot_config[m["id"]]["pin"])
            if x >= 1.0:
                y += y_step
            else:
                x += x_step
        self.init_points()

    def save(self):
        path = QFileDialog().getSaveFileName()[0]
        try:
            os.mkdir(path)
        except FileExistsError and FileNotFoundError:
            return
        with open(os.path.join(path, "data.yaml"), "w") as f:
            data = dict()
            for p in self.robot_image.points:
                data[p.expanded_state.content.id] = {"x": p.px, "y": p.py}
            yaml.dump(data, f, default_flow_style=False)
            return

    def load(self, path=None):
        if path is None:
            tmp_path = QFileDialog().getExistingDirectory(directory=BaseFrameworkQT.data_path)
            if os.path.isdir(tmp_path):
                path = tmp_path
        self.__load(path)

    def __load(self, scheme_path):
        self.scheme_path = scheme_path
        self.load_image(os.path.join(self.scheme_path, "image.png"))
        self.image_loaded()

    def image_loaded(self):
        motor_names = self.controller.root_base.model.motor_names
        with open(os.path.join(self.scheme_path, "data.yaml"), "r") as f:
            data = yaml.load(f)
        robot_config = self.__get_robot_config()
        for k, v in data.items():
            self.add_point(v["x"], v["y"], name=motor_names[k]["names"]["russian"], id=k,
                           pin=robot_config[k]["pin"], motor=robot_config[k])

    def close(self):
        self.robot_image.close()
        QWidget.close(self)


if __name__ == "__main__2":
    framework = BaseFrameworkQT(custom_widget_type=SchemeWidget,
                                auto_expand=False, manual_add=False, point_radius=15)
    framework.run()

if __name__ == "__main__":
    framework = BaseFrameworkQT(custom_widget_type=SchemeWidget,
                                scheme_path="/home/laptop/work/powerpoof/powerpoof_qt/data/motor_schemes/scheme1",
                                auto_expand=False, manual_add=False, point_radius=15)
    framework.run()
