#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID} -ne 0 || -z ${SUDO_USER:-} || ${SUDO_USER} == root ]]; then
    echo 'Run this from your normal Ubuntu account: sudo bash setup-ubuntu.sh'
    exit 1
fi
if ! command -v python3 >/dev/null; then
    echo 'Install Python first: sudo apt install python3'
    exit 1
fi
groupadd --force wifi-trackpad
usermod --append --groups wifi-trackpad "$SUDO_USER"
printf '%s\n' 'uinput' > /etc/modules-load.d/wifi-trackpad.conf
printf '%s\n' 'KERNEL=="uinput", SUBSYSTEM=="misc", GROUP="wifi-trackpad", MODE="0660", OPTIONS+="static_node=uinput"' > /etc/udev/rules.d/99-wifi-trackpad.rules
modprobe uinput
udevadm control --reload-rules
udevadm trigger --subsystem-match=misc --sysname-match=uinput
udevadm settle
chgrp wifi-trackpad /dev/uinput
chmod 0660 /dev/uinput
echo 'Setup complete. Log out of Ubuntu completely and log back in.'
echo 'Then run: python3 receiver.py (without sudo).'
echo 'Members of wifi-trackpad can create virtual input devices.'
