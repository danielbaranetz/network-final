import socket
import json
import os

SERVER_IP = "127.0.0.1"
SERVER_PORT = 12345


def get_user_payload():
    print("--- Configuration ---")
    name = input("Enter your name: ") or "Student"
    container_port = input("Enter container port (default 8080): ") or "8080"
    container_name = input("Enter container name (default nginx_server): ") or "nginx_server"

    data = {
        "name": name,
        "container_name": container_name,
        "port": container_port
    }
    return data


def run_tcp_client():
    payload = get_user_payload()
    json_bytes = json.dumps(payload).encode('utf-8')

    print(f"\n[Client] Connecting to {SERVER_IP}:{SERVER_PORT}...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(20)

    try:
        sock.connect((SERVER_IP, SERVER_PORT))
        print("[Client] Connected successfully!")

        sock.sendall(json_bytes)
        print(f"[Client] Data sent ({len(json_bytes)} bytes). Waiting for server logic...")

        response = sock.recv(4096)
        print(f"\n[Client] Server Response:\n{response.decode()}")

    except socket.timeout:
        print("\n[ERROR] Timeout! Server is taking too long (maybe downloading Docker image?).")
    except ConnectionRefusedError:
        print(f"[Client] Error: Could not connect to {SERVER_IP}:{SERVER_PORT}. Is the server running?")
    except Exception as e:
        print(f"[Client] Error: {e}")
    finally:
        sock.close()
        print("[Client] Connection closed.")


if __name__ == "__main__":
    run_tcp_client()