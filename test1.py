import sys
sys.path.append("/home/seniord/ECE_1896/xarm_case_a/serial_bus_servo_controller_python_module/scripts")

import serial_bus_servo_controller as sbsc
import time
controller = sbsc.SBS_Controller("/dev/ttyS0")

# This is an example of rotating servos with IDs 1 and 2 to positions 100 and 400, respectively, in 500ms.

servo = 1

controller.cmd_servo_move([servo], [200], 2000)

time.sleep(3)
p_val = controller.cmd_mult_servo_pos_read([servo])
print("Servo " + str(servo) + " position: " + str(p_val))
