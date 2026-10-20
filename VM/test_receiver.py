import io
import json
import unittest
from unittest.mock import Mock
import host_receiver as receiver


class HTTPTests(unittest.TestCase):
    def setUp(self):
        receiver.ALLOWED_GUEST = '192.168.1.25'
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

    def test_other_guest_rejected_even_with_valid_token(self):
        receiver.ALLOWED_GUEST = '192.168.1.99'
        self.assertEqual(self.request([{'type': 'down', 'button': 'left'}]), 403)
        receiver.MOUSE.mouse_event.assert_not_called()

    def test_malformed_events_rejected(self):
        self.assertEqual(self.request(['not an event']), 400)
        receiver.MOUSE.mouse_event.assert_not_called()

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
