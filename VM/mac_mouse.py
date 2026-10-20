"""macOS mouse backend using Apple's Quartz event API via PyObjC."""
import time
import Quartz as Q
import objc


class MacMouse:
    def __init__(self):
        if not Q.CGPreflightPostEventAccess():
            Q.CGRequestPostEventAccess()
            raise PermissionError('Enable Accessibility for Terminal (or the app/Python shown by macOS) in System Settings > Privacy & Security > Accessibility, quit and reopen Terminal, then restart the receiver.')
        self.held = set()
        self.clicks = {}
        self.click_counts = {}

    def position(self):
        event = Q.CGEventCreate(None)
        if event is None:
            raise OSError('Cannot read cursor position. Run in a logged-in Mac desktop session.')
        point = Q.CGEventGetLocation(event)
        return point.x, point.y

    def constrain(self, x, y):
        error, displays, count = Q.CGGetActiveDisplayList(32, None, None)
        if error or not count:
            raise OSError('Cannot find an active Mac display.')
        candidates = []
        for display in displays[:count]:
            bounds = Q.CGDisplayBounds(display)
            px = max(bounds.origin.x, min(x, bounds.origin.x + bounds.size.width - 1))
            py = max(bounds.origin.y, min(y, bounds.origin.y + bounds.size.height - 1))
            candidates.append((px, py))
        return min(candidates, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)

    def post(self, event):
        if event is None:
            raise OSError('macOS could not create a mouse event.')
        Q.CGEventPost(Q.kCGHIDEventTap, event)

    def mouse_event(self, flags, x, y, wheel, unused):
        with objc.autorelease_pool():
            if flags == 0x800:
                self.post(Q.CGEventCreateScrollWheelEvent(None, Q.kCGScrollEventUnitPixel, 1, wheel))
                return
            px, py = self.position()
            if flags == 1:
                point = self.constrain(px + x, py + y)
                if 'left' in self.held:
                    kind, button = Q.kCGEventLeftMouseDragged, Q.kCGMouseButtonLeft
                elif 'right' in self.held:
                    kind, button = Q.kCGEventRightMouseDragged, Q.kCGMouseButtonRight
                else:
                    kind, button = Q.kCGEventMouseMoved, Q.kCGMouseButtonLeft
                event = Q.CGEventCreateMouseEvent(None, kind, point, button)
            else:
                name, down, kind, button = {
                    2: ('left', True, Q.kCGEventLeftMouseDown, Q.kCGMouseButtonLeft),
                    4: ('left', False, Q.kCGEventLeftMouseUp, Q.kCGMouseButtonLeft),
                    8: ('right', True, Q.kCGEventRightMouseDown, Q.kCGMouseButtonRight),
                    16: ('right', False, Q.kCGEventRightMouseUp, Q.kCGMouseButtonRight),
                }[flags]
                event = Q.CGEventCreateMouseEvent(None, kind, (px, py), button)
                if event is None:
                    raise OSError('macOS could not create a button event.')
                if down:
                    now = time.monotonic()
                    last, lx, ly, count = self.clicks.get(name, (-100, px, py, 0))
                    count = count + 1 if now - last <= .4 and abs(px - lx) <= 4 and abs(py - ly) <= 4 else 1
                    self.clicks[name] = (now, px, py, count)
                    self.click_counts[name] = count
                Q.CGEventSetIntegerValueField(event, Q.kCGMouseEventClickState, self.click_counts.get(name, 1))
                self.post(event)
                if down:
                    self.held.add(name)
                else:
                    self.held.discard(name)
                return
            self.post(event)

    def close(self):
        for name in list(self.held):
            self.mouse_event(4 if name == 'left' else 16, 0, 0, 0, 0)
