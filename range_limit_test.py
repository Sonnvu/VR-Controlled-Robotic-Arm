import sys
sys.path.append("/home/seniord/ECE_1896/xarm_case_a/serial_bus_servo_controller_python_module/scripts")

import serial_bus_servo_controller as sbsc
import time
controller = sbsc.SBS_Controller("/dev/ttyS0")

servo_id = 5

position = 200
controller.cmd_servo_move([servo_id], [position], 3000)
time.sleep(4)

p_val = controller.cmd_mult_servo_pos_read([servo_id])
print("Servo " + str(servo_id) + " position: " + str(p_val))
