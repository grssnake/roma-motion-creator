from widgets.image_view_widget import ImageViewWidget
import sys, os
from base_tool_qt import BaseFrameworkQT
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QSlider, QCheckBox, QSpinBox, QComboBox, QLabel, \
    QGraphicsScene, QGraphicsPixmapItem, QPushButton, QDialog
from PyQt5 import uic
from PyQt5.QtGui import QPixmap, QPainter, QResizeEvent, QColor, QFont, QBrush, QPen, QColor
from PyQt5.QtCore import Qt, QPoint


class EmptyPointState(QWidget):
    def __init__(self, point):
        QWidget.__init__(self)
        self.point = point
        self.resize(200, 130)
        self.setWindowFlags(Qt.FramelessWindowHint)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.point.closed = True
            self.close()


class PointContainer(EmptyPointState):
    def __init__(self, point, content_type=None, **content_kwargs):
        EmptyPointState.__init__(self, point)
        self.content = None
        if content_type:
            self.content = content_type(self.point, **content_kwargs)

    def update_content(self, *args, **kwargs):
        if self.content:
            self.content.update_content(*args, **kwargs)


class StaticPointContainer(PointContainer):
    def __init__(self, point, content_type=None, **content_kwargs):
        PointContainer.__init__(self, point, content_type=content_type, **content_kwargs)
        uic.loadUi(os.path.join(content_kwargs.get("controller").root_base.model.ui_path, "point_map", "point_state_container.ui"), self)
        if content_type:
            self.content_widget_layout.addWidget(self.content)


class RemovablePointContainer(PointContainer):
    def __init__(self, point, content_type=None, **content_kwargs):
        PointContainer.__init__(self, point, content_type=content_type, **content_kwargs)
        uic.loadUi(
            os.path.join(content_kwargs.get("controller").root_base.model.ui_path, "point_map",
                         "removable_point_state_container.ui"),
            self)
        self.remove_bn.clicked.connect(self.point.remove)
        self.move_bn.clicked.connect(self.point.set_moving)
        if content_type:
            self.content_widget_layout.addWidget(self.content)

    def set_lock_remove_bn(self, state):
        self.remove_bn.setEnabled(not state)


class PointContent(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, parent=kwargs.get("parent"))

    def update_content(self, *args, **kwargs):
        pass


class MapPoint(object):
    def __init__(self, pos, map, point_radius=10, auto_expand=True, expand_on_creation=False, removable=True,
                 content_type=PointContent, **content_kwargs):
        self.px, self.py = pos
        self.map = map
        self.x = None
        self.y = None
        self.radius = point_radius
        self._mouse_entered = False
        self.__content_type = content_type
        state_type = RemovablePointContainer if removable else StaticPointContainer
        self.expanded_state = state_type(self, content_type=self.__content_type, **content_kwargs)
        self.map = map
        self.__creation = True
        self.__expand_on_creation = expand_on_creation
        self.__auto_expand = auto_expand
        self.__closed = False

    def value_changed(self, *args, **kwargs):
        self.map.point_value_changed_callback(self, *args, **kwargs)

    def update(self, *args, **kwargs):
        self.expanded_state.update_content(*args, **kwargs)

    @property
    def closed(self):
        return self.__closed

    @closed.setter
    def closed(self, value):
        self.__closed = value

    @property
    def mouse_entered(self):
        return self._mouse_entered

    @mouse_entered.setter
    def mouse_entered(self, value):
        self._mouse_entered = value

    def close_expanded(self):
        self.expanded_state.close()

    def draw(self, painter):
        painter.setBrush(QColor(213, 235, 21, 255))
        painter.drawEllipse(self.x, self.y, self.radius, self.radius)

    def remove(self):
        self.expanded_state.close()
        self.map.remove_point(self)

    def set_moving(self):
        self.expanded_state.close()
        self.map.set_point_moving(self)
        self.expanded_state.set_lock_remove_bn(True)

    def finish_moving(self, x, y):
        self.px, self.py = x, y
        self.calc_pos()
        self.expanded_state.set_lock_remove_bn(False)

    def calc_pos(self):
        x, y = self.map.img_pos
        w, h = self.map.img_size
        self.x = x + w * self.px - self.radius / 2
        self.y = y + h * self.py - self.radius / 2

    def in_area(self, x, y):
        x1 = self.x - self.radius
        x2 = self.x + self.radius
        y1 = self.y - self.radius
        y2 = self.y + self.radius
        return x1 <= x <= x2 and y1 <= y <= y2

    def mouse_pressed(self, x, y, gx, gy):
        if not self.__auto_expand:
            self.__show_expanded_state(gx, gy)

    def is_mouse_entered(self, x, y, gx, gy):
        if self.in_area(x, y):
            if not self._mouse_entered:
                self.on_mouse_enter(gx, gy)
                self._mouse_entered = True
        else:
            if self._mouse_entered:
                self.on_mouse_leave()
                self._mouse_entered = False

    def __show_expanded_state(self, x, y):
        self.expanded_state.move(x - self.expanded_state.width() / 2, y - self.expanded_state.height() / 2)
        self.expanded_state.show()

    def on_mouse_enter(self, x, y):
        if not self.__closed:
            if self.__creation:
                if self.__expand_on_creation:
                    self.__show_expanded_state(x, y)
                    self.__expand_on_creation = False
                    return
            if self.__auto_expand:
                self.__show_expanded_state(x, y)

    def on_mouse_leave(self):
        if self.__closed:
            self.__closed = False
        else:
            self.expanded_state.close()


