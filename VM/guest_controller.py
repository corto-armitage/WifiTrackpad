"""Open a host pairing URL in the guest's default browser. No mouse injection."""
import argparse
import ipaddress
from urllib.parse import urlsplit
import webbrowser


def pairing_url(value):
    try:
        url = urlsplit(value)
        ip = ipaddress.IPv4Address(url.hostname)
        if (url.scheme != 'http' or url.username or url.password or
                url.path not in ('', '/') or url.query or not url.fragment or
                not url.port or ip.is_unspecified or ip.is_multicast):
            raise ValueError()
    except (ValueError, TypeError):
        raise argparse.ArgumentTypeError('Use the full http://HOST-IP:PORT/#CODE address printed by the host receiver.')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', nargs='?', type=pairing_url)
    args = parser.parse_args()
    url = args.url
    if not url:
        try:
            url = pairing_url(input('Paste the host pairing address: ').strip())
        except argparse.ArgumentTypeError as error:
            parser.error(str(error))
    if not webbrowser.open(url):
        parser.exit(1, 'Could not open a browser. Open the pairing address manually in a browser inside the guest.\n')


if __name__ == '__main__':
    main()
