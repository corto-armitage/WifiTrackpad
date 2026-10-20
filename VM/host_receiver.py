"""Explicit host mouse receiver for a trusted virtual machine. Python 3.10+."""
import argparse
import ipaddress
import sys
import hmac
import json
import math
from pathlib import Path
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGE = Path(__file__).with_name('controller.html')
LOCK = threading.Lock()
OWNER = None
LAST = 0
HELD = set()
TOKEN = secrets.token_urlsafe(24)
MOUSE = None
ALLOWED_GUEST = None


def release():
    for button in list(HELD):
        MOUSE.mouse_event(4 if button == 'left' else 16, 0, 0, 0, 0)
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
        if self.client_address[0] != ALLOWED_GUEST:
            return self.reply(403)
        if self.path == '/':
            self.reply(200, PAGE.read_bytes(), 'text/html; charset=utf-8')
        else:
            self.reply(404)

    def do_POST(self):
        global OWNER, LAST
        if self.client_address[0] != ALLOWED_GUEST:
            return self.reply(403)
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
            if not isinstance(data, dict):
                raise ValueError()
            client = data['client']
            events = data['events']
            if not isinstance(client, str) or not 16 <= len(client) <= 100 or not isinstance(events, list) or len(events) > 100:
                raise ValueError()
            # Validate the entire batch before applying any input.
            clean = []
            for event in events:
                if not isinstance(event, dict):
                    raise ValueError()
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
                if OWNER and (OWNER != client or time.monotonic() - LAST > 3):
                    release()
                OWNER, LAST = client, time.monotonic()
                for event in clean:
                    kind = event[0]
                    if kind == 'move':
                        MOUSE.mouse_event(1, event[1], event[2], 0, 0)
                    elif kind == 'scroll':
                        MOUSE.mouse_event(0x800, 0, 0, event[1], 0)
                    elif kind == 'release':
                        release()
                    else:
                        button = event[1]
                        if kind == 'down' and button not in HELD:
                            MOUSE.mouse_event(2 if button == 'left' else 8, 0, 0, 0, 0)
                            HELD.add(button)
                        elif kind == 'up' and button in HELD:
                            MOUSE.mouse_event(4 if button == 'left' else 16, 0, 0, 0, 0)
                            HELD.remove(button)
            self.reply(200, b'{}')
        except (ValueError, KeyError, TypeError, OSError):
            self.reply(400)


def main():
    global MOUSE, ALLOWED_GUEST
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8767)
    parser.add_argument('--bind', required=True, help='Host IPv4 address on the network shared with the guest')
    parser.add_argument('--guest', required=True, help='Guest IPv4 address as seen by the host (only this peer may connect)')
    args = parser.parse_args()
    try:
        bind = ipaddress.IPv4Address(args.bind)
        guest = ipaddress.IPv4Address(args.guest)
        if bind.is_unspecified or bind.is_multicast or guest.is_unspecified or guest.is_multicast:
            raise ValueError()
        if not 1 <= args.port <= 65535:
            raise ValueError()
    except ValueError:
        parser.error('Provide specific IPv4 addresses and a port from 1 to 65535.')
    ALLOWED_GUEST = str(guest)
    try:
        if sys.platform == 'win32':
            from windows_mouse import WindowsMouse
            MOUSE = WindowsMouse()
        elif sys.platform == 'linux':
            from linux_mouse import LinuxMouse
            MOUSE = LinuxMouse()
        elif sys.platform == 'darwin':
            from mac_mouse import MacMouse
            MOUSE = MacMouse()
        else:
            parser.error('Supported hosts: Windows, Ubuntu desktop, and macOS.')
    except (OSError, ImportError) as error:
        parser.exit(1, f'Cannot enable host mouse control: {error}. See README.md for host setup.\n')
    try:
        server = ThreadingHTTPServer((str(bind), args.port), Handler)
    except OSError as error:
        MOUSE.close()
        parser.exit(1, f'Cannot listen on port {args.port}: {error}\n')
    server.daemon_threads = True
    print(f'\nHost cursor control enabled for guest {ALLOWED_GUEST}. Ctrl+C stops control.')
    print(f'Open INSIDE THE GUEST: http://{bind}:{args.port}/#{TOKEN}')
    print('Keep the host terminal open. Pairing expires when the receiver stops.')
    threading.Thread(target=watchdog, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        with LOCK:
            release()
            MOUSE.close()


if __name__ == '__main__':
    main()
