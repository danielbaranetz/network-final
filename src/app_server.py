import socket
import json
import subprocess
import os
import shutil

LISTENING_IP = '0.0.0.0'
LISTENING_PORT = 12345


def deploy_container_logic(data):
    user_name = data.get('name', 'Guest')
    container_name = data.get('container_name', 'nginx_server')
    website_port = data.get('port', '8080')

    print(f"[Server] Processing deployment for: {user_name} on port {website_port}")

    base_dir = os.path.dirname(os.path.abspath(__file__))

    template_path = os.path.join(base_dir, "html", "template.html")
    output_path = os.path.join(base_dir, "html", "index.html")

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        final_html = html_content.replace("{{NAME}}", user_name)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_html)

    except FileNotFoundError:
        return f"ERROR: Template file missing at {template_path}. Please make sure 'html/template.html' exists."
    except Exception as e:
        return f"ERROR processing HTML: {str(e)}"

    if not shutil.which("docker"):
        return "ERROR: Docker is not installed on the server."

    html_folder = os.path.dirname(output_path)

    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)

    cmd = [
        "docker", "run", "-d",
        "-p", f"{website_port}:80",
        "--rm",
        "--name", container_name,
        "-v", f"{html_folder}:/usr/share/nginx/html",
        "nginx"
    ]

    print(f"[Server] Running Docker container '{container_name}'...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True)
        container_id = result.stdout.decode().strip()[:12]
        return f"SUCCESS! Site deployed. ID: {container_id}. Visit http://localhost:{website_port}"

    except subprocess.CalledProcessError as e:
        return f"DOCKER ERROR: {e.stderr.decode()}"


def start_tcp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((LISTENING_IP, LISTENING_PORT))
        server_socket.listen(5)
        print(f"[*] Server listening on {LISTENING_IP}:{LISTENING_PORT}...")

        while True:
            client_socket, addr = server_socket.accept()
            print(f"[+] Connection from {addr}")
            handle_client_connection(client_socket)

    except Exception as e:
        print(f"[!] Server Error: {e}")
    finally:
        server_socket.close()


def handle_client_connection(client_socket):
    with client_socket:
        try:
            data = client_socket.recv(4096)
            if not data:
                return

            json_str = data.decode('utf-8')
            payload = json.loads(json_str)
            response = deploy_container_logic(payload)
            client_socket.sendall(response.encode('utf-8'))
            print("[Server] Response sent to client.")

        except json.JSONDecodeError:
            client_socket.sendall(b"ERROR: Invalid JSON format.")
        except Exception as e:
            print(f"Handler Error: {e}")


if __name__ == "__main__":
    start_tcp_server()
