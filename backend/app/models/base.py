"""
SQLAlchemy Base Model

Purpose:
    Defines the declarative base class for all SQLAlchemy models.
    Automatically generates table names based on class names (User -> user).
"""
from typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr

@as_declarative()
class Base:
    id: Any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generates table name automatically from class name.
        Example: `User` -> `user`, `StudentAnswer` -> `studentanswer`.
        """
        return cls.__name__.lower()
