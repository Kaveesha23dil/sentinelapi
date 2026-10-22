"""Protect existing API identity and keep configured credentials out of output."""

import contextlib
import io
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from integrate_wso2 import Integration
from wso2_local_auth import management_token


class RecordingClient:
    def __init__(self, responses=()):
        self.responses = iter(responses)
        self.calls = []

    def json(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return next(self.responses)


class IntegrationSafetyTests(unittest.TestCase):
    def test_context_mismatch_stops_before_any_mutation(self):
        client = RecordingClient()
        integration = Integration(client, 'synthetic-management-token')
        integration.api = {'context': '/existing-manual-context'}
        with self.assertRaisesRegex(RuntimeError, 'immutable'):
            integration.complete()
        self.assertEqual(client.calls, [])

    def test_duplicate_api_identity_stops_before_fetch_or_mutation(self):
        client = RecordingClient()
        integration = Integration(client, 'synthetic-management-token')
        integration.pages = lambda url: [
            {'name': 'DemoCommerceAPI', 'version': '1.0.0', 'id': 'one'},
            {'name': 'DemoCommerceAPI', 'version': '1.0.0', 'id': 'two'},
        ]
        with self.assertRaisesRegex(RuntimeError, 'duplicate'):
            integration.inspect()
        self.assertEqual(client.calls, [])

    def test_authentication_does_not_log_credential_or_token_values(self):
        client = RecordingClient([
            {'clientId': 'synthetic-client', 'clientSecret': 'synthetic-secret'},
            {'access_token': 'synthetic-token'},
        ])
        output = io.StringIO()
        with patch.dict(os.environ, {'WSO2_USERNAME': 'synthetic-user',
                                     'WSO2_PASSWORD': 'synthetic-password'}), \
                contextlib.redirect_stdout(output):
            token, registration = management_token(client)
        self.assertEqual(token, 'synthetic-token')
        self.assertEqual(output.getvalue(), '')
        self.assertEqual(len(client.calls), 2)


if __name__ == '__main__':
    unittest.main()
