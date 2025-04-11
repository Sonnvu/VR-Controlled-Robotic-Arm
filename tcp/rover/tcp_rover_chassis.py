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
    log(f"CONNECTION ESTABLISHED: {address}")
    try:
        data = client_socket.recv(1024).decode('utf-8')
        data_dict = json.loads(data)

        # Extract relevant rover data
        steering = data_dict["steering"]
        gas = data_dict["gas"]
        brake = data_dict["break"]
        
        log(f"Received Rover Data: steering={steering}, gas={gas}, brake={brake}")

        # TODO: Implement rover control logic here

        response = f"Rover input received: steering={steering}, gas={gas}, brake={brake}"
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
