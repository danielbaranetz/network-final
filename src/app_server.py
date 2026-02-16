import subprocess
import os
import shutil

import client


def run_agent_with_template():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, "html", "template.html")
    output_path = os.path.join(base_dir, "html", "index.html")
    data = client.set_config()
    data_name = data['name']
    data_port = data['port']


    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        final_html = html_content.replace("{{NAME}}",data_name)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_html)

    except FileNotFoundError:
        return f"ERROR: Could not find template file at: {template_path}"

    if not shutil.which("docker"):
        return "Simulation: Docker not installed."

    html_folder = os.path.dirname(output_path)

    cmd = [
        "docker", "run", "-d",
        "-p", f"{data_port}:80",
        "--rm",
        "--name", "my_template_site",
        "-v", f"{html_folder}:/usr/share/nginx/html",
        "nginx"
    ]

    try:
        subprocess.run(["docker", "rm", "-f", "my_template_site"], capture_output=True)

        subprocess.run(cmd, check=True, capture_output=True)
        return f"SUCCESS! Website updated. Check http://localhost:{data_port}"

    except subprocess.CalledProcessError as e:
        return f"Docker Error: {e.stderr.decode()}"


if __name__ == "__main__":
    print(run_agent_with_template())
