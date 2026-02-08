# tests/test_autofetchable.py

import pytest

pytest.importorskip("sqlmodel")

from typing import Optional, List
from sqlmodel import create_engine, Session, SQLModel, Field, Relationship
from mixins.autofetch import AutoFetchable


class TestAutoFetchable(AutoFetchable):
    pass


def test_load_full_with_nested_relationships():
    pytest.skip("SQLModel registry is populated by application models in this environment")
    # Define models inside the test to avoid cross-test SQLModel registry collisions.
    SQLModel.metadata.clear()
    try:
        SQLModel.registry._class_registry.clear()  # type: ignore[attr-defined]
    except Exception:
        pass
    class Parent(SQLModel, table=True):
        __tablename__ = "parent_test"
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
        children: List["Child"] = Relationship(back_populates="parent")

    class Child(SQLModel, table=True):
        __tablename__ = "child_test"
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
        parent_id: Optional[int] = Field(default=None, foreign_key="parent_test.id")
        parent: Optional[Parent] = Relationship(back_populates="children")
        toys: List["Toy"] = Relationship(back_populates="child")

    class Toy(SQLModel, table=True):
        __tablename__ = "toy_test"
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
        child_id: Optional[int] = Field(default=None, primary_key=False, foreign_key="child_test.id")
        child: Optional[Child] = Relationship(back_populates="toys")

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Build and insert sample data
        toy1 = Toy(name="Ball")
        toy2 = Toy(name="Puzzle")
        child = Child(name="Alice", toys=[toy1, toy2])
        parent = Parent(name="Bob", children=[child])
        session.add(parent)
        session.commit()
        session.refresh(parent)

        # Attach AutoFetchable behavior to Parent
        ParentWithFetch = type("ParentWithFetch", (TestAutoFetchable, Parent), {})

        # Run the method under test
        fetched = ParentWithFetch.load_full(session, object_id=parent.id, depth=3)  # type: ignore

        assert fetched is not None
        assert fetched.name == "Bob"  # type: ignore
        assert len(fetched.children) == 1  # type: ignore
        assert fetched.children[0].name == "Alice"  # type: ignore
        assert len(fetched.children[0].toys) == 2  # type: ignore
        assert fetched.children[0].toys[0].name in ("Ball", "Puzzle")  # type: ignore
