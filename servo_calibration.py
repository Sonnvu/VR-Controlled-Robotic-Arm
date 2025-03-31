import sys
sys.path.append("/home/seniord/ECE_1896/xarm_case_a/serial_bus_servo_controller_python_module/scripts")

import serial_bus_servo_controller as sbsc
import time
controller = sbsc.SBS_Controller("/dev/ttyS0")

controller.cmd_move_with_angle(-90, 0, 0, 0, 0, 0, 1000)

time.sleep(3)

