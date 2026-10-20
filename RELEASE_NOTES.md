# WiFi Trackpad v1.0.0

Use a laptop trackpad to control the mouse on another Windows or Ubuntu computer over the same trusted WiFi network.

Run the Python receiver on the computer you want to control, then open its complete pairing address in a browser on the controlling computer. The browser sends movement, clicks, dragging, and scrolling to the receiver. On Windows, the receiver sends mouse events through the Windows API. On Ubuntu, it creates a virtual mouse through Linux uinput, designed for Wayland and X11 desktops.

## Choose a package

- **WiFiTrackpad-Windows-v1.0.0.zip**: receiver for a Windows computer. Install Python 3.10+ and run Start Receiver.cmd.
- **WiFiTrackpad-Ubuntu-v1.0.0.zip**: receiver for an Ubuntu computer. Run `sudo bash setup-ubuntu.sh` once, log out and back in, then run `python3 receiver.py` without sudo.

The controlling Windows computer needs only a modern browser. Open the HTTP pairing address printed by the receiver; do not open controller.html directly.

## Included

- Cursor movement, left/right clicks, dragging, vertical scrolling, and adjustable speed.
- Optional cursor capture with Esc to exit.
- Random pairing credentials and one controller at a time.
- Automatic release of held buttons after a lost connection.
- No third-party Python dependencies.

Use only on trusted private networks: local HTTP traffic is unencrypted. This is mouse control, not screen sharing or keyboard forwarding. Four simulated Ubuntu tests passed, and the Ubuntu version was reported working by the user; broad hardware and desktop testing has not been performed.
