import yaml, os, json
from powerpoof_control.robot_commander import RobotCommander


class Model(object):
    def __init__(self):
        pass


def update_view(f):
    def decorate(self, *args, update=True, **kwargs):
        ret = f(self, *args, **kwargs)
        if self.view and update:
            self.view.update()
        return ret

    return decorate


class Controller(object):
    def __init__(self, model, view=None):
        """
        :param model: ""
        :param view: ""
        :type model: Model
        :type view: View
        """
        self.model = model
        self.view = view

    def set_view(self, view):
        self.view = view


class View(object):
    def __init__(self, controller=None):
        """
        :param controller: ""
        :type controller: Controller
        """
        self.controller = None
        self.model = None
        if controller:
            self.set_controller(controller)

    def set_controller(self, controller):
        self.controller = controller
        self.controller.set_view(self)
        self.model = self.controller.model


class ChildModel(Model):
    def __init__(self, base=None):
        Model.__init__(self)
        self.base = base

    def set_base(self, base):
        self.base = base


class ChildController(Controller):
    def __init__(self, model, base):
        Controller.__init__(self, model)
        self.base = base
        self.model.set_base(self.base.model)
        self.root_base = self.get_root_base()

    def get_root_base(self):
        current = self
        while hasattr(current, "base"):
            current = current.base
        return current.controller

    def on_connect(self):
        pass


class BaseFrameworkModel(Model):
    def __init__(self):
        Model.__init__(self)
        self.data_path = None
        self.ui_path = None
        self.config_path = None
        self.config = None
        self.robot_config = None
        self.robot_config_path = None
        self.connected = False
        self.connection_type = None
        self.connection_address = None
        self.safe_mode = True
        self.only_safe_mode = False
        self.motor_pairs = [(18,), (10, 14), (11, 15), (12, 16), (13, 17), (4, 9), (3, 8), (2, 7), (1, 6), (0, 5)]


class BaseFrameworkController(Controller):
    MOTOR_COUNT = 19

    def __init__(self, data_path, model=BaseFrameworkModel(), view=None):
        """
        :param data_path: ""
        :param model: ""
        :param view: ""
        :type model: BaseFrameworkModel
        """
        Controller.__init__(self, model, view=view)
        self.model.ui_path = os.path.join(data_path, "ui")
        self.model.config_path = os.path.join(data_path, "config.yaml")
        self.robot = None
        self.model.data_path = data_path
        self.child = None
        with open(self.model.config_path, "r") as f:
            self.model.config = yaml.load(f)

        if not self.validate_config_structure():
            raise RuntimeError("Invalid configuration")

    def set_child(self, child):
        self.child = child

    def validate_config_structure(self):
        fields = {"robot_name": None,
                  "robot_communicator": {"default": None, "wired": None, "wireless": None},
                  "user_data": {"folder_path": None}}

        def check(config, template):
            matching = True
            if config is None:
                return False
            if template:
                for f in template:
                    if f in config:
                        matching = check(config[f], template[f])
                    else:
                        return False
            return matching

        return check(self.model.config, fields)

    def write_config_to_file(self):
        with open(self.model.config_path, "w") as f:
            yaml.dump(self.model.config, f, default_flow_style=False)

    def start(self):
        with open(os.path.join(self.model.data_path, "default_robot_config.yaml")) as f:
            self.model.robot_config = {m["id"]: m for m in yaml.load(f)["motors"]}
        with open(os.path.join(self.model.data_path, "motor_names.yaml")) as f:
            self.model.motor_names = yaml.load(f)
            self.model.motor_names = {m["id"]: m for m in self.model.motor_names}
            for k,v in self.model.motor_names.items():
                v["names"]["russian"]=v["names"]["russian"].encode("windows-1251").decode()
        self.set_connection_type(self.model.config["robot_communicator"]["default"])
        self.view.update()

    @update_view
    def set_connection_type(self, type):
        if not self.model.connected:
            self.model.connection_type = type.lower()
            self.set_connection_device_address(self.model.config["robot_communicator"][self.model.connection_type],
                                               update=False)

    @update_view
    def set_connection_device_address(self, address):
        if not self.model.connected:
            self.model.connection_address = address

    def save_connection_address_to_config(self):
        self.model.config["robot_communicator"][self.model.connection_type] = self.model.connection_address
        self.write_config_to_file()

    def restore_connection_address_from_config(self):
        self.set_connection_type(self.model.connection_type)

    @update_view
    def connect_to_robot(self):
        if not self.model.connected:
            if self.model.connection_type is None:
                self.view.no_connection_type_warning("Error: Select connection type")
                return
            if self.model.connection_address is None:
                self.view.no_connection_address_warning("Error: Set device address type")
                return
            try:
                self.robot = RobotCommander(self.model.robot_config, path=self.model.connection_address)
                self.robot.go_to_safe_mode()
                self.model.connected = True
                state = self.robot.check_state()
                if state == RobotCommander.STATUS_INVALID_CONFIG_CRC:
                    result = self.view.invalid_config_crc_warning_dialog(
                        "Robot configuration was changed unsafely.\n"
                        "Now you in safe mode(motor control disabled).\n"
                        "Please select:\n"
                        "   'Yes' to fix this in calibration mode.\n"
                        "   'No' to restore default config\n"
                        "   'Cancel' to stay in safe mode")
                    if result == "calibrate":
                        pass
                    elif result == "default":
                        self.upload_default_config_to_robot()
                    elif result == "safe":
                        self.model.only_safe_mode = True
                self.child.on_connect()
            except Exception as e:
                self.view.connect_to_robot_error("Connection error:\n{}".format(str(e)))

    @update_view
    def disconnect_from_robot(self):
        if self.model.connected:
            self.robot.close()
            self.model.connected = False
            self.model.safe_mode = True

    @update_view
    def go_to_safe_mode(self):
        if self.model.connected:
            self.robot.go_to_safe_mode()
            self.model.safe_mode = True

    @update_view
    def go_to_full_mode(self):
        if self.model.connected and not self.model.only_safe_mode:
            self.robot.go_to_full_mode()
            self.model.safe_mode = False

    def upload_default_config_to_robot(self):
        with open(os.path.join(self.model.data_path, "default_robot_config.yaml"), "r") as f:
            c = yaml.load(f)
            self.robot.upload_config(c)


