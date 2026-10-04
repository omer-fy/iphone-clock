"""Serve the desk clock to the iPhone over the local network.

The phone only needs this running to install the app or pick up changes.
After that it runs from its own Application Cache, even with this PC off.

    python serve.py [port]
"""
import http.server
import socket
import sys

from build import PRAYERS_FILE, ROOT, build_manifest, prayer_data

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

# Fetched once at startup (from AlAdhan, by this PC); restart to refresh.
PRAYERS = b''


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        # Never let the browser's normal HTTP cache hold on to stale copies;
        # the Application Cache is the only cache we want.
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def send_body(self, body, content_type):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/clock.appcache':
            self.send_body(build_manifest(PRAYERS), 'text/cache-manifest')
        elif path == '/' + PRAYERS_FILE:
            self.send_body(PRAYERS, 'application/json')
        else:
            super().do_GET()


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        return s.getsockname()[0]
    except OSError:
        return '127.0.0.1'
    finally:
        s.close()


if __name__ == '__main__':
    print('Fetching prayer times...')
    PRAYERS = prayer_data()
    server = http.server.ThreadingHTTPServer(('0.0.0.0', PORT), Handler)
    print('Open on the iPhone:  http://%s:%d/' % (lan_ip(), PORT))
    print('Ctrl+C to stop.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
