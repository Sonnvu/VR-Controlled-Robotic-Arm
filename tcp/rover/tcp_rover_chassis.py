import RPi.GPIO as GPIO
import time
import threading

# Define GPIO pins for the stepper motors
# step_pins_SW = [13, 19, 18, 23]  # Stepper motor SE
# step_pins_NW = [24, 25, 8, 7]    # Stepper motor SW
# step_pins_SE = [20, 16, 12, 1]
# step_pins_NE = [2, 3, 4, 17]     # Stepper motor NW
# step_pins_turn = [27, 22, 10, 9] # Stepper motor for turning

#Defining new GPIO pins
wheel_pins = [24, 25] # 24 is the select (1 is forward, 0 is backward), 25 is the clock. (must make square wave with the clock for motion)
steer_pins = [8, 7] # 8 is the select (1 is right, 0 is left), 7 is the clock. 

# Set up the GPIO mode
GPIO.setmode(GPIO.BCM)
for pin_set in [wheel_pins, steer_pins]:
    for pin in pin_set:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

# Stepper motor step sequence (for forward rotation)
step_sequence_forward = [
    [1, 0],
    [1, 1],
    [1, 0],
    [1, 1],
    [1, 0],
    [1, 1],
    [1, 0],
    [1, 1]
]

# Stepper motor step sequence (for backward rotation)
step_sequence_backward = [
    [0, 0],
    [0, 1],
    [0, 0],
    [0, 1],
    [0, 0],
    [0, 1],
    [0, 0],
    [0, 1]
]

# Variable to control motor state and direction
motor_running = False
motor_direction = "forward"  # Initial direction is forward
motor_thread = None

# Variable to control turning motor state and direction
turn_motor_running = False
turn_motor_direction = "forward"  # Initial direction for turning motor
turn_motor_thread = None

# Function to make the stepper motors rotate (forward or backward)
def rotate_motor(pins, direction):
    step_sequence = step_sequence_forward if direction == "forward" else step_sequence_backward
    if pins == steer_pins:
        for step in range(100):  # Adjust steps as needed for one full revolution
            for pin_index in range(2): # was 4
                GPIO.output(pins[pin_index], step_sequence[step % 8][pin_index])
            time.sleep(0.001)  # Adjust the delay to control speed
    else:
        while motor_running:
            for step in range(512):  # Adjust steps as needed for one full revolution
                if not motor_running:
                    break
                for pin_index in range(2): # was 4
                    GPIO.output(pins[pin_index], step_sequence[step % 8][pin_index])
                time.sleep(0.001)  # Adjust the delay to control speed

# Function to start rotating the motors
def start_motor(pin_set, direction):
    global motor_running, turn_motor_running
    if pin_set == steer_pins:
        turn_motor_running = True
    else:
        motor_running = True
    motor_thread = threading.Thread(target=rotate_motor, args=(pin_set, direction))
    motor_thread.start()
    return motor_thread

# Function to stop all motors
def stop_motor():
    global motor_running, turn_motor_running
    motor_running = False
    turn_motor_running = False
    for pin_set in [wheel_pins, steer_pins]:
        for pin in pin_set:
            GPIO.output(pin, GPIO.LOW)

################################### Start of server script #####################################


import socket
import json
import time
import threading

HOST = '0.0.0.0'
PORT = 65433  # Dedicated port for rover

def log(message):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    full_message = f"{timestamp} {message}"
    print(full_message)
    with open("rover_server.log", "a") as f:
        f.write(full_message + "\n")

def handle_client(client_socket, address):
    global motor_running, motor_direction, turn_motor_direction, turn_motor_running
    log(f"CONNECTION ESTABLISHED: {address}")
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break # client disconnected
            data_dict = json.loads(data)

            # Extract relevant rover data
            gas_x = data_dict["gas (x)"]
            gas_y = data_dict["gas (y)"]
            
            log(f"Received Rover Data: gas_x = {gas_x}, gas_y = {gas_y}")
            
            # Parsing x
            if gas_x > 0:
                gas_x = 1
            elif gas_x < 0:
                gas_x = -1
            else:
                gas_x = 0
                
            # Parsing y
            if gas_y > 0:
                gas_y = 1
            elif gas_y < 0:
                gas_y = -1
            else:
                gas_y = 0


            # TODO: Implement rover control logic here
            if gas_y == 1:
                print("Starting motor rotation forward.")
                motor_direction = "forward"
                # Start all motors simultaneously in forward direction
                start_motor(wheel_pins, motor_direction)

            elif gas_y == -1:
                print("Starting motor rotation backward.")
                motor_direction = "backward"
                # Start all motors simultaneously in backward direction
                start_motor(wheel_pins, motor_direction)
                
            elif gas_y == 0 and gas_x == 0:
                print("Stopping motor rotation.")
                stop_motor()

            elif gas_x == "1":
                print("Starting turn motor rotation right.")
                turn_motor_direction = "forward"
                start_motor(steer_pins, "forward")

            elif gas_x == "-1":
                print("Starting turn motor rotation left.")
                turn_motor_direction = "backward"
                start_motor(steer_pins, "backward")

            response = f"Received Rover Data: gas_x = {gas_x}, gas_y = {gas_y}"
            client_socket.sendall(response.encode('utf-8'))

        except json.JSONDecodeError:
            log("Invalid JSON format received.")
            client_socket.sendall(b"Invalid JSON format")
        except ConnectionResetError:
            log(f"Connection reset by client: {address}")
            break
        except Exception as e:
            log(f"Error: {e}")
            break
            
    log(f"Client {address} disconnected.")
    client_socket.close()

def start_rover_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    log(f"Rover TCP Server listening on {HOST}:{PORT}...")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.start()
    except KeyboardInterrupt:
        log("Shutting down Rover TCP server...")
        server_socket.close()

if __name__ == "__main__":
    start_rover_server()


