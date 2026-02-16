import random, socket
from EX3_code.EX3_functions import *
from message_types import *


# Server configuration
MAX_SIZES = [5, 24, 18]  # small sizes to clearly see message splitting
size_index = 0
IS_DYNAMIC = True
SERVER_WINDOW_SIZE = 3
DROP_PROBABILITY = 0.3  # Simulates packet loss


# ---------------------- Client Handler ---------------------------------

def handle_client(conn, addr):
    global size_index

    state = "WAIT_FOR_SIN"
    expected_seq = 0
    buffer = []      # Buffer used to rebuild the original message from received chunks

    while True:
        msg = recv_msg(conn)

        # If the message is empty that means the client disconnected
        if msg is None:
            print(f"Client at address {addr[1]} disconnected")
            break

        # Three-way handshake
        if state == "WAIT_FOR_SIN":
            if msg["type"] == TYPE_SIN:
                send_msg(conn, {"type": TYPE_SIN_ACK})
                state = "WAIT_FOR_ACK"

        elif state == "WAIT_FOR_ACK":
            if msg["type"] == TYPE_ACK:
                print("Handshake completed")
                state = "CONNECTED"

        elif state == "CONNECTED":
            # Client asks for max size
            if msg["type"] == TYPE_GET_MAX_SIZE:
                send_msg(conn, {
                    "type": TYPE_MAX_SIZE,
                    "max_size": MAX_SIZES[size_index],
                    "dynamic": IS_DYNAMIC
                })

            # Handles end of message
            elif msg["type"] == TYPE_END_MESSAGE:
                full_message = "".join(buffer)
                print("FULL MESSAGE:", full_message)

                buffer.clear()
                expected_seq = 0

                send_msg(conn, {"type": TYPE_END_MESSAGE_ACK})


            # Client sends DATA
            elif msg["type"] == TYPE_DATA:
                seq = msg["seq"]
                payload = msg["payload"]

                # Simulated packet loss
                if random.random() < DROP_PROBABILITY:
                    print(f"Simulated loss of seq: {seq}")
                    continue

                # Go-Back-N receiver: accept only the expected seq
                if seq == expected_seq:
                    buffer.append(payload)
                    expected_seq += 1
                    print(f"Accepted seq={seq}: {payload!r}")
                else:
                    print(f"Out-of-order seq={seq}, expected={expected_seq} (discarded)")

                # Cumulative ACK: acknowledge the last in-order packet
                ack_msg = {
                    "type": TYPE_ACK,
                    "ack": expected_seq - 1
                }

                # Dynamic message size update, changes every 2 successfully received packets
                if IS_DYNAMIC and expected_seq % 2 == 0:
                    size_index = (size_index + 1) % len(MAX_SIZES)
                    ack_msg["max_size"] = MAX_SIZES[size_index]
                    print("Server changed MAX_SIZE to: ", MAX_SIZES[size_index])

                send_msg(conn, ack_msg)



# ---------------------- MAIN ---------------------------------

def main():
    print("=== TCP Server ===")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Makes sure that i can you the same port over again
    s.bind(("127.0.0.1", 6000))
    s.listen(1)

    print("Server running, waiting for client...")

    while True:
        connection, addr = s.accept()
        print("New client connected from address:", addr) # Server connected to client.
        handle_client(connection, addr)


if __name__ == "__main__":
    main()
