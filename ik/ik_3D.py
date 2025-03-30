import sys
sys.path.append("/home/seniord/ECE_1896/xarm_case_a/serial_bus_servo_controller_python_module/scripts")
import numpy as np

import serial_bus_servo_controller as sbsc
import time
controller = sbsc.SBS_Controller("/dev/ttyS0")

L1, L2, L3 = 4, 4 , 3

def move_end_effector(controller, x3, y3, z3, p):
	# Length of arm segments in cm
	l1 = 10
	l2 = 9.6
	l3 = 10.2
	
	phi = np.deg2rad(p)
	#Calculate the horizontal distance to the targeton XY plane
	r3 = np.sqrt(x3**2 + y3**2)
	
	# Calculate theta_base 
	theta_base = np.arctan2(y3, x3)
	
	# Get r2 and z2
	r2 = r3 - l3*np.cos(phi)
	z2 = z3 - l3*np.sin(phi)
	
	max_reach = l1 + l2
	current_distance = np.sqrt(r2**2 + z2**2)
	
	if current_distance > max_reach:
		scale_factor = max_reach / current_distance
		r2 *= scale_factor
		z2 *= scale_factor
		print(f"Target out of reach. Moving to closest reachable point: ({r2:.2f}, {z2:.2f})")
	
	c2 = (r2**2 + z2**2 - l1**2 - l2**2)/(2*l1*l2)
	s2 = -np.sqrt(1-c2**2)
	theta_2 = np.arctan2(s2, c2)
	
	s1 = ((l1 + l2*c2)*z2 - l2*s2*r2)/(r2**2 + z2**2)
	c1 = ((l1 + l2*c2)*r2 + l2*s2*z2)/(r2**2 + z2**2)
	theta_1 = np.arctan2(s1, c1)
	
	theta_3 = phi - theta_1 - theta_2
	
	print('theta_base: ', np.rad2deg(theta_base))
	print('theta_1: ', np.rad2deg(theta_1))
	print('theta_2: ', np.rad2deg(theta_2))
	print('theta_3: ', np.rad2deg(theta_3)) 
	
	
	controller.cmd_move_with_angle(np.rad2deg(theta_base), np.rad2deg(theta_1), np.rad2deg(theta_2), np.rad2deg(theta_3), 3000)
	
x, y, z, p = map(float, input("Enter x, y, z and phi angle: ").split())
print(f"x = {x}, y = {y}, z = {z}, phi = {p}")  
move_end_effector(controller, x, y, z, p)
