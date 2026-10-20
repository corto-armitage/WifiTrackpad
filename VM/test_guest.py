import argparse
import unittest
from guest_controller import pairing_url


class GuestTests(unittest.TestCase):
    def test_pairing_address(self):
        url = 'http://192.168.56.1:8767/#test-token'
        self.assertEqual(pairing_url(url), url)

    def test_reject_invalid_addresses(self):
        for url in ['file:///tmp/controller.html', 'https://example.com/#token',
                    'http://192.168.56.1:8767/', 'http://user:pass@192.168.56.1:8767/#token',
                    'http://0.0.0.0:8767/#token', 'http://192.168.56.1:99999/#token']:
            with self.subTest(url=url), self.assertRaises(argparse.ArgumentTypeError):
                pairing_url(url)
