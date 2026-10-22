"""Use the explicitly selected local WSO2 credential source without logging secrets."""

import base64
import getpass
import os
import re
import subprocess
import tomllib
from urllib.parse import urlencode


def basic(username, password):
    return 'Basic ' + base64.b64encode(f'{username}:{password}'.encode()).decode()


def container_admin():
    result = subprocess.run(
        ['docker', 'exec', 'sentinelapi-wso2', 'cat',
         '/home/wso2carbon/wso2am-4.5.0/repository/conf/deployment.toml'],
        capture_output=True, check=True,
    )
    config = tomllib.loads(result.stdout.decode())['super_admin']

    def resolve(value):
        match = re.fullmatch(r'\$env\{([^}]+)\}', value)
        if match:
            result = subprocess.run(['docker', 'exec', 'sentinelapi-wso2', 'printenv',
                                     match[1]], capture_output=True, check=True)
            return result.stdout.decode().strip()
        if re.match(r'^\$\w+\{', value):
            raise RuntimeError('Unsupported credential reference; use explicit environment variables')
        return value

    return resolve(config['username']), resolve(config['password'])


def management_token(client, *, from_container=False):
    if from_container:
        username, password = container_admin()
    else:
        username = os.getenv('WSO2_USERNAME') or input('WSO2 username: ')
        password = os.getenv('WSO2_PASSWORD') or getpass.getpass('WSO2 password (hidden): ')
    registration = client.json(
        'POST', 'https://localhost:9443/client-registration/v0.17/register',
        headers={'Authorization': basic(username, password)},
        payload={'clientName': 'SentinelAPIStep32Automation', 'owner': username,
                 'grantType': 'password', 'saasApp': False},
    )
    scopes = 'apim:api_view apim:api_create apim:api_manage apim:api_publish apim:subscribe apim:app_manage'
    token = client.json(
        'POST', 'https://localhost:9443/oauth2/token',
        headers={'Authorization': basic(registration['clientId'], registration['clientSecret']),
                 'Content-Type': 'application/x-www-form-urlencoded'},
        data=urlencode({'grant_type': 'password', 'username': username, 'password': password,
                        'scope': scopes}).encode(),
    )
    if not token.get('access_token'):
        raise RuntimeError('Management token not issued')
    # All credential values remain in memory and are never part of saved evidence.
    return token['access_token'], registration
