"""Guard against false security success; synthetic responses are not live evidence."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_api_security import check_oauth, check_throttle


class Client:
    def __init__(self, responses):
        self.responses = iter(responses)

    def request(self, *args, **kwargs):
        return next(self.responses)


class SecurityTests(unittest.TestCase):
    def test_requires_observed_429(self):
        result = check_throttle(Client([(200, [])] * 25), 'local', 'synthetic', pause=lambda _: None)
        self.assertFalse(result['passed'])
        self.assertEqual(len(result['statuses']), 25)

    def test_stops_at_observed_throttle(self):
        result = check_throttle(Client([(200, []), (429, {})]), 'local', 'synthetic', pause=lambda _: None)
        self.assertTrue(result['passed'])
        self.assertEqual(result['statuses'], [200, 429])

    def test_auth_error_is_not_throttling(self):
        self.assertFalse(check_throttle(Client([(401, {})]), 'local', 'synthetic')['passed'])

    def test_already_throttled_token_requires_fresh_window(self):
        self.assertFalse(check_throttle(Client([(429, {})]), 'local', 'synthetic')['passed'])

    def test_authentication_bypass_fails(self):
        results = check_oauth(Client([(200, []), (401, {}), (200, [])]), 'local', 'synthetic')
        self.assertFalse(results[0]['passed'])

    def test_backend_contract_required(self):
        results = check_oauth(Client([(401, {}), (401, {}), (200, {})]), 'local', 'synthetic')
        self.assertFalse(results[-1]['passed'])
