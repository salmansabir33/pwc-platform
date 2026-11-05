# PR44 image advisory remediation — 5 November 2026

## Provenance and limits

Original failed run: https://github.com/salmansabir33/pwc-platform/actions/runs/41990060923
on `fb601d3bd9a85a53f37179d3e8667f131b65aff5`, artifact 13397776775.
The sandbox cannot download Azure artifact blobs directly (EOF). A read-only
Actions job downloaded the actual retained artifact and extracted only package
fields; recovery run 41992489986. The accompanying JSON preserves all 286
image/package/advisory observations, including unfixed findings, with provenance.
No raw configuration, environment, keys, database or user data was copied.

`image-1` = app (Python 3.12 Bookworm), `image-2` = NGO Nginx, `image-3` = OPS
Nginx, `image-4` = PostgreSQL 16, `image-5` = HAProxy; the latter four use Debian
Trixie. Package inventory is not authority or deployment acceptance.

## Remediation

Ten fixable observations are one CVE: **CVE-2026-109518**, in `apt` and
`libapt-pkg6.0` (2.6.1 → at least 2.6.2) or `libapt-pkg7.0` (3.0.3 → at least
3.0.4). The same-major security upgrade installs only these packages and asserts
both installed versions using `dpkg --compare-versions`; a stale mirror fails the
build. A derived gateway image is now built and scanned rather than scanning an
unpatched upstream gateway. No package database or advisory evidence is removed.
The existing immutable base-image inputs, PostgreSQL major, Python minor, TLS,
non-root/read-only isolation and original scanner digest/gate are preserved.
Debian repositories supply security package updates at build time; this is not a
bit-identical rebuild guarantee. Retain resolved image digests and package
versions, scan the final immutable images and approve those exact artifacts.

First remediation run 41992749944 passed the original Compose and security gate:
app 39, NGO 64, OPS 64, DB 64, gateway 45 HIGH/CRITICAL observations, **0 fixable**.
This is **276 remaining observations, not zero vulnerabilities**. The original
scan already gates fixable HIGH/CRITICAL and retains all findings; that policy
was not weakened. Final PR checks/artifacts govern the final revision.

## Remaining findings and disposition

For every row below, the installed version/image comes from the original scan.
A blank upstream fixed version is rendered `not supplied`. For those findings,
no compatible fix is established by that report. This assignment does not
invent fixes, claim non-exploitability, migrate libc/distribution/PostgreSQL
major to conceal findings, or accept residual risk. Continue vendor monitoring
and evaluate tested compatible security updates; deployment/security owners must
review the complete remaining reports before real-user activation. Runtime
readers/writers remain disabled. The new diagnostic workflow and detailed
annotations are not replacements for the original scan or live-use acceptance.

## Complete original package matrix

