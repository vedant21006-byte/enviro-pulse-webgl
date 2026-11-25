"""
Lightweight Port 5173 Dev Proxy for EnviroPulse 3D
Forwards requests from http://localhost:5173 directly to http://localhost:8000
"""

import http.server
import socketserver
import urllib.request

PORT = 5173
TARGET_PORT = 8000

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        url = f"http://localhost:{TARGET_PORT}{self.path}"
        try:
            req = urllib.request.Request(url, headers={k: v for k, v in self.headers.items() if k.lower() != 'host'})
            with urllib.request.urlopen(req) as response:
                self.send_response(response.status)
                for header, value in response.getheaders():
                    if header.lower() not in ['transfer-encoding', 'content-length']:
                        self.send_header(header, value)
                content = response.read()
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"Proxy Error: {e}".encode('utf-8'))

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), ProxyHandler) as httpd:
        print(f"Proxy forwarding http://localhost:{PORT} -> http://localhost:{TARGET_PORT}")
        httpd.serve_forever()
