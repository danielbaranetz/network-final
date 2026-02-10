import json
import socket
import os


def set_config():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "config", "config.json")
    name = input("Please enter your name: ")
    container_name = input("Please set a container name (default: nginx_server): ") or "nginx_server"
    port = input("Please set the internal port you would like to use (default: 8080): ") or "8080"
    try:
        with open(json_path, "r") as file:
            data = json.load(file)
        data['name'] = name
        data['container_name'] = container_name
        data['port'] = port
        with open(json_path, "w") as file:
            json.dump(data, file, indent=2)
        return data
    except FileNotFoundError:
        return f"ERROR: Could not find config file at: {json_path}"


if __name__ == "__main__":
    user_input = "Daniel"
    print(set_config())