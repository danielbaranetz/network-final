import socket
import json
import time
import threading
from constants import *

leases = {}          # client_id -> {ip, expires}
ip_in_use = {}       # ip -> client_id
pending_offers = {}  # (client_id, xid) -> ip


#------------------------ FUNCTIONS ----------------------------------
def cleanup_expired_leases():
    while True:
        now = time.time()
        expired = []
        for client_id, data in leases.items():
            if data["expires"] <= now:
                expired.append(client_id)

        for cid in expired:
            ip = leases[cid]["ip"]
            del leases[cid]
            del ip_in_use[ip]
            print(f"[LEASE EXPIRED] {cid} -> {ip}")

        time.sleep(5)


def get_free_ip():
    for ip in IP_POOL:
        if ip not in ip_in_use and ip not in pending_offers.values():
            return ip
    return None


def handle_discover(msg):
    client_id = msg["client_id"]
    xid = msg["xid"]

    # אם יש כבר lease תקף → תחזירי אותו
    if client_id in leases:
        if leases[client_id]["expires"] > time.time():
            pending_offers[(client_id, xid)] = leases[client_id]["ip"]
            return {
                "type": "OFFER",
                "xid": xid,
                "offered_ip": leases[client_id]["ip"],
                "lease_time": LEASE_TIME
            }

    ip = get_free_ip()
    if not ip:
        return {"type": "NAK", "xid": xid, "reason": "POOL_EXHAUSTED"}

    pending_offers[(client_id, xid)] = ip

    return {
        "type": "OFFER",
        "xid": xid,
        "offered_ip": ip,
        "lease_time": LEASE_TIME
    }


def handle_request(msg):
    client_id = msg["client_id"]
    xid = msg["xid"]
    requested_ip = msg["requested_ip"]

    if client_id in leases:
        if leases[client_id]["expires"] > time.time() and leases[client_id]["ip"] == requested_ip:
            # לרענן את זמן ה-lease
            leases[client_id]["expires"] = time.time() + LEASE_TIME

            return {
                "type": "ACK",
                "xid": xid,
                "assigned_ip": requested_ip,
                "lease_time": LEASE_TIME,
                "dns_ip": DNS_SERVER_IP,
                "app_server_ip": APP_SERVER_IP
            }

    key = (client_id, xid)

    if key not in pending_offers:
        return {"type": "NAK", "xid": xid, "reason": "NO_PENDING_OFFER"}

    if pending_offers[key] != requested_ip:
        return {"type": "NAK", "xid": xid, "reason": "IP_MISMATCH"}

    # commit lease
    leases[client_id] = {
        "ip": requested_ip,
        "expires": time.time() + LEASE_TIME
    }

    ip_in_use[requested_ip] = client_id
    del pending_offers[key]

    print(f"[LEASE GRANTED] {client_id} -> {requested_ip}")

    return {
        "type": "ACK",
        "xid": xid,
        "assigned_ip": requested_ip,
        "lease_time": LEASE_TIME,
        "dns_ip": DNS_SERVER_IP,
        "app_server_ip": APP_SERVER_IP
    }

#------------------------ MAIN FUNCTION ---------------------------------------
def start_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((DHCP_SERVER_IP, DHCP_SERVER_PORT))

    print(f"DHCP Server running on {DHCP_SERVER_IP}:{DHCP_SERVER_PORT}")

    while True:
        data, addr = sock.recvfrom(4096)
        msg = json.loads(data.decode())

        if msg["type"] == "DISCOVER":
            response = handle_discover(msg)
        elif msg["type"] == "REQUEST":
            response = handle_request(msg)
        else:
            continue

        sock.sendto(json.dumps(response).encode(), addr)


if __name__ == "__main__":
    threading.Thread(target=cleanup_expired_leases, daemon=True).start()
    start_server()
