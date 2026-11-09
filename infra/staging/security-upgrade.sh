#!/bin/sh
# Patch apt and Trixie zlib without changing the Debian/Python/PostgreSQL major.
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
# The two zlib fixes have a Trixie fixed version; the Bookworm scan reports
# no fixed version. Do not mix distributions or apply a Trixie minimum there.
if [ "$VERSION_CODENAME" = trixie ]; then
    zlib_minimum='1:1.3.dfsg+really1.3.1-1+deb13u1'
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends --only-upgrade zlib1g
    installed=$(dpkg-query -W -f='${Version}' zlib1g)
    if ! dpkg --compare-versions "$installed" ge "$zlib_minimum"; then
        echo "zlib1g $installed is below required $zlib_minimum" >&2
        exit 1
    fi
fi
rm -rf /var/lib/apt/lists/*
