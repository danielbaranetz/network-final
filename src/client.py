import socket
import json, random
import os, uuid
from constants import *
import argparse

#CLIENT_ID_FILE = "client_id.txt"
#CLIENT_ID_FILE = os.path.join(os.path.dirname(__file__), "client_id.txt")

BASE_DIR = os.path.dirname(__file__)
DEFAULT_CLIENT_NUM = 1

def client_id_path(client_num: int) -> str:
    return os.path.join(BASE_DIR, f"client_id_{client_num}.txt")

# def get_or_create_client_id():
#     if os.path.exists(CLIENT_ID_FILE):
#         return open(CLIENT_ID_FILE, "r", encoding="utf-8").read().strip()
#
#     cid = str(uuid.uuid4())
#     with open(CLIENT_ID_FILE, "w", encoding="utf-8") as f:
#         f.write(cid)
#     return cid

def get_or_create_client_id(client_num: int) -> str:
    path = client_id_path(client_num)

    if os.path.exists(path):
        return open(path, "r", encoding="utf-8").read().strip()

    cid = str(uuid.uuid4())
    with open(path, "w", encoding="utf-8") as f:
        f.write(cid)
    return cid


def resolve_dns_locally(domain):
    try:
        dns_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dns_sock.settimeout(2)
        header = b'\xaa\xaa\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00'
        query = b'\x07myagent\x05local\x00\x00\x01\x00\x01'
        dns_sock.sendto(header + query, ("127.0.0.1", 5358))
        dns_sock.recvfrom(1024)
        print("[DNS] Domain resolved via local DNS server")
    except:
        print("[DNS] DNS server not responding, using default IP")
    finally:
        dns_sock.close()




def run_dhcp_server():

#def run_dhcp_server():
def run_dhcp_server(client_num: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)

    #client_id = get_or_create_client_id()
    client_id = get_or_create_client_id(client_num)
    xid = random.randint(1, 99999)

    discover = {"type": "DISCOVER", "xid": xid, "client_id": client_id}

    offer = None
    for attempt in range(3):
        sock.sendto(json.dumps(discover).encode(), (DHCP_SERVER_IP, DHCP_SERVER_PORT))
        try:
            data, _ = sock.recvfrom(4096)
            msg = json.loads(data.decode())

            if msg.get("xid") != xid:
                continue

            if msg.get("type") == "OFFER":
                offer = msg
                break

            if msg.get("type") == "NAK":
                print("DHCP NAK:", msg)
                return None

        except socket.timeout:
            print(f"[DHCP] DISCOVER timeout (attempt {attempt+1}/3)")

    if not offer:
        print("[DHCP] Failed to get OFFER")
        return None

    print("Received OFFER:", offer)

    # REQUEST
    request = {
        "type": "REQUEST",
        "xid": xid,
        "client_id": client_id,
        "requested_ip": offer["offered_ip"]
    }

    ack = None
    for attempt in range(3):
        print(f"[DHCP] Sending REQUEST (attempt {attempt + 1}/3)")
        sock.sendto(json.dumps(request).encode(), (DHCP_SERVER_IP, DHCP_SERVER_PORT))

        try:
            data, _ = sock.recvfrom(4096)
            msg = json.loads(data.decode())

            if msg.get("xid") != xid:
                continue

            if msg.get("type") == "ACK":
                ack = msg
                break

            if msg.get("type") == "NAK":
                print("[DHCP] Server returned NAK:", msg)
                return None

        except socket.timeout:
            print(f"[DHCP] REQUEST timeout (attempt {attempt + 1}/3)")

    if not ack:
        print("[DHCP] Failed to get ACK")
        return None

    print("Received ACK:", ack)
    return ack


    # sock.sendto(json.dumps(request).encode(), (DHCP_SERVER_IP, DHCP_SERVER_PORT))
    #
    # try:
    #     data, _ = sock.recvfrom(4096)
    #     ack = json.loads(data.decode())
    #
    #     if ack.get("xid") != xid:
    #         print("[DHCP] ACK xid mismatch")
    #         return None
    #
    #     if ack.get("type") != "ACK":
    #         print("[DHCP] Failed, got:", ack)
    #         return None
    #
    #     print("Received ACK:", ack)
    #     return ack

    # except socket.timeout:
    #     print("[DHCP] REQUEST timeout")
    #     return None
    # finally:
    #     sock.close()


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

#def dhcp_release():
def dhcp_release(client_num: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)

    #client_id = get_or_create_client_id()
    client_id = get_or_create_client_id(client_num)
    xid = random.randint(1, 99999)

    release = {"type": "RELEASE", "xid": xid, "client_id": client_id}
    sock.sendto(json.dumps(release).encode(), (DHCP_SERVER_IP, DHCP_SERVER_PORT))

    try:
        data, _ = sock.recvfrom(4096)
        resp = json.loads(data.decode())
        print("Received RELEASE response:", resp)
        return resp
    except socket.timeout:
        print("[DHCP] RELEASE timeout")
        return None
    finally:
        sock.close()


def run_tcp_client():
    resolve_dns_locally("myagent.local")
    payload = get_user_payload()
    json_bytes = json.dumps(payload).encode('utf-8')

    print(f"\n[Client] Connecting to {APP_SERVER_IP}:{SERVER_PORT}...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(20)

    try:
        sock.connect((APP_SERVER_IP, SERVER_PORT))
        print("[Client] Connected successfully!")

        sock.sendall(json_bytes)
        print(f"[Client] Data sent ({len(json_bytes)} bytes). Waiting for server logic...")

        response = sock.recv(4096)
        print(f"\n[Client] Server Response:\n{response.decode()}")

    except socket.timeout:
        print("\n[ERROR] Timeout! Server is taking too long (maybe downloading Docker image?).")
    except ConnectionRefusedError:
        print(f"[Client] Error: Could not connect to {APP_SERVER_IP}:{SERVER_PORT}. Is the server running?")
    except Exception as e:
        print(f"[Client] Error: {e}")
    finally:
        sock.close()
        print("[Client] Connection closed.")


# if __name__ == "__main__":
#     ack = run_dhcp_server()
#     if not ack:
#         exit(1)
#     assigned_ip = ack.get("assigned_ip")
#     print(f"[Client] My assigned IP: {assigned_ip}")
#
#     run_tcp_client()
#
#     dhcp_release()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", type=int, default=1, help="Client number (e.g., 1,2,3)")
    args = parser.parse_args()

    client_num = args.client
    print(f"[Client] Running as client #{client_num}")

    ack = run_dhcp_server(client_num)
    if not ack:
        exit(1)

    assigned_ip = ack.get("assigned_ip")
    print(f"[Client {client_num}] My assigned IP: {assigned_ip}")

    run_tcp_client()

    dhcp_release(client_num)