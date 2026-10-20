"""Simulated Quartz tests; never posts real mouse events."""
import contextlib
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


class MacMouseTests(unittest.TestCase):
    def setUp(self):
        self.q = types.SimpleNamespace()
        names = ['kCGHIDEventTap', 'kCGScrollEventUnitPixel', 'kCGEventLeftMouseDragged',
                 'kCGEventRightMouseDragged', 'kCGEventMouseMoved', 'kCGMouseButtonLeft',
                 'kCGMouseButtonRight', 'kCGEventLeftMouseDown', 'kCGEventLeftMouseUp',
                 'kCGEventRightMouseDown', 'kCGEventRightMouseUp', 'kCGMouseEventClickState']
        for i, name in enumerate(names):
            setattr(self.q, name, i)
        for name in ['CGPreflightPostEventAccess', 'CGRequestPostEventAccess',
                     'CGEventCreate', 'CGEventCreateMouseEvent', 'CGEventCreateScrollWheelEvent',
                     'CGEventSetIntegerValueField', 'CGEventPost']:
            setattr(self.q, name, Mock(return_value=object()))
        self.q.CGEventGetLocation = Mock(return_value=types.SimpleNamespace(x=100, y=100))
        self.q.CGGetActiveDisplayList = Mock(return_value=(0, [1, 2], 2))
        def bounds(display):
            return types.SimpleNamespace(origin=types.SimpleNamespace(x=0 if display == 1 else -1000, y=0),
                                         size=types.SimpleNamespace(width=1000, height=800))
        self.q.CGDisplayBounds = Mock(side_effect=bounds)
        spec = importlib.util.spec_from_file_location('fake_mac_backend', Path(__file__).with_name('mac_mouse.py'))
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'Quartz': self.q, 'objc': types.SimpleNamespace(autorelease_pool=contextlib.nullcontext)}):
            spec.loader.exec_module(module)
        self.module = module
        self.mouse = module.MacMouse()

    def test_permission_denied_requests_permission(self):
        self.q.CGPreflightPostEventAccess.return_value = False
        with self.assertRaises(PermissionError):
            self.module.MacMouse()
        self.q.CGRequestPostEventAccess.assert_called_once()

    def test_movement_and_monitor_edges(self):
        self.mouse.mouse_event(1, -150, 5, 0, 0)
        self.q.CGEventCreateMouseEvent.assert_called_with(None, self.q.kCGEventMouseMoved, (-50, 105), self.q.kCGMouseButtonLeft)
        self.assertEqual(self.mouse.constrain(-5000, 3000), (-1000, 799))

    def test_drag_release_and_right_drag(self):
        self.mouse.mouse_event(2, 0, 0, 0, 0)
        self.mouse.mouse_event(1, 3, 4, 0, 0)
        self.q.CGEventCreateMouseEvent.assert_called_with(None, self.q.kCGEventLeftMouseDragged, (103, 104), self.q.kCGMouseButtonLeft)
        self.mouse.close()
        self.assertFalse(self.mouse.held)
        self.mouse.mouse_event(8, 0, 0, 0, 0)
        self.mouse.mouse_event(1, 3, 4, 0, 0)
        self.q.CGEventCreateMouseEvent.assert_called_with(None, self.q.kCGEventRightMouseDragged, (103, 104), self.q.kCGMouseButtonRight)

    def test_double_click_and_scroll(self):
        for flag in [2, 4, 2, 4]:
            self.mouse.mouse_event(flag, 0, 0, 0, 0)
        self.assertEqual(self.q.CGEventSetIntegerValueField.call_args.args[2], 2)
        self.mouse.mouse_event(0x800, 0, 0, -30, 0)
        self.q.CGEventCreateScrollWheelEvent.assert_called_with(None, self.q.kCGScrollEventUnitPixel, 1, -30)

    def test_failed_event_does_not_hold_button(self):
        self.q.CGEventCreateMouseEvent.return_value = None
        with self.assertRaises(OSError):
            self.mouse.mouse_event(2, 0, 0, 0, 0)
        self.assertFalse(self.mouse.held)


if __name__ == '__main__':
    unittest.main()
