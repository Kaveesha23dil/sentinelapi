import os
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Config:
    api_id: str
    api_name: str
    context: str
    version: str
    timezone: str = 'UTC'
    spool: Path = Path('/spool')
    state: Path = Path('/state')
    batch_size: int = 100

    @classmethod
    def env(cls):
        api_id = str(UUID(os.environ['WSO2_API_ID']))
        timezone = os.getenv('WSO2_LOG_TIMEZONE', 'UTC')
        ZoneInfo(timezone)
        return cls(api_id, os.getenv('WSO2_API_NAME', 'DemoCommerceAPI'),
                   os.environ['WSO2_API_CONTEXT'].rstrip('/'), os.environ['WSO2_API_VERSION'], timezone)
