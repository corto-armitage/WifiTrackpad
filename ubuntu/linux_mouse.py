"""Virtual mouse using Linux uinput (no third-party Python packages)."""
import fcntl
import os
import struct
import time


class LinuxMouse:
    def __init__(self):
        self.fd = os.open('/dev/uinput', os.O_WRONLY | os.O_NONBLOCK)
        self.scroll_remainder = 0
        try:
            for event in (1, 2):  # EV_KEY, EV_REL
                fcntl.ioctl(self.fd, 0x40045564, event)
            for button in (0x110, 0x111):  # BTN_LEFT, BTN_RIGHT
                fcntl.ioctl(self.fd, 0x40045565, button)
            for axis in (0, 1, 8):  # REL_X, REL_Y, REL_WHEEL
                fcntl.ioctl(self.fd, 0x40045566, axis)
            setup = struct.pack('@HHHH80sI', 3, 0x1234, 0x5678, 1,
                                b'WiFi Trackpad virtual mouse', 0)
            fcntl.ioctl(self.fd, 0x405C5503, setup)  # UI_DEV_SETUP
            fcntl.ioctl(self.fd, 0x5501)  # UI_DEV_CREATE
            time.sleep(1)  # Allow the desktop to discover the mouse.
        except BaseException:
            os.close(self.fd)
            self.fd = None
            raise

    def emit(self, kind, code, value):
        os.write(self.fd, struct.pack('@llHHi', 0, 0, kind, code, value))

    def mouse_event(self, flags, x, y, wheel, unused):
        if flags == 1:
            self.emit(2, 0, x)
            self.emit(2, 1, y)
        elif flags == 0x800:
            # Browser pixel deltas accumulate into wheel detents. Preserve
            # small trackpad deltas instead of rounding every request to zero.
            self.scroll_remainder += wheel
            steps = int(self.scroll_remainder / 100)
            self.scroll_remainder -= steps * 100
            if steps:
                self.emit(2, 8, steps)
        else:
            button, down = {2: (0x110, 1), 4: (0x110, 0),
                            8: (0x111, 1), 16: (0x111, 0)}[flags]
            self.emit(1, button, down)
        self.emit(0, 0, 0)  # SYN_REPORT

    def close(self):
        if self.fd is not None:
            try:
                fcntl.ioctl(self.fd, 0x5502)  # UI_DEV_DESTROY
            finally:
                os.close(self.fd)
                self.fd = None
