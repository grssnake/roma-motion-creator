# -*- coding: utf-8 -*-

import sys, os
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

# ...

data_folder = os.path.join(sys.path[0], "data")

stream = open(os.path.join(data_folder, "motor_names.yaml"), 'r').read()
motor_names = load(stream, Loader=Loader)


stream = open(os.path.join(data_folder, "default_robot_config.yaml", ), 'r', encoding="cp1251").read()
motor_config = load(stream, Loader=Loader)

# print(data)

# ...

for motor in zip(motor_config["motors"], motor_names):


    #print(motor)
    print("Сервопривод #{}: {}".format(motor[1]['id'], motor[1]['names']["russian"].encode("windows-1251").decode()))
    print("Углы: min {}° max {}°\n".format(motor[0]['min'], motor[0]['max']))

exit()

output = dump(motor_config["motors"], Dumper=Dumper)
print(output)

output = dump(motor_names, Dumper=Dumper)
print(output)