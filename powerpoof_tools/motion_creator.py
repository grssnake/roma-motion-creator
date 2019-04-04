import os
import time
import csv
from threading import Thread
from base_tool import *
import json
from collections import namedtuple

Motor = namedtuple("Motor", "bound, position")


class Step(object):
    def __init__(self, motors=None, delay=500):
        self.motors = motors
        self.delay = delay


class MotionCreatorModel(ChildModel):
    def __init__(self):
        Model.__init__(self)
        self.steps = list()
        self.current_step = None
        self.step_to_copy = None
        self.real_time_control = False
        self.stop_thread = False
        self.in_cycle = False
        self.cycle_running = False
        self.base = None
        self.save_path = None
        self.connected_motors = list()

    def get_current_step(self):
        return self.steps[self.steps.index(self.current_step)]

    def set_current_step(self, step):
        self.steps[self.steps.index(self.current_step)] = step
        self.current_step = step


class MotionCreatorController(ChildController):
    def __init__(self, base, model=MotionCreatorModel()):
        """
        :param model:
        :type model: MotionCreatorModel
        :type base: BaseController
        """
        ChildController.__init__(self, model, base)

    def start(self):
        self.add_step()

    def update_view(f):
        def decorate(self, *args, **kwargs):
            ret = f(self, *args, **kwargs)
            if self.view:
                self.view.update()
            return ret

        return decorate

    @update_view
    def set_step(self, step):
        if type(step) == int:
            if 0 <= step < len(self.model.steps):
                self.model.current_step = self.model.steps[step]
        elif type(step) == Step:
            self.model.current_step = step
        if self.model.real_time_control:
            self.execute_step(self.model.current_step)
        self.model.connected_motors=list()

    def _get_default_step(self):
        return Step(motors={m["id"]: int(m["start"]) for id, m in self.base.model.robot_config.items()})

    @update_view
    def add_step(self):
        step_to_set = -1
        if not self.model.steps:
            s = self._get_default_step()
            self.model.steps.append(s)
        else:
            if self.model.steps.index(self.model.current_step) == len(self.model.steps) - 1:
                self.model.steps.append(Step(motors=self.model.steps[-1].motors.copy()))
            else:
                current_step_index = self.model.steps.index(self.model.current_step)
                new_step = Step(motors=self.model.steps[current_step_index].motors.copy())
                new_steps = self.model.steps[:current_step_index] + [new_step] + self.model.steps[current_step_index:]
                self.model.steps = new_steps
                step_to_set = current_step_index + 1
        self.set_step(self.model.steps[step_to_set])

    def remove_step(self):
        if len(self.model.steps) > 1:
            index = self.model.steps.index(self.model.current_step)
            self.model.steps.remove(self.model.current_step)
            if index == len(self.model.steps):
                index -= 1
            self.set_step(index)

    @update_view
    def change_motor_state(self, motor_index, value):
        base = self.root_base
        m1=motor_index
        m2=None
        for b in self.model.connected_motors:
            if len(b)>1 and motor_index in b:
                m1, m2=b
        self.model.current_step.motors[m1] = value
        if m2:
            self.model.current_step.motors[m2] = value
        if self.model.real_time_control:
            base.robot.move(m1, value, 1)
            if m2:
                base.robot.move(m2, value, 1)
            base.robot.commit(notify=False)

    def change_step_delay(self, delay):
        self.model.current_step.delay = delay

    @update_view
    def set_motors_connected(self, id, state):
        for b in self.root_base.model.motor_pairs:
            if len(b) > 1:
                if id in b:
                    if state:
                        self.model.connected_motors.append(b)
                    else:
                        self.model.connected_motors.remove(b)

    @update_view
    def copy_step(self):
        current_step = self.model.current_step
        self.model.step_to_copy = Step(motors=current_step.motors.copy(), delay=current_step.delay)

    @update_view
    def paste_step(self):
        if self.model.step_to_copy:
            self.model.set_current_step(self.model.step_to_copy)
            self.model.step_to_copy = None

    @update_view
    def step_to_default(self):
        self.model.set_current_step(self._get_default_step())
        self.execute_step(self.model.current_step)

    def execute_step(self, step, wait=False):
        for id, m in step.motors.items():
            self.root_base.robot.move(id, m, step.delay)
        self.root_base.robot.commit(notify=wait)
        # if wait:
        # message = self.base.robot.comm.wait_for_reply("move_all")

    def execute_all_steps(self):
        for step in self.model.steps:
            self.execute_step(step, wait=True)

    @update_view
    def set_in_cycle(self, state):
        self.model.in_cycle = state

    def start_execution_thread(self):
        thread = Thread(target=self.execution_thread)
        self.model.stop_thread = False
        thread.start()

    def stop_execution_thread(self):
        self.model.stop_thread = True

    def execution_thread(self):
        self.model.cycle_running = True
        while not self.model.stop_thread:
            self.execute_all_steps()
        self.model.cycle_running = False

    def start_execution(self):
        if self.model.in_cycle:
            self.start_execution_thread()
        else:
            self.execute_all_steps()

    def set_control_in_real_time(self, value):
        self.model.real_time_control = value
        if value:
            self.execute_step(self.model.current_step)

    def save_steps_to_file(self, path):
        with open(path, "w") as f:
            fieldnames = [str(k) for k, v in self.base.model.robot_config.items()] + ['delay']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            fields = dict()
            for step in self.model.steps:
                # for i in range(int(self.base.model.robot_config["motor_count"])):
                for k, v in step.motors.items():
                    fields[str(k)] = v
                fields["delay"] = step.delay
                writer.writerow(fields)

    def save_steps(self):
        path = self.view.save_steps_dialog()
        self.model.save_path = path
        self.save_steps_to_file(path)

    def load_steps_from_file(self, path):
        self.model.steps = list()
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            self.root_base.model.robot_config
            for row in reader:
                motors = {id: int(row[str(id)]) for id, m in self.base.model.robot_config.items()}
                self.model.steps.append(Step(motors=motors, delay=int(row["delay"])))
            self.set_step(0)

    def load_steps(self):
        path = self.view.load_steps_dialog()
        self.load_steps_from_file(path)

    def set_robot_config_path(self, path):
        self.model.set_communicator_path(path)

    def check_robot_config(self):
        """
        :param get_path_dialog_function: "function that implements robot configuration file  path selection"
        :param save_new_path_dialog_function: "function that implements dialog for saving new configuration path"
        :type get_path_dialog_function: function
        :type save_new_path_dialog_function: function
        :return: "path to new robot configuration file"
        :rtype: bool
        """

        def check(path):
            if path:
                if os.path.exists(path) and os.path.isfile(path):
                    return True
            return False

        path = self.model.config.get("robot_config_path")
        valid = check(path)
        if not valid:
            while not check(path):
                path = self.view.call_path_dialog(self.model.localization["config_file_not_found"])

        if not valid:
            self.model.config["robot_config_path"] = path
            to_save = self.view.new_config_path_dialog(self.model.localization["save_new_config"])
            if to_save:
                self.save_config()

    def check_robot_serial_path(self):
        path = self.model.config.get("serial_path")
        if path is None:
            while path is None:
                path = self.view.input_serial_path_dialog(self.model.localization["input_serial_path"])
            self.model.config["serial_path"] = path
            to_save = self.view.new_config_path_dialog(self.model.localization["save_new_config"])
            if to_save:
                self.save_config()


class MotionCreatorView(View):
    def __init__(self, base, **kwargs):
        View.__init__(self, controller=MotionCreatorController(base))


class MotionCreatorView2(View):
    def __init__(self, model=None, controller=None):
        """
        :param controller:
        :type controller: MotionCreatorController
        """
        View.__init__(self, controller=controller)

    def update(self):
        pass

    def change_step(self, step_index):
        self.controller.set_step(step_index)

    def add_step(self):
        self.controller.add_step()

    def save_steps_dialog(self):
        pass

    def load_steps_dialog(self):
        pass
