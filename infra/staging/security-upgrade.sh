#!/bin/sh
# Patch CVE-2026-109518 without changing the Debian/Python/PostgreSQL major.
# Never remove package database/advisory evidence or accept an unpatched mirror.
set -eu
. /etc/os-release
[ "$ID" = debian ]
case "$VERSION_CODENAME" in
    bookworm) library=libapt-pkg6.0; minimum=2.6.2 ;;
    trixie) library=libapt-pkg7.0; minimum=3.0.4 ;;
    *) echo 'Unreviewed image distribution' >&2; exit 1 ;;
esac
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends --only-upgrade apt "$library"
for package in apt "$library"; do
    dpkg --compare-versions "$(dpkg-query -W -f='${Version}' "$package")" ge "$minimum"
done
rm -rf /var/lib/apt/lists/*
