"""Static file server with HTTP Range support (so review videos can be scrubbed). Usage: range_server.py <dir> <port>"""
import os, re, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial

class H(SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path.split("?")[0])
        rng = self.headers.get("Range")
        if not rng or not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path); m = re.match(r"bytes=(\d*)-(\d*)", rng)
        start = int(m.group(1)) if m.group(1) else size - int(m.group(2))
        end = int(m.group(2)) if m.group(1) and m.group(2) else size - 1
        end = min(end, size - 1); f = open(path, "rb"); f.seek(start)
        self.send_response(206); self.send_header("Content-type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes"); self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1)); self.send_header("Cache-Control", "no-cache"); self.end_headers()
        self._remaining = end - start + 1
        return f
    def copyfile(self, src, dst):
        n = getattr(self, "_remaining", None)
        if n is None:
            return super().copyfile(src, dst)
        while n > 0:
            b = src.read(min(1 << 20, n))
            if not b:
                break
            try:
                dst.write(b)
            except (BrokenPipeError, ConnectionResetError):
                break
            n -= len(b)
    def end_headers(self):
        if not self.headers.get("Range"):
            self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

ThreadingHTTPServer(("", int(sys.argv[2])), partial(H, directory=sys.argv[1])).serve_forever()
