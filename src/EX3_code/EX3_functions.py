import json

# ---------------------- FUNCTIONS ---------------------------------

# Sends a length-prefixed JSON message
def send_msg(sock, obj):
    data = json.dumps(obj).encode("utf-8")
    msg_len = len(data)

    header = msg_len.to_bytes(4, "big")
    sock.sendall(header)
    sock.sendall(data)
    print("SEND:", obj)


# Receives a length-prefixed JSON message
def recv_msg(sock):
    header = sock.recv(4)
    if not header:
        return None

    msg_len = int.from_bytes(header, "big")
    data = b"" #  An empty bit sequence

    while len(data) < msg_len:
        chunk = sock.recv(msg_len - len(data))
        if not chunk:
            return None
        data += chunk

    full_msg = json.loads(data.decode("utf-8"))
    print("RECV:", full_msg)
    return full_msg

