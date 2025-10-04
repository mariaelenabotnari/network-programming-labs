import os.path
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

hostname = "localhost"
port = 8080

class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        file_path = self.path[1:]
        if self.path == '/':
            pass
        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.send_response(200)
            if file_path.endswith(".html"):
                self.send_header('Content-type', 'text/html')
            elif file_path.endswith(".png"):
                self.send_header('Content-Type', 'image/png')
            elif file_path.endswith('.pdf'):
                self.send_header('Content-type', 'text/pdf')
            else:
                self.send_header('Content-type', 'text/plain')
            self.end_headers()
            with open(file_path, "rb") as file:
                self.wfile.write(file.read())
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("<html><body><h1>404 - File Not Found</h1></body></html>", "utf-8"))


if __name__ == "__main__":
    web_server = HTTPServer((hostname, port), Server)
    print("Server started http://%s:%s" % (hostname, port))

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass

    web_server.server_close()
    print("Server stopped")
