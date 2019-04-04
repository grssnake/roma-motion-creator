import sys, os
from collections import OrderedDict
from powerpoof_tools.base_tool import BaseFrameworkView
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QSlider, QCheckBox, QSpinBox, QComboBox, QLabel, \
    QAction, QMenu, QMessageBox, QFileDialog, QPushButton, QLineEdit
from PyQt5 import uic


def change_value_without_signal(widget, value):
    """
    :param widget:""
    :param value:""
    :type widget: QWidget
    :return:
    """
    widget.blockSignals(True)
    widget_type = type(widget)
    if widget_type == QSlider or widget_type == QSpinBox or isinstance(widget, QSlider):
        widget.setValue(value)
    elif widget_type == QCheckBox:
        widget.setCheckState(value)
    elif widget_type == QComboBox:
        widget.setCurrentText(value)
    elif widget_type == QLabel or widget_type ==QLineEdit:
        widget.setText(str(value))
    widget.blockSignals(False)


class BaseFrameworkQT(BaseFrameworkView, QMainWindow):
    app = None
    root_path = os.path.dirname(os.path.realpath(__file__))
    data_path = os.path.join(root_path, "data")

    def __init__(self, data_path=data_path, custom_widget_type=None, hide_connection=False, *args, **kwargs):
        if self.app is None:
            self.app = self.app = QApplication(sys.argv)
        QMainWindow.__init__(self)
        BaseFrameworkView.__init__(self, data_path)
        uic.loadUi(os.path.join(self.model.ui_path, "base_frame_window.ui"), self)
        self.connection_types_cmb.currentIndexChanged.connect(
            lambda: self.controller.set_connection_type(self.connection_types_cmb.currentText()))
        self.connection_address_cmb.currentTextChanged.connect(self.controller.set_connection_device_address)
        self.save_connection_address_bn.clicked.connect(self.controller.save_connection_address_to_config)
        self.restore_connection_address_bn.clicked.connect(self.controller.restore_connection_address_from_config)
        self.connection_bn.enterEvent = lambda x: self.connection_bn.setText(
            "Disconnect" if self.model.connected else "Connect")
        self.connection_bn.leaveEvent = lambda x: self.connection_bn.setText(
            "Connected" if self.model.connected else "Disconnected")
        self.connection_bn.clicked.connect(
            lambda x:self.controller.disconnect_from_robot() if self.model.connected
            else self.controller.connect_to_robot())
        self.connection_bn.setMouseTracking(True)

        self.mode_bn.enterEvent = lambda x: self.mode_bn.setText(
            "Only safe" if self.model.only_safe_mode else "Go full" if self.model.safe_mode else "Go safe")
        self.mode_bn.leaveEvent = lambda x: self.mode_bn.setText(
              "Only safe" if self.model.only_safe_mode else "Safe" if self.model.safe_mode else "Full")
        self.mode_bn.clicked.connect(
            lambda x: self.controller.go_to_full_mode()
            if self.model.safe_mode else self.controller.go_to_safe_mode())
        self.mode_bn.setMouseTracking(True)

        self.custom_widget_type = custom_widget_type
        self.hide_connection_panel = hide_connection
        self.child_widget = None
        self.menus = dict()
        self.__custom_widget_args=kwargs

    def __update_connect_bn(self):
        if self.model.connected:
            self.connection_bn.setText("Connected")
            self.mode_bn.setEnabled(True)
        else:
            self.connection_bn.setText("Disconnected")
            self.mode_bn.setEnabled(False)

    def update(self):
        if self.hide_connection_panel:
            self.connection_frame.hide()
        self.__update_connect_bn()
        con_type = self.model.connection_type
        change_value_without_signal(self.connection_types_cmb,
                                    con_type[0].replace(con_type[0], con_type[0].upper()) + con_type[1:])
        change_value_without_signal(self.connection_address_cmb, self.model.connection_address)
        if self.model.only_safe_mode:
            self.mode_bn.setText("Only safe")
            self.mode_bn.setEnabled(False)
        if self.child_widget:
            self.child_widget.setEnabled(self.model.connected)


        self.connection_types_cmb.setEnabled(not self.model.connected)
        self.connection_address_cmb.setEnabled(not self.model.connected)
        self.restore_connection_address_bn.setEnabled(not self.model.connected)

    def start(self):
        BaseFrameworkView.start(self)
        self.init_menu_begin()
        if self.custom_widget_type:
            self.child_widget = self.custom_widget_type(parent=self, **self.__custom_widget_args)
            self.add_child_widget_menu(self.child_widget)
            self.custom_frame_layout.addWidget(self.child_widget)
            self.controller.set_child(self.child_widget.controller)
        self.init_menu_end()
        self.update()

    def show(self):
        QMainWindow.show(self)

    def init_menu_begin(self):
        file_menu = QMenu("File")
        self.menu_bar.addMenu(file_menu)
        self.menus["File"] = file_menu

    def init_menu_end(self):
        self.menus["File"].addSeparator()
        close_action = QAction("Close", self.menus["File"])
        close_action.triggered.connect(self.close)
        self.menus["File"].addAction(close_action)

    def add_action(self, menu_name, action_name, trig_func):
        action = QAction(action_name)
        action.triggered.connect(trig_func)
        self.menus[menu_name][action_name] = action

    def load_menu(self):
        vv = self.menus.keys()
        for km in self.menus:
            menu = self.menus[km]
            qmenu = QMenu(km, self.menu_bar)
            for ka, action in menu.items():
                separate = False
                if ka.startswith("sep_"):
                    separate = True
                    action = QAction(action, qmenu)
                    action.setEnabled(False)
                else:
                    pos = ka.find("_")
                    if pos != -1:
                        name = ka[pos + 1:]
                    else:
                        name = ka
                    action.setText(name)
                qmenu.addAction(action)
                if separate:
                    qmenu.addSeparator()
            self.menu_bar.addMenu(qmenu)

    def add_child_widget_menu(self, widget):
        if hasattr(widget,"menu") and  widget.menu is not None and isinstance(widget, FrameworkChild):
            menu = QMenu(widget.menu_name, self.menu_bar)
            for a in widget.menu:
                menu.addAction(a)
            self.menu_bar.addMenu(menu)
            if widget.file_menu:
                action = QAction(widget.menu_name, self.menus["File"])
                action.setEnabled(False)
                self.menus["File"].addSeparator()
                self.menus["File"].addAction(action)
                self.menus["File"].addSeparator()

                for a in widget.file_menu:
                    self.menus["File"].addAction(a)

    def run(self):
        self.start()
        self.show()
        exit(self.app.exec_())

    def closeEvent(self, event):
        if self.child_widget:
            self.child_widget.close()
        QMainWindow.closeEvent(self, event)

    def invalid_config_crc_warning_dialog(self, text):
        res = QMessageBox().question(self, "", text, buttons=QMessageBox.Yes | QMessageBox.No| QMessageBox.Cancel)
        if res == QMessageBox.Yes:
            return "calibrate"
        elif res == QMessageBox.No:
            return "default"
        else:
            return "safe"

    def connect_to_robot_error(self, text):
        QMessageBox().critical(self,"", text,QMessageBox.Ok)

    def no_connection_type_warning(self, text):
        QMessageBox().warning(self, "", text, QMessageBox.Ok)

    def no_connection_address_warning(self, text):
        QMessageBox().warning(self, "", text, QMessageBox.Ok)

    def no_user_data_but_found_dialog(self, text):
        return QMessageBox().question(self, "", text, QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes

    def set_default_user_data_path_dialog(self, text):
        return QMessageBox().question(self, "", text, QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes

    def set_user_data_path_dialog(self, text):
        return QFileDialog.getOpenFileName(parent=self, directory=os.path.expanduser("~"))[0]


class FrameworkChild(QWidget):
    def __init__(self, base_framework):
        QWidget.__init__(self, base_framework)
        self.file_menu = list()
        self.menu = list()
        self.menu_name = None
        self.base_framework=base_framework
        self.init_menu()

    def init_menu(self):
        pass

    @staticmethod
    def add_action(name, menu_dict, separator=False):
        if separator:
            action = QAction(name)
            action.setEnabled(False)
            menu_dict["separator_{}".format(name)] = action
        else:
            menu_dict[name] = QAction(name)




if __name__ == "__main__":
    framework = BaseFrameworkQT()
    framework.run()
