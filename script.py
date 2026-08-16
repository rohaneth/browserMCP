from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime, timezone

HOST = "localhost"
PORT = 8000


class EventHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"Browser Memory Observer server is running!"
        )

    def do_POST(self):
        if self.path != "/events":
            self.send_response(404)
            self.end_headers()
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            event = json.loads(body)

            print("\n📥 Browser event received:")
            print(json.dumps(event, indent=2, ensure_ascii=False))

            with open("events.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            self.wfile.write(
                json.dumps({"status": "ok"}).encode("utf-8")
            )

        except Exception as e:
            print("❌ Error:", e)
            self.send_response(400)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), EventHandler)

    print("🚀 Browser Memory Observer running")
    print("🌐 http://localhost:8000")
    print("📡 POST endpoint: http://localhost:8000/events")
    print("📝 Saving events to events.log")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.server_close()