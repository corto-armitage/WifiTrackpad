# WiFi Trackpad for macOS

Control a Mac's cursor from a Windows, Linux, or Mac laptop using a browser and trackpad. Run these files on the Mac you want to control. Both computers must share a trusted private network.

## First-time setup on the Mac

Install Python 3.10 or newer from python.org if needed. This version is intended for macOS 11 or newer on Apple Silicon or Intel; use a Python build compatible with your macOS version. Extract the package, open Terminal in this folder, and run:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python receiver.py
```

macOS requires permission to post mouse events. If the receiver stops with an Accessibility message, open **System Settings > Privacy & Security > Accessibility**, enable Terminal (or the app/Python executable named by the permission prompt), then quit and reopen Terminal and run the receiver again. On older macOS versions this panel is in System Preferences > Security & Privacy > Privacy. Permissions must be granted locally on the Mac; the program does not bypass them. Do not use sudo.

If macOS asks about incoming network connections or Local Network access for Terminal/Python, allow it on your trusted network. Screen Recording and Input Monitoring are not required by this implementation.

## Start and connect

On the Mac, run:

```bash
.venv/bin/python receiver.py
```

Optionally, run `chmod +x 'Start Receiver.command'` once, then double-click that launcher on subsequent runs. Keep the Terminal window open.

On the controlling laptop, open the **complete HTTP address printed by the Mac receiver**, including the `#` pairing code, and click Connect. Do not open the downloaded controller.html file. If several addresses are printed, use the Mac's WiFi/Ethernet IPv4 address from its network settings. The controller needs only a modern desktop browser.

Move over the large pad to control the Mac. Left/right clicks, double clicks, vertical scrolling, dragging, and speed adjustment are included. Capture cursor enables continuous movement where supported; press Esc to leave capture. Multiple displays use Quartz global coordinates, including monitors positioned to the left or above the main display.

Press Ctrl+C in Terminal to stop, or Disconnect in the browser. Lost connections release held buttons within about three seconds. Each receiver restart generates a new pairing address. To use a different port: `.venv/bin/python receiver.py --port 8766`.

## Limits and security

Use a logged-in, unlocked Mac desktop session. This does not provide screen sharing, keyboard control, login/unlock control, or permission-dialog bypass. Local HTTP is unencrypted; anyone with the pairing address can control the mouse while the receiver is running. Use trusted private WiFi only, and do not expose the port through your router. One controller is accepted at a time.

The Mac receiver uses PyObjC's Quartz bridge rather than the Windows or Linux input backend. Python dependencies install only on the Mac. Permission checks, event creation, dragging, clicks, scrolling, display bounds, and shared receiver request handling have simulated tests. Actual macOS Accessibility behavior and hardware cursor movement still require verification on a Mac.

References: [Apple mouse event API](https://developer.apple.com/documentation/coregraphics/1454356-cgeventcreatemouseevent), [Apple event posting API](https://developer.apple.com/documentation/coregraphics/cgevent/post(tap:)), [PyObjC Quartz bindings](https://pyobjc.readthedocs.io/en/latest/apinotes/Quartz.html).
