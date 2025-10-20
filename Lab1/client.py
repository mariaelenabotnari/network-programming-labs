import argparse
import os
import socket

def download_file(hostname, port, filename, directory):
    if not filename.strip():
        raise ValueError("Error: filename cannot be empty.")

    if filename.endswith("/") or filename.endswith("\\"):
        raise ValueError("Error: filename points to a directory, not a file.")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((hostname, port))

        request = f"GET /view/{filename} HTTP/1.1\r\nHost: {hostname}\r\nConnection: close\r\n\r\n"
        client_socket.sendall(request.encode())

        response = b""
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            response = response + chunk

        header_data, body = response.split(b"\r\n\r\n", 1)
        headers = header_data.decode().split("\r\n")

        status_line = headers[0]
        status_code = int(status_line.split(" ")[1])
        if status_code == 404:
            raise FileNotFoundError(f"Error: The file '{filename}' does not exist on the server.")

        content_type = "text/plain"
        for header_line in headers:
            if header_line.lower().startswith("content-type:"):
                content_type = header_line.split(":", 1)[1].strip().lower()
                break

        if content_type.startswith("text/html"):
            print("\nBody of the response:")
            print(body.decode(errors="ignore"))
            file_path = os.path.join(directory, os.path.basename(filename))
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(body.decode(errors="ignore"))
            print(f"HTML file saved: {file_path}")

        elif content_type.startswith("image/png") or content_type.startswith("application/pdf"):
            file_path = os.path.join(directory, os.path.basename(filename))
            with open(file_path, "wb") as f:
                f.write(body)
            print(f"File saved: {file_path}")

        else:
            print(f"Unsupported content type: {content_type}")

def main():
    parser = argparse.ArgumentParser(description='HTTP Client for file server')
    parser.add_argument('server_host', help='Server hostname or IP')
    parser.add_argument('server_port', type=int, help='Server port number')
    parser.add_argument('filename', help='Filename or path to download')
    parser.add_argument('save_directory', help='Directory to save files in')

    args = parser.parse_args()

    url = f"http://{args.server_host}:{args.server_port}/view/{args.filename}"

    print(f"Downloading: {url}")
    print(f"Saving to directory: {args.save_directory}")
    download_file(args.server_host, args.server_port, args.filename, args.save_directory)

if __name__ == "__main__":
    main()