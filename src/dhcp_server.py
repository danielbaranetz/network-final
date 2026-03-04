import socket, json, time, threading
from constants import *

leases = {}          # client_id -> {"ip": str, "expires": float}
ip_in_use = {}       # ip -> client_id
pending_offers = {}  # (client_id, xid) -> {"ip": str, "expires": float}

lock = threading.Lock()

#------------------------ FUNCTIONS ----------------------------------

def cleanup_loop():
    while True:
        now = time.time()
        with lock:
            # cleanup expired leases
            expired_leases = [cid for cid, d in leases.items() if d["expires"] <= now]
            for cid in expired_leases:
                ip = leases[cid]["ip"]
                leases.pop(cid, None)
                ip_in_use.pop(ip, None)
                print(f"[LEASE EXPIRED] client_id={cid} ip={ip}")

            # cleanup expired pending offers
            expired_offers = [key for key, d in pending_offers.items() if d["expires"] <= now]
            for key in expired_offers:
                ip = pending_offers[key]["ip"]
                pending_offers.pop(key, None)
                print(f"[OFFER EXPIRED] key={key} ip={ip}")

        time.sleep(2)

def get_free_ip():
    with lock:
        offered_ips = {d["ip"] for d in pending_offers.values()}
        for ip in IP_POOL:
            if ip not in ip_in_use and ip not in offered_ips:
                return ip
    return None


def handle_discover(msg):
    client_id = msg["client_id"]
    xid = msg.get["xid"]

    if not client_id or xid is None:
        return {
            "type": "NAK",
            "xid": xid,
            "reason": "MISSING_FIELDS"
        }

    now = time.time()

    with lock:
        # valid lease exists -> re-offer same IP
        if client_id in leases and leases[client_id]["expires"] > now:
            ip = leases[client_id]["ip"]
            pending_offers[(client_id, xid)] = {"ip": ip, "expires": now + OFFER_TTL}

            return {
                "type": "OFFER",
                "xid": xid,
                "offered_ip": ip,
                "lease_time": LEASE_TIME
            }

    ip = get_free_ip()
    if not ip:
        return {
            "type": "NAK",
            "xid": xid,
            "reason": "POOL_EXHAUSTED"
        }

    with lock:
        pending_offers[(client_id, xid)] = {"ip": ip, "expires": now + OFFER_TTL}

    return {
        "type": "OFFER",
        "xid": xid,
        "offered_ip": ip,
        "lease_time": LEASE_TIME
    }


def handle_request(msg):
    client_id = msg.get("client_id")
    xid = msg.get("xid")

    requested_ip = msg.get("requested_ip")
    if not client_id or xid is None or not requested_ip:
        return {
            "type": "NAK",
            "xid": xid,
            "reason": "MISSING_FIELDS"
        }

    now = time.time()
    key = (client_id, xid)

    with lock:
        # If client already has that lease -> renew
        if client_id in leases and leases[client_id]["ip"] == requested_ip and leases[client_id]["expires"] > now:
            leases[client_id]["expires"] = now + LEASE_TIME
            return {
                "type": "ACK", "xid": xid,
                "assigned_ip": requested_ip,
                "lease_time": LEASE_TIME,
                "dns_ip": DNS_SERVER_IP,
                "app_server_ip": APP_SERVER_IP
            }

        # must have matching pending offer
        if key not in pending_offers:
            return {
                "type": "NAK",
                "xid": xid,
                "reason": "NO_PENDING_OFFER"
            }

        offered = pending_offers[key]
        if offered["expires"] <= now:
            pending_offers.pop(key, None)
            return {
                "type": "NAK",
                "xid": xid,
                "reason": "OFFER_EXPIRED"
            }

        if offered["ip"] != requested_ip:
            return {
                "type": "NAK",
                "xid": xid,
                "reason": "IP_MISMATCH"
            }

        # commit lease
        leases[client_id] = {"ip": requested_ip, "expires": now + LEASE_TIME}
        ip_in_use[requested_ip] = client_id
        pending_offers.pop(key, None)

    print(f"[LEASE GRANTED] client_id={client_id} ip={requested_ip}")
    return {
        "type": "ACK", "xid": xid,
        "assigned_ip": requested_ip,
        "lease_time": LEASE_TIME,
        "dns_ip": DNS_SERVER_IP,
        "app_server_ip": APP_SERVER_IP
    }

def handle_release(msg):
    client_id = msg.get("client_id")
    xid = msg.get("xid")

    if not client_id:
        return {"type": "NAK", "xid": xid, "reason": "MISSING_CLIENT_ID"}

    with lock:
        if client_id not in leases:
            return {"type": "ACK", "xid": xid, "released": False, "reason": "NO_ACTIVE_LEASE"}

        ip = leases[client_id]["ip"]
        leases.pop(client_id, None)
        ip_in_use.pop(ip, None)

        # לנקות offers תלויים של אותו client (נחמד)
        to_delete = [k for k in pending_offers.keys() if k[0] == client_id]
        for k in to_delete:
            pending_offers.pop(k, None)

    print(f"[LEASE RELEASED] client_id={client_id} ip={ip}")
    return {"type": "ACK", "xid": xid, "released": True, "released_ip": ip}

#------------------------ MAIN FUNCTION ---------------------------------------
def start_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((DHCP_SERVER_IP, DHCP_SERVER_PORT))
    print(f"[DHCP] listening on: {DHCP_SERVER_IP}:{DHCP_SERVER_PORT}")

    while True:
        data, addr = sock.recvfrom(4096)
        try:
            msg = json.loads(data.decode())
        except Exception:
            continue

        mtype = msg.get("type")
        if mtype == "DISCOVER":
            resp = handle_discover(msg)
        elif mtype == "REQUEST":
            resp = handle_request(msg)
        elif mtype == "RELEASE":
            resp = handle_release(msg)
        else:
            resp = {"type": "NAK", "xid": msg.get("xid"), "reason": "UNKNOWN_TYPE"}

        print(
            f"[DHCP] RX {mtype} from {addr} -> TX {resp.get('type')} xid={resp.get('xid')} client_id={msg.get('client_id')}")
        sock.sendto(json.dumps(resp).encode(), addr)



if __name__ == "__main__":
    threading.Thread(target=cleanup_loop, daemon=True).start()
    start_server()
