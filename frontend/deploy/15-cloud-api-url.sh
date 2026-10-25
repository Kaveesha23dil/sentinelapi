#!/bin/sh
set -eu
# Only an HTTPS URL with a DNS hostname and optional gateway path is accepted.
# No credentials, query strings, fragments or Nginx directives may be injected.
if ! printf '%s' "${SENTINEL_API_URL:-}" | grep -Eq '^https://[A-Za-z0-9][A-Za-z0-9.-]*(:[0-9]+)?/([A-Za-z0-9._~/-]*/)?$'; then
    echo 'Set SENTINEL_API_URL to the verified HTTPS API base URL ending with /' >&2
    exit 1
fi
