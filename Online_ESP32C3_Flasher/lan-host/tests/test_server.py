import gzip
import hashlib
import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server import Host


class HostTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.host = Host(("127.0.0.1", 0), ROOT.parent / "esp32-1352", cls.temp.name)
        cls.worker = threading.Thread(target=cls.host.serve_forever, daemon=True)
        cls.worker.start()

    @classmethod
    def tearDownClass(cls):
        cls.host.shutdown()
        cls.host.server_close()
        cls.worker.join()
        cls.temp.cleanup()

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.host.server_port, timeout=3)
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        conn.close()
        return result

    def test_all_payloads_and_web_assets_match_manifest_over_http(self):
        manifest = json.loads((ROOT.parent / "esp32-1352/generated/asset-manifest.json").read_text())
        for item in manifest["assets"]:
            with self.subTest(route=item["route"]):
                status, headers, body = self.request("GET", item["route"], headers={"Accept-Encoding": "gzip"})
                self.assertEqual(status, 200)
                self.assertEqual(headers["Content-Encoding"], "gzip")
                self.assertEqual(int(headers["Content-Length"]), len(body))
                self.assertEqual(hashlib.sha256(gzip.decompress(body)).hexdigest(), item["sha256"])

    def test_query_head_and_no_gzip(self):
        path = "/1302-1352/core.js?v=10"
        status, headers, body = self.request("GET", path, headers={"Accept-Encoding": "gzip;q=0"})
        self.assertEqual(status, 200)
        self.assertNotIn("Content-Encoding", headers)
        self.assertEqual(body, self.host.assets["/1302-1352/core.js"][1])
        status, headers, body = self.request("HEAD", path)
        self.assertEqual(status, 200)
        self.assertGreater(int(headers["Content-Length"]), 0)
        self.assertEqual(body, b"")

    def test_root_and_missing_resources(self):
        status, headers, _ = self.request("GET", "/document/sw/ps4/index.html", headers={"Host": "manuals.playstation.net"})
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], "/1302-1352/index.html")
        status, headers, _ = self.request("GET", "/")
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], "/1302-1352/index.html")
        for path in ("/../../README.md", "/%2e%2e/README.md", "/1302-1352/missing.js", "/logs/"):
            self.assertEqual(self.request("GET", path)[0], 404)

    def test_telemetry_is_saved_as_json(self):
        detail = "test med åäö och rad\n2"
        body = urlencode({"PS4-JB": "", "tag": "LOCAL-TEST", "detail": detail})
        status, _, _ = self.request("POST", "/t", body, {"Content-Type": "application/x-www-form-urlencoded"})
        self.assertEqual(status, 204)
        records = [json.loads(line) for file in Path(self.temp.name).glob("telemetry-*.jsonl")
                   for line in file.read_text().splitlines()]
        self.assertTrue(any(r["tag"] == "LOCAL-TEST" and r["detail"] == detail for r in records))
        self.assertEqual(self.request("POST", "/t", b"x" * 65537,
                                     {"Content-Type": "application/x-www-form-urlencoded"})[0], 413)
        self.assertEqual(self.request("POST", "/t", "{}", {"Content-Type": "application/json"})[0], 415)


if __name__ == "__main__":
    unittest.main()
