from time import sleep
from powerpoof_control.communication import Communicator
import json, os
import time
from collections import namedtuple

ConfigMotor = namedtuple("ConfigMotor", "id, start, reversed, offset, min, max, pin")
MotorInfo = namedtuple("MotorInfo", "id, position, offset")


class RobotCommander(object):
    MOTOR_COUNT = 19
    MODE_WIRED = 0
    MODE_WIRELESS = 1

    STATUS_FINISHED = 100
    STATUS_INVALID_CONFIG_CRC = 3

    MODE_SAFE = 0
    MODE_FULL = 1

    __modes_text = {"safe": MODE_SAFE, "full": MODE_FULL}

    def __init__(self, config, func=None, path="/dev/ttyUSB0", baudrate=57600, auto_start=False, mode=MODE_WIRED):
        self.func = func
        self.comm = None
        self.config = config
        self.mode = self.MODE_SAFE
        self.start(path, baudrate)

        self.registered_callbacks = dict()
        self.config = None
        if auto_start:
            self.execute()

    def ask_current_mode(self):
        return RobotCommander.__modes_text[self.comm.wait_for_reply("mode", params="get")]

    def go_to_full_mode(self):
        self.comm.send_and_check_reply("mode", "ok", params="set full")

    def go_to_safe_mode(self):
        self.comm.send_and_check_reply("mode", "ok", params="set safe")

    def close(self):
        self.comm.close()

    def dispatch(self):
        type, message = self.comm.wait_for_line()
        if type in self.registered_callbacks:
            self.registered_callbacks[type](message)

    def register_callback(self, message_type, callback):
        self.registered_callbacks[message_type] = callback

    def move(self, what, where, time):
        self.comm.send_request("move", params="{} {} {}".format(what, where, time))

    def go(self, what, where, time, notify=True):
        self.comm.send_request("go", params="{} {} {}".format(what, where, time, int(notify)))
        if notify:
            return self.comm.wait_reply(headers="move")

    def commit(self, notify=True):
        self.comm.send_request("commit", params="{}".format(int(notify)))
        if notify:
            return self.comm.wait_reply(headers="move")

    def execute(self):
        pass

    def get_config(self):
        if self.config is None:
            path = os.path.realpath(os.path.join(__file__, "..", "..", "..", "config.json"))
            with open(path, "r") as f:
                self.config = json.load(f)
        return self.config

    def start(self, path, baudrate):
        self.comm = Communicator(path, baudrate=baudrate)
        time.sleep(2)
        self.comm.send_and_check_reply("knock", "who's there")

    def fetch_config(self):
        motor_fields = "start motor_offset reversed motor_min motor_max motor_pin_map".split(" ")
        fetched = dict()
        for i in range(self.MOTOR_COUNT):
            id, start, reversed, offset, min, max, pin = self.comm.wait_for_reply("config",
                                                                                  params="get motor {}".format(
                                                                                      i)).split(" ")
            fetched[id] = {"start": start, "reversed": reversed, "offset": offset, "min": min, "max": max, "pin": pin}
        return fetched

    def check_state(self):
        state = self.comm.wait_for_reply("init_state")
        if state == "finished":
            return self.STATUS_FINISHED
        else:
            return int(state)

    def upload_config(self, config, save_in_storage=True):
        motor_fields = "start offset reversed min max pin".split(" ")
        d = [m for m in config["motors"]]
        for k, v in {m["id"]: m for m in config["motors"]}.items():
            for f in motor_fields:
                ss = (k, f, v[f])
                self.comm.send_and_check_reply("config", params="set motor {} {} {}".format(k, f, v[f]),
                                               data_to_check="ok")

        if save_in_storage:
            changed = self.comm.wait_for_reply("config", params="save")
            changed = self.comm.wait_for_reply("config", params="fix")
            changed = changed

    def get_motor_config_info(self, motor_id):
        result = self.comm.wait_for_reply("config", params="get motor {}".format(motor_id))
        if result.endswith(" ok"):
            msg = [int(f) for f in result.split(" ok")[0].split(" ")]
        return ConfigMotor(*msg)

    def get_motor_info(self, id):
        result = self.comm.wait_for_reply("motor", params="get {}".format(id))
        if result.endswith(" ok"):
            msg = [int(f) for f in result.split(" ok")[0].split(" ")]
        return MotorInfo(*msg)

    def save_config(self):
        changed = self.comm.wait_for_reply("config", params="save")

    def update_config_by_motors(self):
        result = self.comm.send_and_wait("config", params="from_motors offset")

    def to_zero_position(self):
        result = self.comm.send_and_wait("zero_offset", params="all")
        result = result

    def run(self):
        sleep(1)
        print('hi there')
        self.comm.send("hello")
        self.comm.wait_for("hi")
        print("done greeting")
        if self.func is not None:
            self.func(self)
        else:
            self.execute()
