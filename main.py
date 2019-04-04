import sys, os
sys.path.append(os.path.join(sys.path[0], "powerpoof_tools"))
sys.path.append(os.path.join(sys.path[-1], "powerpoof_control"))
from motion_creator import MotionCreatorApp
from base_tool_qt import BaseViewQT



from PyQt5.QtWidgets import QApplication

if __name__ == "__main2__":
    app = MotionCreatorApp(sys.argv)
    exit(app.exec_())


