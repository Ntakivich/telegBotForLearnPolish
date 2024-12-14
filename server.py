from http.server import BaseHTTPRequestHandler, HTTPServer

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Hello, visitor!")

def start_http_server(port=8000):
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()
