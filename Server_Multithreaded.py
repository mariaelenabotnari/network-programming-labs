import signal
import socket
import threading
import time

import argparse
import os.path

hostname = "0.0.0.0"
port = 8080

client_threads = []
shutdown_event = threading.Event()


def build_response(status_code, content_type, body):
    return (
        f"HTTP/1.1 {status_code}\r\n"
        f"Content-Type: {content_type}; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: close\r\n\r\n"
    ).encode() + body


def list_files(directory, subpath=""):
    current_directory = os.path.join(directory, subpath)
    if not os.path.exists(current_directory):
        return build_response("404 Not Found", "text/html", b"<h1>Directory not Found</h1>")

    entries = os.listdir(current_directory)
    html = f"<html><body><h1>Files in /{subpath or directory}</h1>"

    if subpath:
        parent_path = os.path.dirname(subpath.rstrip("/"))
        html += f'<p><a href="/browse/{parent_path}">⬅ Back</a></p>'

    for entry in entries:
        entry_path = os.path.join(current_directory, entry)
        url_path = os.path.join(subpath, entry).replace("\\", "/")
        if os.path.isdir(entry_path):
            html += f'<p>📁 <a href="/browse/{url_path}">{entry}</a></p>'
        else:
            html += f'<p>📄 <a href="/view/{url_path}" target="_blank">{entry}</a></p>'

    html += "</body> </html>"

    return build_response("200 OK", "text/html", html.encode())


def serve_file(directory, file_path):
    requested_path = os.path.join(directory, file_path)
    if not os.path.exists(requested_path):
        return build_response("404 Not Found", "text/html", b"<h1>File Not Found</h1>")

    if requested_path.endswith(".png"):
        mime = "image/png"
    elif requested_path.endswith(".pdf"):
        mime = "application/pdf"
    elif requested_path.endswith(".html"):
        mime = "text/html"
    else:
        mime = "plain/text"

    with open(requested_path, "rb") as f:
        body = f.read()

    return build_response("200 OK", mime, body)


def handle_request(directory, request):
    try:
        time.sleep(1)
        request_line = request.split("\r\n")[0]
        method, path, _ = request_line.split(" ")

        requested_path = path.lstrip("/")

        if path == "/" or path.startswith("/browse"):
            subpath = path[len("/browse/"):].rstrip("/") if path.startswith("/browse/") else ""
            return list_files(directory, subpath)

        if path.startswith("/view/"):
            subpath = path[len("/view/"):]
            return serve_file(directory, subpath)

        absolute_path = os.path.join(directory, requested_path)
        if os.path.isdir(absolute_path):
            return list_files(directory, requested_path)
        if os.path.isfile(absolute_path):
            return serve_file(directory, requested_path)

        return build_response("404 Not Found", "text/html", b"<h1>Not Found</h1>")

    except Exception as e:
        return build_response("500 Internal Server Error", "text/html", f"<h1>Error: {e}</h1>".encode())


def handle_client(client_connection_socket, client_address, directory):
    with client_connection_socket:
        try:
            request = client_connection_socket.recv(4096).decode("utf-8", errors="ignore")
            if not request:
                return
            response = handle_request(directory, request)
            client_connection_socket.sendall(response)
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
    print(f"Connection with {client_address} closed.")


def start_server(directory):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((hostname, port))
        server_socket.listen(5)

        print(f"Server started at http://{hostname}:{port}")

        while not shutdown_event.isSet():
            try:
                server_socket.settimeout(1.0)
                client_connection_socket, client_address = server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            print(f"New connection from {client_address}")

            client_thread = threading.Thread(target=handle_client,
                                             args=(client_connection_socket, client_address, directory),
                                             daemon=True)
            client_thread.start()
            client_threads.append(client_thread)

        print("Server is shutting down, waiting for threads to finish...")

        for t in client_threads:
            t.join()

        print("All client threads finished. Server closed.")


def handle_shutdown():
    shutdown_event.set()


signal.signal(signal.SIGINT, handle_shutdown)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A simple socket-based HTTP file server.')
    parser.add_argument('directory', type=str, help='The directory to serve files from.')
    args = parser.parse_args()
    directory = args.directory
    start_server(directory)