class BaseFrameworkView(View):
    def __init__(self, data_path=None):
        View.__init__(self, BaseFrameworkController(data_path, view=self))
        # self.controller =

    def invalid_config_crc_warning_dialog(self, text):
        pass

    def connect_to_robot_error(self, text):
        pass

    ####################################################

    def new_robot_config_path_dialog(self, text):
        pass

    def save_question_dialog(self, text):
        pass

    def get_robot_communicator_path_dialog(self, text):
        pass

    def no_connection_type_warning(self, text):
        pass

    def no_connection_address_warning(self, text):
        pass

    def no_user_data_but_found_dialog(self, text):
        pass

    def set_default_user_data_path_dialog(self, text):
        pass

    def set_user_data_path_dialog(self, text):
        pass

    ###########################################

    def start(self):
        self.controller.start()

    def update(self):
        pass


class Console(BaseFrameworkView):
    def __init__(self, config_path):
        BaseFrameworkView.__init__(self, config_path)

    def new_robot_config_path_dialog(self, text):
        return input(text)

    def no_connection_type_warning(self, text):
        print(text)

    def no_connection_address_warning(self, text):
        print(text)

    def start(self):
        BaseFramework.start(self)
        params = None

        def perform_params(cond):
            nonlocal params
            if type(cond) == type:
                return type(params) == cond
            elif type(cond) == list:
                return params in cond
            else:
                return params == cond

        while 1:
            command_str = input("================================\nInsert command\n")
            if command_str.find(" ") != -1:
                command, params = command_str.split(" ")
            else:
                command = command_str
            if command == "communication_type":
                if params in ['wired', 'wireless']:
                    self.controller.set_connection_type(params)
                else:
                    print("Unknown param")
            elif command == "test":
                self.controller.set_connection_type("communication_type wired")
            elif command == "connect":
                self.controller.connect_to_robot()
            elif command == "state":
                model = self.model
                print("Robot config path: {config_path}\n"
                      "Connection type: {conn_type}\n"
                      "Connection address: {conn_address}"
                      "".format(config_path=model.config["robot_config_path"], conn_type=model.connection_type,
                                conn_address=model.connection_address))
            elif command == "set_comm_type":
                if perform_params(str):
                    self.controller.set_connection_type(params)



            else:
                print("Unknown command")

    def update(self):
        pass


if __name__ == "__main__":
    c = Console("/home/laptop/work/powerpoof/powerpoof_qt/config.yaml")
    c.start()
