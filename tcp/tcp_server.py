import socket 
import subprocess
import json
import time
import signal
import sys
import numpy as np
sys.path.append("/home/seniord/ECE_1896/xarm_case_a/serial_bus_servo_controller_python_module/scripts")

import serial_bus_servo_controller as sbsc
import time
controller = sbsc.SBS_Controller("/dev/ttyS0")
prev_pose = None

def log(message):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    full_message = f"{timestamp} {message}\n"
    print(f"{timestamp} {message}")
    
    try:
        with open("server.log", "a") as f:
            f.write(full_message)
    except Exception as e:
        print(f"Failed to write to server.log: {e}")

    if log_socket:
        try:
            log_socket.sendall(full_message.encode())
        except Exception as e:
            print(f"Failed to send log to EC2: {e}")
            
def graceful_shutdown(signum, frame):
	log("Shutting down server due to system signal...")
	if server_socket:
		server_socket.close()
	sys.exit(0)

# Catch system shutdown
signal.signal(signal.SIGTERM, graceful_shutdown)
signal.signal(signal.SIGINT, graceful_shutdown)  # Optional: Ctrl+C too

def interpolate_and_move(arm, prev_pose, new_pose, steps=10, total_duration=2.0):
        """
        Smoothly interpolate from prev_pose to new_pose
        :param prev_pose: (x, y, z, phi)
        :param new_pose: (x, y, z, phi)
        :param steps: Number of interpolation steps
        :param total_duration: Total time in seconds to finish interpolation
        :return: new_pose
        """
        if prev_pose is None:
            # First move, no interpolation needed
            arm.move_end_effector(*new_pose, t=int(total_duration * 1000))
            return new_pose

        prev_x, prev_y, prev_z, prev_phi = prev_pose
        new_x, new_y, new_z, new_phi = new_pose

        step_duration = total_duration / steps

        for i in range(1, steps + 1):
            ratio = i / steps
            interp_x = prev_x + (new_x - prev_x) * ratio
            interp_y = prev_y + (new_y - prev_y) * ratio
            interp_z = prev_z + (new_z - prev_z) * ratio
            interp_phi = prev_phi + (new_phi - prev_phi) * ratio
        
            log_msg = f"Interpolate Position step [{i}]: {interp_x} {interp_y} {interp_z} | Duration: {int(step_duration*1000)}"
            log(log_msg)
            print(log_msg)

            # Send interpolated pose to the arm
            arm.move_end_effector(interp_x, interp_y, interp_z, interp_phi, int(step_duration * 1000))
            time.sleep(step_duration)  # Optional: allow the arm to catch up

        return new_pose

# AWS EC2 details
EC2_HOST = "ec2-18-218-93-102.us-east-2.compute.amazonaws.com"
HOST = '0.0.0.0'
PORT = 65432
LOG_REMOTE_PORT = 5000
LOG_LOCAL_PORT = 5000
log_socket = None

log("TCP Server Application Started")

#************************ TCP Server Section ************************#
# Create log socket
log_socket = None
for attempt in range(5):
    try:
        log_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        log_socket.connect((EC2_HOST, LOG_LOCAL_PORT))
        log(f"Connection to remote log stream on: {HOST}:{LOG_REMOTE_PORT}")
        break
    except Exception as e:
        log(f"Attempt {attempt + 1}: Failed to connect to log stream: {e}")
        time.sleep(2)  # Wait and retry
else:
    log_socket = None
    log("Could not connect to log stream after retries.")
    
# ~ # Creating main server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(5)    
log(f"TCP Server listening on {HOST}:{PORT}...")

MAX_REACH = 29.5
def scale_to_reach(x, y, z, max_reach):
	distance = np.sqrt(x**2 + y**2 + z**2)
	if distance > max_reach:
		scale = max_reach / distance
		x *= scale 
		y *= scale 
		z *= scale
	return x, y, z

# Main Server Loop
try:
	while True:
		client_socket, client_address = server_socket.accept()
		log(f"CONNECTION ESTABLISHED: {client_address}")
		
		# Receive data
		data = client_socket.recv(1024).decode('utf-8')
		try:
			data_dict = json.loads(data)
			x = data_dict["x"]
			z = data_dict["y"]
			y = data_dict["z"]
			# ~ phi = data_dict["phi"]
			wrist = data_dict["wrist"]
			grip = data_dict["grip"]
			gas_x = data_dict["gas (x)"]
			gas_y = data_dict["gas (y)"]
			
			# Y scaling
			z = z - 9
			if grip > 1000:
				grip = 1000
			
			# ~ steer = data_dict["steering"]
			
			# ~ x, y, z = scale_to_reach(x, y, z, MAX_REACH)
			
			log(f"Received: x = {x}, y = {y}, z = {z}, wrist = {wrist}, grip = {grip}, gas_x = {gas_x}, gas_y = {gas_y}")
			
			try:
				# Option 1: No Interpolation + Default Execution Time
				grip = int(grip)
				controller.move_end_effector(x, y, z, 0, wrist, grip, 900)
				
				# Option 2: Interpolation Test
				# ~ prev_pose = interpolate_and_move(controller, prev_pose, (x, y, z, phi), steps=10, total_duration=1.0)
			except ValueError as e:
				log(f"ValueError during move_end_effector: {e}")
				response = f"Error: {e}"
				continue
			except Exception as e:
				
				log(f"Unexpected error during move_end_effector: {e}")
				response = f"Error: {e}"
				continue 
			else:
				response = f"Received: x = {x}, y = {y}, z = {z}"
			
			client_socket.sendall(response.encode('utf-8'))
		except json.JSONDecodeError:
			response = "Invalid JSON format received"
		finally:
			client_socket.close()
except KeyboardInterrupt:
	log("Shutting down server...")
	server_socket.close()
	


