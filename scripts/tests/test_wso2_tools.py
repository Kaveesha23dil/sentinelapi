"""Regression checks for false-positive gateway evidence and unsafe redirects."""

import contextlib
import copy
import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from export_democommerce_openapi import validate
from smoke_wso2_gateway import run_smoke, validate_gateway_url
from wso2_http import NoRedirect


ORDER = {'id': 2, 'user_id': 1, 'items': [{'product_id': 101, 'quantity': 2}],
         'total_amount': '99.98', 'status': 'pending'}


class FakeClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def request(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return next(self.responses)


def responses():
    return [(401, {}), (200, []), (201, copy.deepcopy(ORDER)),
            (404, {'detail': 'Order not found'}), (200, ORDER), (200, ORDER)]


class GatewayEvidenceTests(unittest.TestCase):
    def run_checks(self, client):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            result = run_smoke(client, 'https://localhost:8243/demo/1.0.0',
                               'synthetic-test-value', 'http://localhost:8000')
        self.assertNotIn('synthetic-test-value', output.getvalue())
        return result

    def test_complete_flow_checks_backend_read_back(self):
        client = FakeClient(responses())
        self.assertEqual(len(self.run_checks(client)), 6)
        self.assertIsNone(client.calls[0][1]['token'])
        self.assertNotIn('token', client.calls[-1][1])

    def test_authentication_bypass_fails_before_creating_order(self):
        client = FakeClient([(200, [])])
        with self.assertRaises(AssertionError):
            self.run_checks(client)
        self.assertEqual(len(client.calls), 1)

    def test_gateway_route_404_is_not_backend_404(self):
        data = responses()
        data[3] = (404, {'code': '404', 'message': 'Not Found'})
        with self.assertRaises(AssertionError):
            self.run_checks(FakeClient(data))

    def test_wrong_created_order_is_rejected(self):
        data = responses()
        data[2][1]['total_amount'] = '0.00'
        with self.assertRaises(AssertionError):
            self.run_checks(FakeClient(data))

    def test_different_backend_is_rejected(self):
        data = responses()
        data[-1] = (404, {'detail': 'Order not found'})
        with self.assertRaises(AssertionError):
            self.run_checks(FakeClient(data))

    def test_unsafe_gateway_urls_are_rejected(self):
        for url in ['http://localhost:8243/demo', 'https://user:secret@localhost/demo',
                    'https://localhost/demo?token=value', 'https://localhost/demo#secret']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_gateway_url(url)

    def test_redirect_cannot_forward_credentials(self):
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, '', {},
                                                       'https://other.invalid'))

    def test_export_rejects_missing_payment_operation(self):
        document = json.loads((Path(__file__).resolve().parents[2] /
                               'infrastructure/wso2/democommerce-openapi.json').read_text())
        document['paths']['/api/v1/payments/simulate'].pop('post')
        with self.assertRaises(ValueError):
            validate(document)

    def test_export_rejects_broken_schema_reference(self):
        document = json.loads((Path(__file__).resolve().parents[2] /
                               'infrastructure/wso2/democommerce-openapi.json').read_text())
        document['components']['schemas'].pop('Order')
        with self.assertRaises(KeyError):
            validate(document)


if __name__ == '__main__':
    unittest.main()
