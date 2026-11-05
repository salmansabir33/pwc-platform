ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE}
COPY infra/staging/security-upgrade.sh /tmp/pwc-security-upgrade.sh
RUN sh /tmp/pwc-security-upgrade.sh && rm /tmp/pwc-security-upgrade.sh
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/apps/backend DJANGO_SETTINGS_MODULE=config.staging
WORKDIR /app
COPY apps/backend/requirements.lock /tmp/requirements.lock
RUN pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock
COPY apps/backend /app/apps/backend
COPY infra/staging/runtime.py infra/staging/gunicorn.conf.py /app/infra/staging/
USER 10001:10001
ENTRYPOINT ["python", "/app/infra/staging/runtime.py"]
CMD ["serve"]
