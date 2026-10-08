#!/bin/sh
set -eu
if [ "$(id -u)" != 0 ]; then
    echo 'Run this script with sudo to install DNS and HTTP on ports 53 and 80.' >&2
    exit 1
fi
cd "$(dirname "$0")"
/usr/bin/dnsmasq --test --conf-file=ps4-guide-dns.conf
install -m 644 ps4-guide-dns.conf /etc/ps4-guide-dns.conf
install -m 644 ps4-guide-dns.service ps4-guide-http.socket ps4-guide-http.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now ps4-guide-dns.service ps4-guide-http.socket
systemctl --no-pager status ps4-guide-dns.service ps4-guide-http.socket
