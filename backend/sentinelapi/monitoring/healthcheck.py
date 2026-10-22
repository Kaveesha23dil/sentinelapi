"""Authenticated local health probe; do not echo headers or response bodies."""
import os
from urllib.request import Request, urlopen

try:
    request = Request('http://127.0.0.1:8001/api/v1/monitoring/health',
                      headers={'Authorization': 'Bearer ' + os.environ['MONITORING_API_TOKEN']})
    with urlopen(request, timeout=5) as response:
        raise SystemExit(0 if response.status == 200 else 1)
except Exception:
    raise SystemExit(1)
