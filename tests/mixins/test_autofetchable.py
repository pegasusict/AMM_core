# tests/test_autofetchable.py

from sqlmodel import create_engine, Session, SQLModel
from mixins.autofetch import AutoFetchable
from test_autofetchable_models import Parent, Child, Toy


class TestAutoFetchable(AutoFetchable):
    pass


def test_load_full_with_nested_relationships():
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
