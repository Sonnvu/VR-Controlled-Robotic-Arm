import RPi.GPIO as GPIO
import time
import threading

# Define GPIO pins for the stepper motors
step_pins_SW = [14, 15, 18, 23]  # Stepper motor SE
step_pins_NW = [24, 25, 8, 7]    # Stepper motor SW
step_pins_SE = [20, 16, 12, 1]
step_pins_NE = [2, 3, 4, 17]     # Stepper motor NW
step_pins_turn = [27, 22, 10, 9] # Stepper motor for turning

# Set up the GPIO mode
GPIO.setmode(GPIO.BCM)
for pin_set in [step_pins_SE, step_pins_SW, step_pins_NE, step_pins_NW, step_pins_turn]:
    for pin in pin_set:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

# Stepper motor step sequence (for forward rotation)
step_sequence_forward = [
    [1, 0, 0, 1],
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1]
]

# Stepper motor step sequence (for backward rotation)
step_sequence_backward = [
    [0, 0, 0, 1],
    [0, 0, 1, 1],
    [0, 0, 1, 0],
    [0, 1, 1, 0],
    [0, 1, 0, 0],
    [1, 1, 0, 0],
    [1, 0, 0, 0],
    [1, 0, 0, 1]
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
def rotate_motor(step_pins, direction):
    step_sequence = step_sequence_forward if direction == "forward" else step_sequence_backward
    while motor_running or turn_motor_running:
        for step in range(512):  # Adjust steps as needed for one full revolution
            if not motor_running and not turn_motor_running:
                break
            for pin_index in range(4):
                GPIO.output(step_pins[pin_index], step_sequence[step % 8][pin_index])
            time.sleep(0.001)  # Adjust the delay to control speed

# Function to start rotating the motors
def start_motor(pin_set, direction):
    global motor_running, turn_motor_running
    if pin_set == step_pins_turn:
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
    for pin_set in [step_pins_SE, step_pins_SW, step_pins_NE, step_pins_NW, step_pins_turn]:
        for pin in pin_set:
            GPIO.output(pin, GPIO.LOW)

################################### Start of server script #####################################


import socket
import json
import time
import threading

HOST = '0.0.0.0'
PORT = 65432  # Dedicated port for rover

def log(message):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    full_message = f"{timestamp} {message}"
    print(full_message)
    with open("rover_server.log", "a") as f:
        f.write(full_message + "\n")

def handle_client(client_socket, address):
    global motor_running, motor_direction, turn_motor_direction, turn_motor_running
    log(f"CONNECTION ESTABLISHED: {address}")
    try:
        data = client_socket.recv(1024).decode('utf-8')
        data_dict = json.loads(data)

        # Extract relevant rover data
        user_input = data_dict["input"]
        
        log(f"Received Rover Data: user_input={user_input}")

        # TODO: Implement rover control logic here
        if user_input == "1":
            print("User input is 1")
            if motor_running and motor_direction == "forward":
                print("Stopping motor rotation forward.")
                stop_motor()
            else:
                print("Starting motor rotation forward.")
                motor_direction = "forward"
                # Start all motors simultaneously in forward direction
                start_motor(step_pins_SE, motor_direction)
                start_motor(step_pins_SW, motor_direction)
                start_motor(step_pins_NE, motor_direction)
                start_motor(step_pins_NW, motor_direction)

        elif user_input == "-1":
            if motor_running and motor_direction == "backward":
                print("Stopping motor rotation backward.")
                stop_motor()
            else:
                print("Starting motor rotation backward.")
                motor_direction = "backward"
                # Start all motors simultaneously in backward direction
                start_motor(step_pins_SE, motor_direction)
                start_motor(step_pins_SW, motor_direction)
                start_motor(step_pins_NE, motor_direction)
                start_motor(step_pins_NW, motor_direction)

        elif user_input == "2":
            if turn_motor_running and turn_motor_direction == "forward":
                print("Stopping turn motor rotation forward.")
                turn_motor_running = False
                # Wait for the motor thread to stop
                if turn_motor_thread is not None:
                    turn_motor_thread.join()
                # Stop the turn motor
                for pin in step_pins_turn:
                    GPIO.output(pin, GPIO.LOW)
            else:
                print("Starting turn motor rotation forward.")
                turn_motor_direction = "forward"
                start_motor(step_pins_turn, "forward")

        elif user_input == "3":
            if turn_motor_running and turn_motor_direction == "backward":
                print("Stopping turn motor rotation backward.")
                turn_motor_running = False
                # Wait for the motor thread to stop
                if turn_motor_thread is not None:
                    turn_motor_thread.join()
                # Stop the turn motor
                for pin in step_pins_turn:
                    GPIO.output(pin, GPIO.LOW)
            else:
                print("Starting turn motor rotation backward.")
                turn_motor_direction = "backward"
                start_motor(step_pins_turn, "backward")


        response = f"Received Rover Data: user_input={user_input}"
        client_socket.sendall(response.encode('utf-8'))

    except json.JSONDecodeError:
        log("Invalid JSON format received.")
        client_socket.sendall(b"Invalid JSON format")
    except Exception as e:
        log(f"Error: {e}")
        client_socket.sendall(f"Server error: {e}".encode('utf-8'))
    finally:
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


