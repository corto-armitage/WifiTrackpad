# WiFi Trackpad

Control a Windows PC mouse using a laptop trackpad over the same private WiFi. The PC runs `receiver.py`; the laptop runs the included controller in its browser. No Python packages are required.

## Start

1. On the PC, install Python 3.10 or newer if needed, including its Windows launcher. Keep all these files in the same folder.
2. Double-click **Start Receiver.cmd**, or run `py -3 receiver.py` from this folder.
3. If Windows Firewall asks, allow Python on **Private networks only**. Do not disable the firewall. If no prompt appears and the laptop cannot connect, allow inbound TCP port 8765 for Python on the private network profile in Windows Firewall.
4. Copy one complete address printed by the receiver, including the `#` and pairing code, into your laptop browser. Try another printed address if the first does not connect.
5. Click **Connect**. Move your laptop pointer over the large pad. Use your trackpad's normal click, right-click, and two-finger scroll gestures.

**Capture cursor** enables continuous movement if the browser permits pointer lock over the local HTTP connection. Press **Esc** to exit. Normal movement over the pad works without capture. **Start drag** holds the PC's left mouse button while you move; **End drag** releases it. The click buttons provide alternatives to trackpad gestures. Adjust Speed as needed.

Click **Disconnect** to stop laptop input. Press **Ctrl+C** in the PC receiver window to shut down the receiver and invalidate its pairing code. A stalled or closed laptop connection releases held mouse buttons within approximately 3 seconds.

## Network and security

Use only a trusted home/private network. Input and the pairing credential travel over local HTTP without encryption. Anyone who obtains the full pairing address can control the mouse while the receiver runs. A fresh random credential is generated at each start, is omitted from request logs, and is removed from the browser address bar after loading. Do not forward this port through your router or expose it to the internet. Only one controller session is accepted at a time; an inactive session expires after 3 seconds.

The receiver listens on all PC network interfaces. Guest WiFi, wireless client isolation, VPNs, or a public Windows network profile may block connections. Connect both computers to the same private LAN. If port 8765 is occupied, run `py -3 receiver.py --port 8766` and use the address it prints.

## Scope and limitations

The receiver supports Windows; the laptop can use any desktop OS with a modern browser and trackpad. There is no screen sharing: you need to see the PC display. This version controls the mouse only. It cannot control Windows sign-in, UAC secure-desktop prompts, or some elevated applications. Run it as a normal user. Horizontal scrolling and custom multi-finger gestures are not forwarded. Local HTTP pointer capture support varies by browser; the pad remains the fallback.

## Verification checklist

Before relying on it, check movement, left/right click, two-finger vertical scrolling, Start/End drag, Esc from capture, and disconnect. Close the laptop tab while dragging and confirm the PC mouse releases within 3 seconds. Restart the receiver and confirm the old pairing address is rejected. A second laptop should be rejected while the first remains connected.
