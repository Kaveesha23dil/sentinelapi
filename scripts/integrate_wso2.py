"""Inspect and complete Step 3.2 through the installed WSO2 4.5 REST APIs."""

import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from discover_wso2 import multipart
from smoke_wso2_gateway import run_smoke
from wso2_http import Client
from wso2_local_auth import basic, management_token

PUB = 'https://localhost:9443/api/am/publisher/v4'
DEV = 'https://localhost:9443/api/am/devportal/v3'
API_NAME = 'DemoCommerceAPI'
APP_NAME = 'SentinelAPITestClient'


class Integration:
    def __init__(self, client, token):
        self.client, self.token = client, token

    def call(self, method, url, **kwargs):
        return self.client.json(method, url, token=self.token, **kwargs)

    def pages(self, url):
        rows, offset = [], 0
        while True:
            separator = '&' if '?' in url else '?'
            page = self.call('GET', url + f'{separator}limit=100&offset={offset}')
            rows.extend(page['list'])
            offset += len(page['list'])
            if not page['list'] or offset >= page.get('pagination', {}).get('total', offset):
                return rows

    def inspect(self):
        apis = self.pages(PUB + '/apis')
        matches = [a for a in apis if a['name'] == API_NAME and a['version'] == '1.0.0']
        if len(matches) > 1:
            raise RuntimeError('Ambiguous duplicate API versions; review required')
        self.api = self.call('GET', PUB + '/apis/' + matches[0]['id']) if matches else None
        self.settings = self.call('GET', PUB + '/settings')
        self.apps = self.pages(DEV + '/applications')
        if self.api:
            self.deployments = self.call('GET', PUB + '/apis/' + self.api['id'] + '/deployments')
        else:
            self.deployments = {'list': []}
        safe = {
            'api': {k: self.api.get(k) for k in
                    ['id', 'name', 'version', 'context', 'lifeCycleStatus', 'securityScheme',
                     'policies']} if self.api else None,
            'operations': [{k: o.get(k) for k in ['target', 'verb', 'authType']}
                           for o in self.api['operations']] if self.api else [],
            'production_endpoint': self.api.get('endpointConfig', {}).get('production_endpoints', {}).get('url')
                                   if self.api else None,
            'deployments': self.deployments,
            'gateway_environments': self.settings.get('environment'),
            'matching_applications': [{k: a.get(k) for k in ['applicationId', 'name', 'throttlingPolicy']}
                                      for a in self.apps if a['name'] == APP_NAME],
        }
        print(json.dumps(safe, indent=2), flush=True)
        return apis

    def complete(self):
        if self.api and self.api['context'] != '/democommerce':
            # WSO2 9.31.86 PublisherCommonUtils.updateApi deliberately restores
            # the original context. Replacing an existing API needs approval.
            raise RuntimeError('Existing API context is immutable; retain it or obtain approval for replacement')
        spec_path = Path('infrastructure/wso2/democommerce-openapi.json')
        spec = json.loads(spec_path.read_text(encoding='utf-8-sig'))
        data, headers = multipart({'inlineAPIDefinition': json.dumps(spec)})
        validation = self.call('POST', PUB + '/apis/validate-openapi', data=data, headers=headers)
        if not validation.get('isValid'):
            raise RuntimeError('Installed WSO2 OpenAPI validation failed')
        print('Installed WSO2 OpenAPI validation: PASS', flush=True)
        if not self.api:
            data, headers = multipart({
                'inlineAPIDefinition': json.dumps(spec),
                'additionalProperties': Path('infrastructure/wso2/democommerce-api-properties.json').read_text(),
            })
            self.api = self.call('POST', PUB + '/apis/import-openapi', data=data, headers=headers)
        api_url = PUB + '/apis/' + self.api['id']
        endpoint = dict(self.api.get('endpointConfig', {}))
        endpoint['endpoint_type'] = 'http'
        endpoint['production_endpoints'] = dict(endpoint.get('production_endpoints', {}),
                                               url='http://democommerce:8000')
        desired = {
            'context': '/democommerce',
            'endpointConfig': endpoint,
            'securityScheme': ['oauth_basic_auth_api_key_mandatory', 'oauth2'],
            'policies': ['Unlimited'],
            'transport': ['https'],
        }
        # Preserve unrelated existing API attributes and policies.
        dirty = any(self.api.get(k) != v for k, v in desired.items())
        self.api.update(desired)
        expected_operations = {(path, method.upper()) for path, methods in spec['paths'].items()
                               for method in methods if method in ['get', 'post', 'put', 'patch', 'delete']}
        actual_operations = {(o['target'], o['verb']) for o in self.api['operations']}
        if expected_operations != actual_operations:
            raise RuntimeError('Existing API operations differ from actual backend; explicit review required')
        for operation in self.api['operations']:
            if operation.get('authType') != 'Application & Application User':
                dirty = True
            operation['authType'] = 'Application & Application User'
        if dirty:
            self.call('PUT', api_url, payload=self.api)
            print('Updated existing API through supported Publisher PUT.', flush=True)
        self.api = self.call('GET', api_url)
        if self.api['context'] != '/democommerce':
            raise RuntimeError('WSO2 did not accept the requested context; no deletion attempted')
        # Ensure the existing gateway definition has the actual resource paths.
        swagger = self.call('GET', api_url + '/swagger')
        if isinstance(swagger, str):
            swagger = json.loads(swagger)
        if set(swagger['paths']) != set(spec['paths']):
            raise RuntimeError('Deployed API definition does not match backend paths')
        deployment_rows = self.deployments if isinstance(self.deployments, list) else self.deployments['list']
        if dirty or not deployment_rows:
            environments = self.settings['environment']
            local = [e for e in environments if any(v['host'] == 'localhost' for v in e.get('vhosts', []))]
            if len(local) != 1:
                raise RuntimeError('Local gateway environment is ambiguous')
            revision = self.call('POST', api_url + '/revisions',
                                 payload={'description': 'Step 3.2 DemoCommerce integration'})
            self.call('POST', api_url + '/deploy-revision?revisionId=' + revision['id'],
                      payload=[{'name': local[0]['name'], 'vhost': 'localhost',
                                'displayOnDevportal': True}])
            print('Created and submitted a new gateway revision; existing revisions retained.', flush=True)
        if self.api['lifeCycleStatus'] != 'PUBLISHED':
            self.call('POST', PUB + '/apis/change-lifecycle?' +
                      urlencode({'action': 'Publish', 'apiId': self.api['id']}))
        self.test_application()

    def deploy_existing(self):
        if not self.api:
            raise RuntimeError('No API to deploy')
        api_url = PUB + '/apis/' + self.api['id']
        local = [e for e in self.settings['environment']
                 if any(v['host'] == 'localhost' for v in e.get('vhosts', []))]
        if len(local) != 1:
            raise RuntimeError('Local gateway environment is ambiguous')
        revision = self.call('POST', api_url + '/revisions',
                             payload={'description': 'Step 3.2 verified OAuth gateway integration'})
        self.call('POST', api_url + '/deploy-revision?revisionId=' + revision['id'],
                  payload=[{'name': local[0]['name'], 'vhost': 'localhost',
                            'displayOnDevportal': True}])
        for attempt in range(15):
            deployments = self.call('GET', api_url + '/deployments')
            rows = deployments if isinstance(deployments, list) else deployments['list']
            if any(d['revisionUuid'] == revision['id'] and d['status'] == 'APPROVED' for d in rows):
                self.deployments = deployments
                print('New revision deployment APPROVED on the discovered local gateway.', flush=True)
                return
            time.sleep(2)
        raise RuntimeError('Revision deployment did not become approved')

    def test_application(self):
        app_matches = [a for a in self.pages(DEV + '/applications') if a['name'] == APP_NAME]
        if len(app_matches) > 1:
            raise RuntimeError('Ambiguous test applications')
        app = app_matches[0] if app_matches else self.call(
            'POST', DEV + '/applications',
            payload={'name': APP_NAME, 'throttlingPolicy': 'Unlimited', 'tokenType': 'JWT',
                     'description': 'SentinelAPI local Step 3.2 gateway smoke tests'})
        app_url = DEV + '/applications/' + app['applicationId']
        print('Test application ready (credentials withheld).', flush=True)
        subscriptions = self.pages(DEV + '/subscriptions?applicationId=' + app['applicationId'])
        subscriptions = [s for s in subscriptions if s.get('apiId') == self.api['id']]
        if not subscriptions:
            subscription = self.call('POST', DEV + '/subscriptions',
                                     payload={'apiId': self.api['id'],
                                              'applicationId': app['applicationId'],
                                              'throttlingPolicy': 'Unlimited'})
        else:
            subscription = subscriptions[0]
        if subscription.get('status') != 'UNBLOCKED':
            raise RuntimeError('Subscription not active')
        print('Unlimited subscription is active.', flush=True)
        managers = self.call('GET', DEV + '/key-managers')['list']
        resident = [m for m in managers if m.get('name') == 'Resident Key Manager']
        if len(resident) != 1:
            raise RuntimeError('Resident Key Manager unavailable')
        keys = self.call('GET', app_url + '/oauth-keys')['list']
        keys = [k for k in keys if k['keyType'] == 'PRODUCTION']
        if keys:
            if len(keys) != 1:
                raise RuntimeError('Multiple production keys; explicit selection required')
            key = self.call('GET', app_url + '/oauth-keys/' + keys[0]['keyMappingId'])
        else:
            key = self.call('POST', app_url + '/generate-keys',
                            payload={'keyType': 'PRODUCTION', 'keyManager': resident[0]['name'],
                                     'grantTypesToBeSupported': ['client_credentials'],
                                     'validityTime': '300', 'scopes': ['default'],
                                     'additionalProperties': {'application_access_token_expiry_time': '300'}})
        properties = key.get('additionalProperties') or {}
        if isinstance(properties, str):
            properties = json.loads(properties)
        if str(properties.get('application_access_token_expiry_time')) != '300':
            properties = dict(properties, application_access_token_expiry_time='300')
            key_url = app_url + '/oauth-keys/' + key['keyMappingId']
            self.call('PUT', key_url, payload={
                'keyMappingId': key['keyMappingId'], 'keyManager': key['keyManager'],
                'keyType': key['keyType'], 'callbackUrl': key.get('callbackUrl') or '',
                'supportedGrantTypes': key['supportedGrantTypes'],
                'additionalProperties': properties,
            })
            key = self.call('GET', key_url)
            print('Configured per-application access-token lifetime to 300 seconds.', flush=True)
        generated = self.call(
            'POST', app_url + '/oauth-keys/' + key['keyMappingId'] + '/generate-token',
            payload={'consumerSecret': key['consumerSecret'], 'validityPeriod': 300,
                     'scopes': ['default'], 'grantType': 'CLIENT_CREDENTIALS'})
        test_token = generated['accessToken']
        encoded_claims = test_token.split('.')[1]
        claims = json.loads(base64.urlsafe_b64decode(encoded_claims + '=' * (-len(encoded_claims) % 4)))
        validity = int(claims['exp']) - int(claims['iat'])
        print(f'Token lifetime: response={int(generated["validityTime"])}; JWT exp-iat={validity} seconds.',
              flush=True)
        if not 0 < validity <= 300:
            self.revoke_test_token(key, test_token)
            raise RuntimeError('Test token lifetime is not short-lived')
        print(f'Test application subscribed; OAuth token issued for {validity} seconds (value withheld).',
              flush=True)
        portal = None
        gateway_url = None
        for attempt in range(15):
            portal = self.call('GET', DEV + '/apis/' + self.api['id'])
            urls = [e['URLs']['https'] for e in portal['endpointURLs']
                    if e.get('URLs', {}).get('https')]
            if len(urls) != 1:
                raise RuntimeError('HTTPS gateway URL is ambiguous')
            gateway_url = urls[0]
            if urlsplit(gateway_url).scheme != 'https' or urlsplit(gateway_url).hostname != 'localhost':
                self.revoke_test_token(key, test_token)
                raise RuntimeError('This local automation only sends test tokens to HTTPS localhost')
            expected_path = self.api['context'].rstrip('/') + '/' + self.api['version']
            if not gateway_url.endswith(expected_path):
                raise RuntimeError('Developer Portal still advertises a different context')
            status, _ = self.client.request('GET', gateway_url + '/api/v1/orders')
            if status == 401:
                break
            time.sleep(2)
        else:
            raise RuntimeError('Gateway did not deploy requested route')
        try:
            results = run_smoke(self.client, gateway_url, test_token, 'http://localhost:8000')
            deployments = self.call('GET', PUB + '/apis/' + self.api['id'] + '/deployments')
            report = {
                'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'passed': True,
                'api_id': self.api['id'], 'name': API_NAME, 'version': '1.0.0',
                'context': self.api['context'], 'requested_context': '/democommerce',
                'requested_context_matches': self.api['context'] == '/democommerce',
                'step_3_2_complete': self.api['context'] == '/democommerce',
                'gateway_url': gateway_url,
                'production_endpoint': 'http://democommerce:8000', 'security': 'OAuth2',
                'subscription_policy': 'Unlimited', 'application_name': APP_NAME,
                'application_id': app['applicationId'], 'subscription_id': subscription['subscriptionId'],
                'token_validity_seconds': validity, 'deployments': deployments, 'tests': results,
            }
            Path('infrastructure/wso2/gateway-verification.json').write_text(
                json.dumps(report, indent=2) + '\n')
            print('PASS: actual deployment, publication, subscription and gateway routing verified.', flush=True)
        finally:
            self.revoke_test_token(key, test_token)

    def revoke_test_token(self, key, token):
        self.client.json('POST', 'https://localhost:9443/oauth2/revoke',
                         headers={'Authorization': basic(key['consumerKey'], key['consumerSecret']),
                                  'Content-Type': 'application/x-www-form-urlencoded'},
                         data=urlencode({'token': token, 'token_type_hint': 'access_token'}).encode())
        print('Test token revocation submitted; value withheld.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-container', action='store_true',
                        help='Read existing super_admin credentials into memory from the local container')
    parser.add_argument('--ca-file', default=os.getenv('WSO2_CA_FILE'))
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument('--apply', action='store_true', help='Complete the inspected integration')
    parser.add_argument('--test-existing', action='store_true',
                        help='Create/reuse the test client and test the current deployed context')
    parser.add_argument('--deploy-existing', action='store_true',
                        help='Create and deploy a revision of the inspected API before testing')
    args = parser.parse_args()
    client = Client(args.ca_file)
    token, registration = management_token(client, from_container=args.from_container)
    print('Authenticated with configured local administrator; credential values withheld.', flush=True)
    integration = Integration(client, token)
    integration.inspect()
    if args.apply:
        integration.complete()
    elif args.test_existing:
        if not integration.api:
            raise RuntimeError('No existing API to test')
        if args.deploy_existing:
            integration.deploy_existing()
        integration.test_application()
    if args.interactive:
        print('Inspection complete. Enter an action (inspect/apply/quit):', flush=True)
        while True:
            action = input().strip()
            if action == 'quit':
                break
            if action == 'inspect':
                integration.inspect()
            elif action == 'apply':
                integration.complete()
            else:
                print('Unknown action', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Suppress exception text/tracebacks: HTTP payloads may contain credentials.
        print(f'FAIL: Step 3.2 automation stopped ({type(error).__name__}); no secret values displayed.',
              flush=True)
        if isinstance(error, RuntimeError):
            # Only our own authored errors/HTTP status messages use RuntimeError.
            print(str(error), flush=True)
        sys.exit(1)
