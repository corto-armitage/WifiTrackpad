# WiFi Trackpad: Windows controls Ubuntu

Run the receiver on the Ubuntu computer whose cursor you want to move. Open its pairing address in a browser on the Windows computer. Both computers must share a trusted private network. No Windows installation or third-party Python packages are needed.

## Ubuntu setup (once)

Keep all files in this folder together. In an Ubuntu terminal opened in this folder, run:

```bash
sudo bash setup-ubuntu.sh
```

Log out of Ubuntu completely and log back in so your new group membership takes effect. The setup script enables the kernel uinput module and grants your account access through a dedicated wifi-trackpad group. This permission allows creation of virtual input devices. It does not add you to the broader input group or grant access to physical keyboard events. Python 3.10+ is required; if missing, install it with `sudo apt install python3`.

## Each time

On Ubuntu, run as your normal user:

```bash
python3 receiver.py
```

Keep the terminal open. On Windows, open the **complete HTTP address** printed by the receiver, including the `#` pairing code. Do not open the downloaded controller.html file. Click Connect, then move your trackpad pointer over the large pad. Clicks, right-clicks, vertical scrolling, and Start/End drag are supported. Capture cursor allows continuous movement when your browser supports pointer lock over local HTTP; Esc leaves capture.

If several addresses are listed, use the IPv4 address for Ubuntu's active WiFi or Ethernet connection, visible in Settings → Network/Wi-Fi → connection details. Do not use Windows' own address, loopback, VPN, or container addresses. Restarting the receiver changes its pairing code.

If Ubuntu's UFW firewall is active, allow only your Windows computer's address (replace the example):

```bash
sudo ufw allow from 192.168.1.25 to any port 8765 proto tcp
```

Do not disable your firewall. Guest WiFi/client isolation and VPN routing may prevent connections. Allow browser local-network access if prompted. To choose a different port, run `python3 receiver.py --port 8766` and adjust the firewall rule.

## Compatibility and stopping

This receiver creates a virtual Linux mouse through uinput and is designed for Ubuntu desktop sessions using either Wayland or X11. No DISPLAY setting or X11 automation tool is used. A graphical Ubuntu desktop and kernel uinput support are required; containers, WSL, and headless systems are outside this version's scope. There is no screen sharing or keyboard forwarding. Natural scrolling and mouse acceleration follow the Ubuntu desktop's settings.

Disconnect in the browser or press Ctrl+C in the receiver terminal. Lost connections release held buttons within approximately three seconds. Only one controller session is accepted at a time. Use trusted private WiFi only: HTTP traffic is unencrypted, and anyone with the pairing address can operate the mouse while the receiver runs. Do not expose the port to the internet.

If you get permission denied for /dev/uinput, finish setup and log out/back in, then check `id -nG` includes wifi-trackpad. Do not run the network receiver with sudo.

## Remove setup

Stop the receiver. Remove your account from wifi-trackpad with `sudo gpasswd -d "$USER" wifi-trackpad`, then remove `/etc/udev/rules.d/99-wifi-trackpad.rules` and `/etc/modules-load.d/wifi-trackpad.conf` using sudo. Reboot to discard the active device permissions and group membership. Do not remove the group if other accounts still use this program.

## Validation

The virtual input encoding and receiver HTTP behavior are checked with a simulated device. Actual cursor movement, desktop discovery, and setup permissions must still be checked on an Ubuntu machine. Test clicks, drag, scrolling, loss of connection while dragging, and rejection of an old pairing code after restart before relying on it.

Implementation reference: [Linux kernel uinput documentation](https://docs.kernel.org/input/uinput.html).
