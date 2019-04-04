from powerpoof_tools.base_tool import ChildModel, ChildController, View
from powerpoof_tools.base_tool import update_view


class MotorSchemeModel(ChildModel):
    def __init__(self):
        ChildModel.__init__(self)
        pass


class MotorSchemeController(ChildController):
    def __init__(self, base, model=MotorSchemeModel()):
        ChildController.__init__(self, model, base)


class MotorSchemeView(View):
    def __init__(self, base):
        View.__init__(self, controller=MotorSchemeController(base))


class MotorScheme(MotorSchemeView):
    pass
