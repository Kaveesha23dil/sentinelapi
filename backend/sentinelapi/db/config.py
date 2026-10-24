"""Build URLs without interpolation, logging or embedding secrets in files."""
import os
from typing import Literal

from pydantic import BaseModel, Field, SecretStr
from sqlalchemy import URL


class Settings(BaseModel):
    host: str = 'postgres'
    port: int = Field(default=5432, ge=1, le=65535)
    database: str = Field(min_length=1)
    username: str = Field(min_length=1)
    password: SecretStr
    sslmode: Literal['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full'] | None = None
    sslrootcert: str | None = None

    @classmethod
    def from_environment(cls):
        password = os.environ.get('POSTGRES_PASSWORD', '')
        if not password or password == 'REPLACE_WITH_A_LONG_RANDOM_LOCAL_SECRET':
            raise ValueError('Set a non-placeholder POSTGRES_PASSWORD in the runtime environment')
        return cls(host=os.getenv('POSTGRES_HOST', 'postgres'),
                   port=int(os.getenv('POSTGRES_PORT', '5432')),
                   database=os.getenv('POSTGRES_DB', 'sentinelapi'),
                   username=os.getenv('POSTGRES_USER', 'sentinelapi_owner'),
                   password=SecretStr(password),
                   sslmode=os.getenv('POSTGRES_SSLMODE') or None,
                   sslrootcert=os.getenv('POSTGRES_SSLROOTCERT') or None)

    def url(self):
        return URL.create('postgresql+psycopg', username=self.username,
                          password=self.password.get_secret_value(), host=self.host,
                          port=self.port, database=self.database,
                          query={key: value for key, value in {
                              'sslmode': self.sslmode, 'sslrootcert': self.sslrootcert
                          }.items() if value is not None})
