"""Small TLS-verifying HTTP client shared by the local WSO2 tools."""

import json
import ssl
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener, HTTPSHandler


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward credentials to a redirect destination.
        return None


class Client:
    def __init__(self, ca_file=None):
        context = ssl.create_default_context(cafile=ca_file)
        self.opener = build_opener(HTTPSHandler(context=context), NoRedirect())

    def request(self, method, url, *, token=None, payload=None, data=None, headers=None):
        headers = dict(headers or {})
        if token:
            headers['Authorization'] = 'Bearer ' + token
        if payload is not None:
            data = json.dumps(payload).encode()
            headers['Content-Type'] = 'application/json'
        req = Request(url, data=data, headers=headers, method=method)
        try:
            response = self.opener.open(req, timeout=30)
        except HTTPError as error:
            response = error
        with response:
            raw = response.read()
            try:
                body = json.loads(raw) if raw else None
            except (ValueError, UnicodeDecodeError):
                body = None
            return response.status, body

    def json(self, method, url, **kwargs):
        status, body = self.request(method, url, **kwargs)
        if not 200 <= status < 300:
            # Server bodies may contain sensitive fields. Never echo them.
            raise RuntimeError(f'{method} request failed with HTTP {status}')
        return body
