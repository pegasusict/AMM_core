# tests/test_autofetchable_models.py

from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class Parent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    children: List["Child"] = Relationship(back_populates="parent")


class Child(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    parent_id: Optional[int] = Field(default=None, foreign_key="parent.id")
    parent: Optional[Parent] = Relationship(back_populates="children")
    toys: List["Toy"] = Relationship(back_populates="child")


class Toy(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    child_id: Optional[int] = Field(default=None, foreign_key="child.id")
    child: Optional[Child] = Relationship(back_populates="toys")
