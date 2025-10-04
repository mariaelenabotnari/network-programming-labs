import os.path
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

hostname = "localhost"
port = 8080
directory = "book_covers"

class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.list_files()

        elif self.path.startswith("/view/"):
            filename = self.path[len("/view/"):]
            file_path = os.path.join(directory, filename)
            if not os.path.exists(file_path):
                self.send_error(404, "File Not Found")
                return

            html = f"""
                    <html>
                    <body>
                    <h1>Displaying: {filename}</h1>
                    <img src="/{directory}/{filename}" alt="{filename}" style="max-width:500px;">
                    <br><br>
                    <a href="/">Back to list</a>
                    </body>
                    </html>
                    """

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        elif self.path.startswith(f"/{directory}/"):
            self.serve_file()

        else:
            self.send_error(404, "Not Found")

    def list_files(self):
        files = [file for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]
        html = "<html> <body> <h1> Files in directory </h1>"
        for file in files:
            html += f'<a href="/view/{file}"> {file} </a>'
        html += "</body> </html>"

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes(html, "utf-8"))

    def serve_file(self):
        requested_path = os.path.join(".", self.path.lstrip("/"))
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
