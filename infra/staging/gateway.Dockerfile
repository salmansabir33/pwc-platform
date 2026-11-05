ARG HAPROXY_IMAGE
FROM ${HAPROXY_IMAGE}
USER root
COPY infra/staging/security-upgrade.sh /tmp/pwc-security-upgrade.sh
RUN sh /tmp/pwc-security-upgrade.sh && rm /tmp/pwc-security-upgrade.sh
USER 10001:10001