class PointMapWidget(ImageViewWidget):
    def __init__(self, *args, **kwargs):
        ImageViewWidget.__init__(self, parent=kwargs.get("parent"), image_path=kwargs.get("image_path"))
        self.__removable_points = kwargs.get("removable_points")
        self.__content_type = kwargs.get("content_type")
        self.__expand_on_creation = kwargs.get("expand_on_creation")
        self.__auto_expand = kwargs.get("auto_expand")
        self.__point_radius = kwargs.get("point_radius")
        self.__current_moving_point = None
        self.manual_add = kwargs.get("manual_add")
        self.points = list()
        self.__point_value_changed_callback = None
        self.__point_kwargs = kwargs

    def update_points(self, *args, **kwargs):
        for p in self.points:
            p.update(*args, **kwargs)

    @property
    def point_value_changed_callback(self):
        return self.__point_value_changed_callback

    @point_value_changed_callback.setter
    def point_value_changed_callback(self, new):
        self.__point_value_changed_callback = new

    def add_point(self, px, py, **kwargs):
        p = MapPoint((px, py), self, **kwargs, removable=self.__point_kwargs.get("removable_points"),
                     **self.__point_kwargs)
        self.point_added(p)
        self.points.append(p)
        p.calc_pos()

    def remove_point(self, point):
        self.point_removed(point)
        self.points.remove(point)
        self.viewport().repaint()

    def set_point_moving(self, point):
        self.__current_moving_point = point

    def point_added(self, point):
        pass

    def point_removed(self, point):
        pass

    def on_image_click(self, event):

        x, y = event.x(), event.y()
        gx, gy = event.globalX(), event.globalY()
        iw, ih = self.img_size
        ix, iy = self.img_pos

        px = (x - ix) / iw
        py = (y - iy) / ih

        if self.__current_moving_point:
            if not any([p.in_area(x, y) for p in self.points]):
                self.__current_moving_point.finish_moving(px, py)
                self.__current_moving_point = None
        else:
            for p in self.points:
                if p.in_area(x, y):
                    p.mouse_pressed(x, y, gx, gy)
                    return
            if self.manual_add:
                self.add_point(px, py)
                self.check_points_for_mouse_enter(x, y, gx, gy)

        self.viewport().repaint()

    def point_value_changed(self, point, *args, **kwargs):
        if self.__point_value_changed_callback:
            self.__point_value_changed_callback(point, *args, **kwargs)

    def paintEvent(self, event):
        if self.inited:
            ImageViewWidget.paintEvent(self, event)
            qp = QPainter(self.viewport())
            iw, ih = self.img_size
            ix, iy = self.img_pos
            for p in self.points:
                p.draw(qp)

    def resizeEvent(self, event):
        ImageViewWidget.resizeEvent(self, event)
        for p in self.points:
            p.calc_pos()

    def check_points_for_mouse_enter(self, x, y, gx, gy):
        for p in self.points:
            p.is_mouse_entered(x, y, gx, gy)

    def on_image_mouse_move(self, event):
        self.check_points_for_mouse_enter(event.x(), event.y(), event.globalX(), event.globalY())

    def close(self):
        for p in self.points:
            p.close_expanded()
        ImageViewWidget.close(self)


if __name__ == "__main__":
    framework = BaseFrameworkQT(custom_widget_type=PointMapWidget,
                                image_path="/home/laptop/work/powerpoof/powerpoof_qt/data/motor_schemes/scheme1/image.png",
                                auto_expand=False, expand_on_creation=True, hide_connection=True, manual_add=True)
    framework.run()
