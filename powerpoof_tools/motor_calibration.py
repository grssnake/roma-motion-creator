from powerpoof_tools.base_tool import ChildModel, ChildController, View
from powerpoof_tools.base_tool import update_view


class MotorCalibratorModel(ChildModel):
    def __init__(self):
        ChildModel.__init__(self)
        self.offsets = dict()
        self.positions = dict()


class MotorCalibratorController(ChildController):
    def __init__(self, base, model=MotorCalibratorModel()):
        ChildController.__init__(self, model, base)
        for id, m in self.root_base.model.robot_config.items():
            self.model.offsets[id] = m["offset"]
            self.model.positions[id] = 0

    @update_view
    def on_connect(self):
        for id, m in self.root_base.model.robot_config.items():
            # self.model.offsets[id] = self.root_base.robot.get_motor_config_info(id).offset
            info = self.root_base.robot.get_motor_info(id)
            self.model.offsets[id] = info.offset
            #self.model.positions[id] = info.position

    def update_config(self):
        if self.view.update_config_confirm_dialog("Confirm robot configuration change."):
            self.root_base.robot.update_config_by_motors()
            self.root_base.robot.save_config()

    @update_view
    def change_motor_position(self, id, pos):
        if not self.root_base.model.safe_mode:
            self.model.positions[id]=pos
            self.root_base.robot.go(id, pos, 1, notify=False)

    @update_view
    def change_motor_offset(self, id, offset):
        if not self.root_base.model.safe_mode:
            self.model.offsets[id] = offset
            self.root_base.robot.comm.send_and_wait("motor", params="set offset {} {}".format(id, offset))
            self.root_base.robot.comm.send_and_wait("zero_offset", params="{}".format(id))

    def to_zero_position_all(self):
        self.root_base.robot.to_zero_position()


class MotorCalibratorView(View):
    def __init__(self, base):
        View.__init__(self, controller=MotorCalibratorController(base))

    def update_config_confirm_dialog(self):
        pass
