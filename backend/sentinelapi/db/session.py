"""Synchronous unit-of-work sessions; callers must not block an async route."""
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from .config import Settings


def make_engine(settings=None):
    return create_engine((settings or Settings.from_environment()).url(),
                         pool_pre_ping=True, hide_parameters=True, echo=False,
                         connect_args={'options': '-c timezone=UTC', 'connect_timeout': 10})


@contextmanager
def transaction(engine):
    try:
        with sessionmaker(engine, expire_on_commit=False)() as session:
            with session.begin():
                yield session
    except SQLAlchemyError:
        raise PersistenceError('Database operation failed; transaction rolled back. Check database availability and constraints.') from None


class PersistenceError(RuntimeError):
    """Safe public error without SQL parameters or driver details."""
