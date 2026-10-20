"""Windows mouse receiver. Python 3.10+, standard library only."""
import argparse
import ctypes
import hmac
import json
import math
import os
from pathlib import Path
import secrets
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGE = Path(__file__).with_name('controller.html')
LOCK = threading.Lock()
OWNER = None
LAST = 0
HELD = set()
TOKEN = secrets.token_urlsafe(24)
USER32 = None


def release():
    for button in list(HELD):
        USER32.mouse_event(4 if button == 'left' else 16, 0, 0, 0, 0)
    HELD.clear()


def number(data, key, limit):
    value = data.get(key, 0)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Invalid number')
    return round(max(-limit, min(limit, value)))


def watchdog():
    global OWNER
    while True:
        time.sleep(.25)
        with LOCK:
            if OWNER and time.monotonic() - LAST > 3:
                release()
                OWNER = None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Never log pairing credentials.

    def reply(self, code, body=b'', kind='application/json'):
        self.send_response(code)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/':
            self.reply(200, PAGE.read_bytes(), 'text/html; charset=utf-8')
        else:
            self.reply(404)

    def do_POST(self):
        global OWNER, LAST
        if self.path != '/input':
            return self.reply(404)
        if not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + TOKEN):
            return self.reply(401)
        # Reject cross-origin browser requests, including DNS-rebinding hosts.
        if self.headers.get('Origin') != 'http://' + self.headers.get('Host', ''):
            return self.reply(403)
        try:
            self.connection.settimeout(3)
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 8192:
                return self.reply(413)
            data = json.loads(self.rfile.read(length))
            client = data['client']
            events = data['events']
            if not isinstance(client, str) or not 16 <= len(client) <= 100 or not isinstance(events, list) or len(events) > 100:
                raise ValueError()
            # Validate the entire batch before applying any input.
            clean = []
            for event in events:
                kind = event['type']
                if kind == 'move':
                    clean.append((kind, number(event, 'x', 2000), number(event, 'y', 2000)))
                elif kind == 'scroll':
                    clean.append((kind, number(event, 'y', 1200)))
                elif kind in ('down', 'up') and event.get('button') in ('left', 'right'):
                    clean.append((kind, event['button']))
                elif kind == 'release':
                    clean.append((kind,))
                else:
                    raise ValueError()
            with LOCK:
                if OWNER and OWNER != client and time.monotonic() - LAST <= 3:
                    return self.reply(409)
                OWNER, LAST = client, time.monotonic()
                for event in clean:
                    kind = event[0]
                    if kind == 'move':
                        USER32.mouse_event(1, event[1], event[2], 0, 0)
                    elif kind == 'scroll':
                        USER32.mouse_event(0x800, 0, 0, event[1], 0)
                    elif kind == 'release':
                        release()
                    else:
                        button = event[1]
                        if kind == 'down' and button not in HELD:
                            USER32.mouse_event(2 if button == 'left' else 8, 0, 0, 0, 0)
                            HELD.add(button)
                        elif kind == 'up' and button in HELD:
                            USER32.mouse_event(4 if button == 'left' else 16, 0, 0, 0, 0)
                            HELD.remove(button)
            self.reply(200, b'{}')
        except (ValueError, KeyError, TypeError, OSError):
            self.reply(400)


def main():
    global USER32
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    if os.name != 'nt':
        parser.error('Run the receiver on the Windows PC you want to control.')
    USER32 = ctypes.windll.user32
    USER32.mouse_event.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_size_t]
    server = ThreadingHTTPServer(('0.0.0.0', args.port), Handler)
    server.daemon_threads = True
    addresses = set(socket.gethostbyname_ex(socket.gethostname())[2])
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(('192.0.2.1', 80))
            addresses.add(sock.getsockname()[0])
    except OSError:
        pass
    print('\nWiFi Trackpad — leave this window open. Ctrl+C stops control.\n')
    for address in sorted(addresses):
        if not address.startswith('127.'):
            print(f'Open on laptop: http://{address}:{args.port}/#{TOKEN}')
    print('\nUse a trusted private WiFi network. Pairing expires when this program stops.')
    threading.Thread(target=watchdog, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        with LOCK:
            release()


if __name__ == '__main__':
    main()
