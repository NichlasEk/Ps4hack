#!/usr/bin/env python3
"""LAN-only PS4 13.52 asset host with persistent request and /t telemetry logs."""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from urllib.parse import parse_qs, unquote, urlsplit
import uuid

ROOT = Path(__file__).resolve().parent
LANDING = "/1302-1352/index.html"
MAX_BODY = 65536
TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".png": "image/png",
    ".bin": "application/octet-stream",
    ".appcache": "text/cache-manifest; charset=utf-8",
}


class Journal:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.run_id = str(uuid.uuid4())

    def write(self, kind, **fields):
        now = datetime.now(timezone.utc)
        record = dict(time=now.isoformat(), run_id=self.run_id, **fields)
        line = json.dumps(record, ensure_ascii=True) + "\n"
        path = self.directory / f"{kind}-{now:%Y-%m-%d}.jsonl"
        with self.lock, path.open("a", encoding="utf-8") as file:
            file.write(line)


def load_assets(asset_dir):
    base = Path(asset_dir).resolve()
    manifest = json.loads((base / "generated/asset-manifest.json").read_text())
    assets = {}
    for item in manifest["assets"]:
        route = item["route"]
        if not route.startswith("/1302-1352/") or ".." in route.split("/"):
            raise ValueError(f"Invalid asset route: {route}")
        packed = (base / "data" / (route.lstrip("/") + ".gz")).read_bytes()
        raw = gzip.decompress(packed)
        if len(packed) != item["compressed_bytes"] or len(raw) != item["bytes"]:
            raise ValueError(f"Asset size mismatch: {route}")
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError(f"Asset hash mismatch: {route}")
        assets[route] = (packed, raw, TYPES[Path(route).suffix])
    if len(assets) != 15 or LANDING not in assets:
        raise ValueError("Expected all 15 pinned upstream assets")
    return assets


def accepts_gzip(value):
    for token in value.lower().split(","):
        parts = [part.strip() for part in token.split(";")]
        if parts[0] != "gzip":
            continue
        try:
            quality = next((float(p[2:]) for p in parts[1:] if p.startswith("q=")), 1)
        except ValueError:
            return False
        return quality > 0
    return False


class Host(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, asset_dir, log_dir):
        self.assets = load_assets(asset_dir)
        self.journal = Journal(log_dir)
        super().__init__(address, Handler)
        self.journal.write("server", event="start", bind=address[0],
                           port=self.server_port, assets=len(self.assets))


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "PS4LANHost/1"

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, fmt, *args):
        # Responses are logged as structured JSON below, without header secrets.
        pass

    def reply(self, status, data=b"", mime="text/plain; charset=utf-8", **headers):
        self.close_connection = True
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.send_header("Cache-Control", "no-cache")
        for key, value in headers.items():
            self.send_header(key.replace("_", "-"), value)
        self.end_headers()
        completed = True
        try:
            if self.command != "HEAD" and data:
                self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            completed = False
        self.server.journal.write(
            "requests", client=self.client_address[0], method=self.command,
            path=self.path[:2048], status=status, bytes=len(data),
            completed=completed, user_agent=self.headers.get("User-Agent", "")[:512])

    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path.startswith("/document/"):
            return self.reply(302, Location=LANDING)
        if path in ("/", "/index.html", "/main.html", "/1302-1352", "/1302-1352/"):
            return self.reply(302, Location=LANDING)
        if path == "/healthz":
            body = json.dumps(dict(status="ok", assets=len(self.server.assets),
                                   target="PS4 13.52")).encode()
            return self.reply(200, body, "application/json")
        asset = self.server.assets.get(path)
        if asset is None:
            return self.reply(404, b"Not found\n")
        packed, raw, mime = asset
        if accepts_gzip(self.headers.get("Accept-Encoding", "")):
            return self.reply(200, packed, mime, Content_Encoding="gzip", Vary="Accept-Encoding")
        return self.reply(200, raw, mime, Vary="Accept-Encoding")

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        if urlsplit(self.path).path != "/t":
            return self.reply(404, b"Not found\n")
        if self.headers.get("Transfer-Encoding"):
            return self.reply(400, b"Content-Length required\n")
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) != 1:
            return self.reply(411, b"One Content-Length required\n")
        try:
            length = int(lengths[0])
        except ValueError:
            return self.reply(400, b"Invalid Content-Length\n")
        if not 0 <= length <= MAX_BODY:
            return self.reply(413, b"Telemetry body too large\n")
        if self.headers.get_content_type() != "application/x-www-form-urlencoded":
            return self.reply(415, b"Expected form data\n")
        try:
            body = self.rfile.read(length)
            if len(body) != length:
                return self.reply(400, b"Incomplete body\n")
            fields = parse_qs(body.decode("utf-8"), keep_blank_values=True,
                              max_num_fields=16)
        except (TimeoutError, UnicodeDecodeError, ValueError):
            return self.reply(400, b"Invalid telemetry\n")
        self.server.journal.write(
            "telemetry", client=self.client_address[0],
            tag=fields.get("tag", [""])[0], detail=fields.get("detail", [""])[0],
            user_agent=self.headers.get("User-Agent", "")[:512])
        self.reply(204)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8088)
    parser.add_argument("--assets", type=Path, default=ROOT.parent / "esp32-1352")
    parser.add_argument("--logs", type=Path, default=ROOT / "logs")
    args = parser.parse_args()
    host = Host((args.bind, args.port), args.assets, args.logs)
    print(f"PS4 LAN host: http://{args.bind}:{host.server_port}{LANDING}", flush=True)
    print(f"Verified {len(host.assets)} assets; logs: {args.logs}", flush=True)
    try:
        host.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        host.server_close()


if __name__ == "__main__":
    main()
