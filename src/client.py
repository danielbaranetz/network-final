import socket
import json
import os


SERVER_IP = "127.0.0.1"
SERVER_PORT = 5050


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
    # 1. הכנת הנתונים
    payload = get_user_payload()
    json_bytes = json.dumps(payload).encode('utf-8')

    print(f"\n[Client] Preparing to send {len(json_bytes)} bytes to {SERVER_IP}:{SERVER_PORT}...")

    # 2. יצירת סוקט TCP
    # AF_INET = IPv4
    # SOCK_STREAM = TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 3. התחברות לשרת (L3 Handshake קורה כאן אוטומטית)
        sock.connect((SERVER_IP, SERVER_PORT))
        print("[Client] Connected successfully!")

        # 4. שליחת ה-JSON
        sock.sendall(json_bytes)
        print("[Client] Data sent. Waiting for response...")

        # 5. המתנה לתשובה מהשרת (חוסם עד שמגיעה תשובה)
        response = sock.recv(1024)
        print(f"\n[Client] Server Response:\n{response.decode()}")

    except ConnectionRefusedError:
        print(f"[Client] Error: Could not connect to {SERVER_IP}:{SERVER_PORT}. Is the server running?")
    except Exception as e:
        print(f"[Client] Error: {e}")
    finally:
        # 6. סגירת החיבור
        sock.close()
        print("[Client] Connection closed.")


if __name__ == "__main__":
    run_tcp_client()