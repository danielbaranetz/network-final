import socket

DNS_LOCAL_IP = "127.0.0.1"
DNS_LOCAL_PORT = 5354
GOOGLE_DNS = ("8.8.8.8", 53)
BUFFER_SIZE = 1024

LOCAL_RECORDS = {"myagent.local.": "127.0.0.1"}


def start_dns_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        server_socket.bind((DNS_LOCAL_IP, DNS_LOCAL_PORT))
        print(f"[STATUS] DNS Server started successfully on {DNS_LOCAL_IP}:{DNS_LOCAL_PORT}")
    except Exception as e:
        print(f"[ERROR] Could not start server: {e}")
        return

    print("[INFO] Waiting for DNS queries...")

    while True:
        try:
            data, client_address = server_socket.recvfrom(BUFFER_SIZE)
            print(f"\n[QUERY] Received request from client at {client_address}")
            print(f"[DEBUG] Raw data length: {len(data)} bytes")

            print(f"[FORWARD] Sending query to Google DNS ({GOOGLE_DNS[0]})...")

            proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            proxy_socket.settimeout(2.0)

            proxy_socket.sendto(data, GOOGLE_DNS)

            response, _ = proxy_socket.recvfrom(BUFFER_SIZE)
            print(f"[RESPONSE] Received answer from Google DNS ({len(response)} bytes)")

            server_socket.sendto(response, client_address)
            print(f"[DONE] Sent response back to client {client_address}")

            proxy_socket.close()

        except socket.timeout:
            print("[TIMEOUT] Google DNS did not respond within 2 seconds.")
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred: {e}")


if __name__ == "__main__":
    start_dns_server()