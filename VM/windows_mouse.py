"""Native Windows mouse backend; no third-party packages."""
import ctypes


class WindowsMouse:
    def __init__(self):
        self.native = ctypes.windll.user32
        self.native.mouse_event.argtypes = [ctypes.c_ulong, ctypes.c_ulong,
                                           ctypes.c_ulong, ctypes.c_ulong, ctypes.c_size_t]

    def mouse_event(self, flags, x, y, wheel, unused):
        self.native.mouse_event(flags, x, y, wheel, unused)

    def close(self):
        pass  # The receiver releases held buttons before closing.
