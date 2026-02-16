import socket, time
from EX3_functions import *
from message_types import *


CLIENT_WINDOW_SIZE = 3       # Sliding window size
TIMEOUT = 3                  # Timeout in seconds

# ---------------------- FUNCTIONS ---------------------------------

def send_end_message(sock):
    msg = {"type": TYPE_END_MESSAGE}
    send_msg(sock, msg)


# Reads a message from a txt file
def read_messages_from_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
        return []


# Reads a message from the user
def read_messages_from_user():
    messages = []
    print("Enter messages:")
    print("* To submit make sure you have an empty line at the end * \n")
    while True:
        line = input()
        if line == "":
            break
        messages.append(line)
    return messages


# ---------------------- MAIN ---------------------------------

def main():
    print("=== TCP Client ===")
    sock = socket.create_connection(("127.0.0.1", 6000))
    sock.settimeout(0.5)

    # -------- Handshake --------
    send_msg(sock, {"type": TYPE_SIN}) # Sending a SIN message to the server so that the client can connect
    SIN_res = recv_msg(sock)

    if SIN_res["type"] != TYPE_SIN_ACK:
        print("Handshake Failed!")
        return

    send_msg(sock, {"type": TYPE_ACK})
    print("Handshake Succeeded!")
    print(f"Connected to server 127.0.0.1 : 6000\n") # Client connected to server.

    # -------- Get MAX_SIZE --------
    # Request from the server the max message size
    send_msg(sock, {"type": TYPE_GET_MAX_SIZE})
    max_size_res =  recv_msg(sock)
    MAX_SIZE = max_size_res["max_size"]

    # -------- Main loop --------
    # Keep the connection open until user chooses EXIT
    while True:
        client_choice = input("\nChoose input method: \n text = Enter your own text to send \n file = Enter a filename to send \n exit = Disconnect from the server \n ").strip()

        if client_choice == "exit":
            break
        elif client_choice == "text":
            messages = read_messages_from_user()
        elif client_choice == "file":
            filename = input("Enter file name: ")
            messages = read_messages_from_file(filename)
        else:
            print("Invalid choice")
            return

        # Split message
        for message in messages:

            chunks = [
                message[i:i + MAX_SIZE]
                for i in range(0, len(message), MAX_SIZE)
            ]

            seq = 0
            next_seq = 0
            send_times = {}
            total = len(chunks)

            sock.settimeout(0.5)

            while seq < total:

                # Send packets within the window
                while next_seq < total and next_seq < seq + CLIENT_WINDOW_SIZE:
                    send_msg(sock, {
                        "type": TYPE_DATA,
                        "seq": next_seq,
                        "payload": chunks[next_seq]
                    })
                    send_times[next_seq] = time.time()
                    next_seq += 1


                # Timeout check
                if seq in send_times:
                    elapsed = time.time() - send_times[seq]
                    if elapsed > TIMEOUT:
                        print("Timeout! Retransmitting from: ", seq)
                        next_seq = seq
                        send_times.clear()
                        continue

                # Receive ACK
                try:
                    ack_msg = recv_msg(sock)
                    if ack_msg is None:
                        break

                    if "max_size" in ack_msg:
                        MAX_SIZE = ack_msg["max_size"]
                        print("Client updated MAX_SIZE to: ", MAX_SIZE)

                    ack = ack_msg["ack"]

                    if ack >= seq:
                        for s in range(seq, ack + 1):
                            send_times.pop(s, None)
                        seq = ack + 1



                except socket.timeout:
                    pass

            send_end_message(sock)

            while True:
                end_ack = recv_msg(sock)
                if end_ack and end_ack["type"] == TYPE_END_MESSAGE_ACK:
                    print("Server confirmed end of message")
                    break

if __name__ == "__main__":
    main()
