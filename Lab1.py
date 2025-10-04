import os.path
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

hostname = "localhost"
port = 8080
directory = "book_covers"

class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        requested_path = self.path.lstrip("/")

        if self.path == "/":
            self.list_files()
            return

        if self.path.startswith("/browse/") or self.path == "/browse":
            subpath = self.path[len("/browse/"):].rstrip("/")
            self.list_files(subpath)
            return

        if self.path.startswith("/view/"):
            subpath = self.path[len("/view/"):]
            self.serve_file(subpath)
            return

        absolute_path = os.path.join(".", requested_path)

        if os.path.isdir(absolute_path):
            subpath = requested_path[len(directory):].lstrip("/") if requested_path.startswith(directory) else requested_path
            self.list_files(subpath)
            return

        if os.path.isfile(absolute_path):
            self.serve_file(requested_path)
            return

        self.send_error(404, "Not Found")

    def list_files(self, subpath=""):
        current_directory = os.path.join(directory, subpath)
        if not os.path.exists(current_directory):
            self.send_error(404, "Directory not Found")
            return

        entries = os.listdir(current_directory)
        html = f"<html><body><h1>Files in /{subpath or directory}</h1>"

        if subpath:
            parent_path = os.path.dirname(subpath.rstrip("/"))
            html += f'<p><a href="/browse/{parent_path}">⬅ Back</a></p>'

        for entry in entries:
            entry_path = os.path.join(current_directory, entry)
            url_path = os.path.join(subpath, entry).replace("\\", "/")
            if os.path.isdir(entry_path):
                html += f'<p>📁 <a href="/browse/{url_path}" target="_blank">{entry}</a></p>'
            else:
                html += f'<p>📄 <a href="/view/{url_path}" target="_blank">{entry}</a></p>'

        html += "</body> </html>"

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(bytes(html, "utf-8"))

    def serve_file(self, file_path):
        requested_path = os.path.join(directory, file_path)
        if not os.path.exists(requested_path):
            self.send_error(404, "File Not Found")
            return

        if requested_path.endswith(".png"):
            mime = "image/png"
        elif requested_path.endswith(".pdf"):
            mime = "application/pdf"
        elif requested_path.endswith(".html"):
            mime = "text/html"
        else:
            mime = "plain/text"

        self.send_response(200)
        self.send_header("Content-type", mime)
        self.end_headers()
        with open(requested_path, "rb") as f:
            self.wfile.write(f.read())


if __name__ == "__main__":
    web_server = HTTPServer((hostname, port), Server)
    print("Server started http://%s:%s" % (hostname, port))

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass

    web_server.server_close()
    print("Server stopped")
