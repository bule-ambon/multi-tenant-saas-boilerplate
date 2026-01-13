#!/usr/bin/env bash
set -euo pipefail

CERT_DIR="nginx/ssl"
CERT_KEY="${CERT_DIR}/localhost.key"
CERT_CRT="${CERT_DIR}/localhost.crt"

mkdir -p "${CERT_DIR}"

if [ -f "${CERT_KEY}" ] || [ -f "${CERT_CRT}" ]; then
  echo "Certificate files already exist in ${CERT_DIR}."
  exit 0
fi

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "${CERT_KEY}" \
  -out "${CERT_CRT}" \
  -subj "/CN=192.168.4.53" \
  -addext "subjectAltName=IP:192.168.4.53,DNS:localhost"

echo "Generated self-signed certs in ${CERT_DIR}."
