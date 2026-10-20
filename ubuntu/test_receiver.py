"""No real mouse events: run python3 -m unittest -v test_receiver.py."""
import io
import json
import struct
import sys
import types
import unittest
from unittest.mock import Mock, patch

if sys.platform != 'linux':
    sys.modules.setdefault('fcntl', types.SimpleNamespace(ioctl=Mock()))
import linux_mouse
import receiver


class MouseTests(unittest.TestCase):
    def test_device_and_events(self):
        writes = []
        with patch.object(linux_mouse.os, 'open', return_value=42), \
             patch.object(linux_mouse.os, 'O_NONBLOCK', 2048, create=True), \
             patch.object(linux_mouse.os, 'write', side_effect=lambda fd, b: writes.append(b)), \
             patch.object(linux_mouse.os, 'close') as close, \
             patch.object(linux_mouse.fcntl, 'ioctl') as ioctl, \
             patch.object(linux_mouse.time, 'sleep'):
            mouse = linux_mouse.LinuxMouse()
            setup = ioctl.call_args_list[-2].args[2]
            self.assertEqual(len(setup), 92)
            self.assertEqual(struct.unpack('@HHHH80sI', setup)[4].rstrip(b'\0'), b'WiFi Trackpad virtual mouse')
            mouse.mouse_event(1, -20, 15, 0, 0)
            mouse.mouse_event(2, 0, 0, 0, 0)
            mouse.mouse_event(4, 0, 0, 0, 0)
            mouse.mouse_event(8, 0, 0, 0, 0)
            mouse.mouse_event(16, 0, 0, 0, 0)
            for _ in range(4):
                mouse.mouse_event(0x800, 0, 0, -30, 0)
            events = [struct.unpack('@llHHi', b)[2:] for b in writes]
            self.assertIn((2, 0, -20), events)
            self.assertIn((2, 1, 15), events)
            for button in (0x110, 0x111):
                for value in (0, 1):
                    self.assertIn((1, button, value), events)
            self.assertEqual([e for e in events if e[:2] == (2, 8)], [(2, 8, -1)])
            self.assertEqual(mouse.scroll_remainder, -20)
            mouse.close()
            mouse.close()
            close.assert_called_once_with(42)
            ioctl.assert_called_with(42, 0x5502)


class HTTPTests(unittest.TestCase):
    def setUp(self):
        receiver.MOUSE = Mock()
        receiver.OWNER = None
        receiver.HELD.clear()
        self.host = '192.168.1.20:8765'

    def request(self, events, client='a' * 32, token=None, origin=None):
        body = json.dumps({'client': client, 'events': events}).encode()
        headers = {'Host': self.host,
                   'Authorization': 'Bearer ' + (receiver.TOKEN if token is None else token),
                   'Origin': 'http://' + self.host if origin is None else origin,
                   'Content-Type': 'application/json', 'Content-Length': str(len(body))}
        wire = ('POST /input HTTP/1.0\r\n' + ''.join(f'{k}: {v}\r\n' for k, v in headers.items()) + '\r\n').encode() + body
        connection = Mock()
        connection.makefile.return_value = io.BytesIO(wire)
        output = bytearray()
        connection.sendall.side_effect = output.extend
        receiver.Handler(connection, ('192.168.1.25', 1234), Mock())
        return int(output.split(b'\r\n', 1)[0].split()[1])

    def test_pairing_origin_and_single_controller(self):
        self.assertEqual(self.request([], token='incorrect'), 401)
        self.assertEqual(self.request([], origin='http://elsewhere'), 403)
        self.assertEqual(self.request([]), 200)
        self.assertEqual(self.request([], client='b' * 32), 409)

    def test_move_drag_release_and_expired_session(self):
        self.assertEqual(self.request([{'type': 'move', 'x': -10, 'y': 5},
                                       {'type': 'down', 'button': 'left'}]), 200)
        receiver.MOUSE.mouse_event.assert_any_call(1, -10, 5, 0, 0)
        self.assertEqual(receiver.HELD, {'left'})
        receiver.LAST -= 4
        self.assertEqual(self.request([], client='b' * 32), 200)
        self.assertFalse(receiver.HELD)
        receiver.MOUSE.mouse_event.assert_any_call(4, 0, 0, 0, 0)
        self.assertEqual(self.request([{'type': 'down', 'button': 'right'},
                                       {'type': 'release'}], client='b' * 32), 200)
        self.assertFalse(receiver.HELD)

    def test_batch_validation_applies_no_partial_input(self):
        self.assertEqual(self.request([{'type': 'down', 'button': 'left'},
                                       {'type': 'move', 'x': 'bad'}]), 400)
        receiver.MOUSE.mouse_event.assert_not_called()


if __name__ == '__main__':
    unittest.main()
