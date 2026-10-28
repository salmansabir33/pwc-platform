ARG POSTGRES_IMAGE
FROM ${POSTGRES_IMAGE}
# The official image's downloaded Go gosu binary is not needed: use Debian's
# maintained util-linux setpriv for the non-interactive UID/GID drop instead.
# Remove unused vulnerable executable from the actual runtime, not scan evidence.
RUN test "$PG_MAJOR" = 16 && command -v setpriv && rm /usr/local/bin/gosu
