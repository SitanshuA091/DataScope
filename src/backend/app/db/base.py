## Shared declarative model base and model imports for Alembic
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass