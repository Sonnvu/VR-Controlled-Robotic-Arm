import sys
sys.path.append("/home/seniord/ECE_1896/xarm_case_a/serial_bus_servo_controller_python_module/scripts")

import serial_bus_servo_controller as sbsc
import time
import subprocess
import serial
from flask import Flask, request, jsonify

# Initialize Flask app
app = Flask(__name__)

# Initialize Ngrok
def ngrok_init():
	# Run Ngrok in the background and forward port 5000
	process = subprocess.Popen(["ngrok", "http", "--url=gelding-flying-stud.ngrok-free.app", "5000"])
	time.sleep(5)
	print("Ngrok started successfully")
	
# Initialize Ngrok servo controller
ngrok_init()
controller = sbsc.SBS_Controller("/dev/ttyS0")
	
@app.route('/move', methods=['POST'])
def move():
	try:
		data = request.json
		servo_ids = data["servo_id"]
		positions = data["position"]
		duration = int(data.get("duration", 2000))
		
		controller.cmd_servo_move(servo_ids, positions, duration)
		
		return jsonify({"status": "success", "message": f"Servos {servo_ids} moved to {positions} in {duration}ms"})
	except Exception as e:
		return jsonify({"error": str(e)}), 500
		
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)
