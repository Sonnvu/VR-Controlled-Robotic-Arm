# network_config.py
import socket
import subprocess
import time
import threading
import sys

# Example SSH command that you'll pass into the function
SSH_KEY = "/home/seniord/ECE_1896/xarm_case_a/tcp/public_key.pem"
EC2_USER = "ec2-user"
EC2_HOST = "ec2-18-218-93-102.us-east-2.compute.amazonaws.com"
REMOTE_PORT = 65432
LOCAL_PORT = 65432

ssh_command = [
	"ssh",
	"-i", SSH_KEY,
	"-R", f"{REMOTE_PORT}:localhost:{LOCAL_PORT}",
	"-R", f"{LOG_REMOTE_PORT}:localhost:{LOG_LOCAL_PORT}",
	f"{EC2_USER}@{EC2_HOST}", 
	"-N", "-o", "ExitOnForwardFailure=yes"
]

def check_network(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False

def start_ssh_tunnel_with_retry(log_func):
    max_retries = 5
    retry_delay = 5
    for attempt in range(max_retries):
        if not check_network():
            log_func(f"Network unavailable, retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
            continue
        log_func(f"Attempting to start SSH tunnel (Attempt {attempt + 1})")
        try:
            tunnel = subprocess.Popen(ssh_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(5)
            if tunnel.poll() is None:
                log_func("SSH Tunnel established successfully.")
                return tunnel
            else:
                log_func(f"SSH Tunnel exited early (Attempt {attempt + 1})")
        except Exception as e:
            log_func(f"Error starting SSH tunnel: {e}")
        time.sleep(retry_delay)
    log_func("Failed to establish SSH tunnel after retries. Exiting.")
    sys.exit(1)

def network_monitor(tunnel_process_ref, log_func):
    while True:
        if not check_network():
            log_func("Network lost! Restarting SSH tunnel...")
            try:
                tunnel_process_ref[0].terminate()
            except Exception:
                pass
            time.sleep(5)
            tunnel_process_ref[0] = start_ssh_tunnel_with_retry(log_func)
        time.sleep(10)
