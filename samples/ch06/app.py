import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        message = os.environ.get("APP_MESSAGE", "こんにちは")
        body = message.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"listening on {port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