| Advisory | Severity | Package | Installed | Fixed version in report | Images |
|---|---|---|---|---|---|
| CVE-2023-45853 | CRITICAL | `zlib1g` | `1:1.2.13.dfsg-1` | not supplied | app |
| CVE-2025-69720 | HIGH | `libncursesw6` | `6.4-4` | not supplied | app |
| CVE-2025-69720 | HIGH | `libncursesw6` | `6.5+20250216-2` | not supplied | db |
| CVE-2025-69720 | HIGH | `libtinfo6` | `6.4-4` | not supplied | app |
| CVE-2025-69720 | HIGH | `libtinfo6` | `6.5+20250216-2` | not supplied | db, haproxy, ngo, ops |
| CVE-2025-69720 | HIGH | `ncurses-base` | `6.4-4` | not supplied | app |
| CVE-2025-69720 | HIGH | `ncurses-base` | `6.5+20250216-2` | not supplied | db, haproxy, ngo, ops |
| CVE-2025-69720 | HIGH | `ncurses-bin` | `6.4-4` | not supplied | app |
| CVE-2025-69720 | HIGH | `ncurses-bin` | `6.5+20250216-2` | not supplied | db, haproxy, ngo, ops |
| CVE-2025-7458 | CRITICAL | `libsqlite3-0` | `3.40.1-2+deb12u2` | not supplied | app |
| CVE-2026-109518 | HIGH | `apt` | `2.6.1` | `2.6.2` | app |
| CVE-2026-109518 | HIGH | `apt` | `3.0.3` | `3.0.4` | db, haproxy, ngo, ops |
| CVE-2026-109518 | HIGH | `libapt-pkg6.0` | `2.6.1` | `2.6.2` | app |
| CVE-2026-109518 | HIGH | `libapt-pkg7.0` | `3.0.3` | `3.0.4` | db, haproxy, ngo, ops |
| CVE-2026-113351 | HIGH | `libexpat1` | `2.9.0-1~deb13u1` | not supplied | ngo, ops |
| CVE-2026-117610 | HIGH | `libexpat1` | `2.9.0-1~deb13u1` | not supplied | ngo, ops |
| CVE-2026-11822 | HIGH | `libsqlite3-0` | `3.40.1-2+deb12u2` | not supplied | app |
| CVE-2026-11824 | HIGH | `libsqlite3-0` | `3.40.1-2+deb12u2` | not supplied | app |
| CVE-2026-118370 | HIGH | `libexpat1` | `2.9.0-1~deb13u1` | not supplied | ngo, ops |
| CVE-2026-119373 | HIGH | `libsqlite3-0` | `3.40.1-2+deb12u2` | not supplied | app |
| CVE-2026-119373 | HIGH | `libsqlite3-0` | `3.46.1-7+deb13u2` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-12064 | HIGH | `curl` | `8.14.1-2+deb13u7` | not supplied | ngo, ops |
| CVE-2026-12064 | HIGH | `libcurl4t64` | `8.14.1-2+deb13u7` | not supplied | ngo, ops |
| CVE-2026-16742 | HIGH | `libsystemd0` | `252.39-1~deb12u2` | not supplied | app |
| CVE-2026-16742 | HIGH | `libsystemd0` | `257.13-1~deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-16742 | HIGH | `libudev1` | `252.39-1~deb12u2` | not supplied | app |
| CVE-2026-16742 | HIGH | `libudev1` | `257.13-1~deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-24882 | HIGH | `dirmngr` | `2.4.7-21+deb13u1+b5` | not supplied | db |
| CVE-2026-24882 | HIGH | `gnupg` | `2.4.7-21+deb13u1` | not supplied | db |
| CVE-2026-24882 | HIGH | `gnupg-l10n` | `2.4.7-21+deb13u1` | not supplied | db |
| CVE-2026-24882 | HIGH | `gpg` | `2.4.7-21+deb13u1+b5` | not supplied | db |
| CVE-2026-24882 | HIGH | `gpg-agent` | `2.4.7-21+deb13u1+b5` | not supplied | db |
| CVE-2026-24882 | HIGH | `gpgconf` | `2.4.7-21+deb13u1+b5` | not supplied | db |
| CVE-2026-24882 | HIGH | `gpgsm` | `2.4.7-21+deb13u1+b5` | not supplied | db |
| CVE-2026-36849 | HIGH | `libtiff6` | `4.7.0-3+deb13u3` | not supplied | ngo, ops |
| CVE-2026-41992 | HIGH | `gzip` | `1.12-1` | not supplied | app |
| CVE-2026-52490 | HIGH | `libtiff6` | `4.7.0-3+deb13u3` | not supplied | ngo, ops |
| CVE-2026-53613 | HIGH | `bsdutils` | `1:2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-53613 | HIGH | `libblkid1` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-53613 | HIGH | `libmount1` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-53613 | HIGH | `libsmartcols1` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-53613 | HIGH | `libuuid1` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-53613 | HIGH | `mount` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-53613 | HIGH | `util-linux` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-53613 | HIGH | `util-linux-extra` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-53615 | HIGH | `bsdutils` | `1:2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-53615 | HIGH | `libblkid1` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-53615 | HIGH | `libmount1` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-53615 | HIGH | `libsmartcols1` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-53615 | HIGH | `libuuid1` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-53615 | HIGH | `mount` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-53615 | HIGH | `util-linux` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-53615 | HIGH | `util-linux-extra` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-54369 | HIGH | `libacl1` | `2.3.1-3` | not supplied | app |
| CVE-2026-54369 | HIGH | `libacl1` | `2.3.2-2+b1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-6653 | CRITICAL | `libxml2` | `2.12.7+dfsg+really2.9.14-2.1+deb13u3` | not supplied | db, ngo, ops |
| CVE-2026-74860 | HIGH | `libxml2` | `2.12.7+dfsg+really2.9.14-2.1+deb13u3` | not supplied | db, ngo, ops |
| CVE-2026-76642 | HIGH | `bsdutils` | `1:2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-76642 | HIGH | `libblkid1` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-76642 | HIGH | `liblastlog2-2` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-76642 | HIGH | `libmount1` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-76642 | HIGH | `libsmartcols1` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-76642 | HIGH | `libuuid1` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-76642 | HIGH | `login` | `1:4.16.0-2+really2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-76642 | HIGH | `mount` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-76642 | HIGH | `util-linux` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-76844 | HIGH | `zlib1g` | `1:1.2.13.dfsg-1` | not supplied | app |
| CVE-2026-76844 | HIGH | `zlib1g` | `1:1.3.dfsg+really1.3.1-1+b1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78408 | HIGH | `bsdutils` | `1:2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78408 | HIGH | `libblkid1` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78408 | HIGH | `liblastlog2-2` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78408 | HIGH | `libmount1` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78408 | HIGH | `libsmartcols1` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78408 | HIGH | `libuuid1` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78408 | HIGH | `login` | `1:4.16.0-2+really2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78408 | HIGH | `mount` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78408 | HIGH | `util-linux` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78409 | HIGH | `bsdutils` | `1:2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78409 | HIGH | `libblkid1` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78409 | HIGH | `liblastlog2-2` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78409 | HIGH | `libmount1` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78409 | HIGH | `libsmartcols1` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78409 | HIGH | `libuuid1` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78409 | HIGH | `login` | `1:4.16.0-2+really2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78409 | HIGH | `mount` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78409 | HIGH | `util-linux` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78410 | HIGH | `bsdutils` | `1:2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-78410 | HIGH | `bsdutils` | `1:2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78410 | HIGH | `libblkid1` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-78410 | HIGH | `libblkid1` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78410 | HIGH | `liblastlog2-2` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78410 | HIGH | `libmount1` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-78410 | HIGH | `libmount1` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78410 | HIGH | `libsmartcols1` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-78410 | HIGH | `libsmartcols1` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78410 | HIGH | `libuuid1` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-78410 | HIGH | `libuuid1` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78410 | HIGH | `login` | `1:4.16.0-2+really2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78410 | HIGH | `mount` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-78410 | HIGH | `mount` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78410 | HIGH | `util-linux` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-78410 | HIGH | `util-linux` | `2.41.5-0+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-78410 | HIGH | `util-linux-extra` | `2.38.1-5+deb12u3` | not supplied | app |
| CVE-2026-8458 | HIGH | `curl` | `8.14.1-2+deb13u7` | not supplied | ngo, ops |
| CVE-2026-8458 | HIGH | `libcurl4t64` | `8.14.1-2+deb13u7` | not supplied | ngo, ops |
| CVE-2026-86138 | HIGH | `libxml2` | `2.12.7+dfsg+really2.9.14-2.1+deb13u3` | not supplied | db, ngo, ops |
| CVE-2026-86139 | HIGH | `libxml2` | `2.12.7+dfsg+really2.9.14-2.1+deb13u3` | not supplied | db, ngo, ops |
| CVE-2026-86140 | HIGH | `libxml2` | `2.12.7+dfsg+really2.9.14-2.1+deb13u3` | not supplied | db, ngo, ops |
| CVE-2026-86142 | HIGH | `libxml2` | `2.12.7+dfsg+really2.9.14-2.1+deb13u3` | not supplied | db, ngo, ops |
| CVE-2026-86143 | HIGH | `libxml2` | `2.12.7+dfsg+really2.9.14-2.1+deb13u3` | not supplied | db, ngo, ops |
| CVE-2026-86144 | HIGH | `libxml2` | `2.12.7+dfsg+really2.9.14-2.1+deb13u3` | not supplied | db, ngo, ops |
| CVE-2026-88806 | HIGH | `libx11-6` | `2:1.8.12-1` | not supplied | ngo, ops |
| CVE-2026-88806 | HIGH | `libx11-data` | `2:1.8.12-1` | not supplied | ngo, ops |
| CVE-2026-9538 | HIGH | `libperl5.40` | `5.40.1-6+deb13u1` | not supplied | db |
| CVE-2026-9538 | HIGH | `perl` | `5.40.1-6+deb13u1` | not supplied | db |
| CVE-2026-9538 | HIGH | `perl-base` | `5.36.0-7+deb12u4` | not supplied | app |
| CVE-2026-9538 | HIGH | `perl-base` | `5.40.1-6+deb13u1` | not supplied | db, haproxy, ngo, ops |
| CVE-2026-9538 | HIGH | `perl-modules-5.40` | `5.40.1-6+deb13u1` | not supplied | db |
