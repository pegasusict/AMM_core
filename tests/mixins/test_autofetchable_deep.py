# test_autofetchable_deep.py

import pytest
from sqlmodel import Session, SQLModel, create_engine
from models import Author, Book, Review


@pytest.fixture
def session():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_load_full_with_deep_relationships(session):
    # Create sample data with nested relationships
    author = Author(name="Douglas Adams")
    book = Book(title="The Hitchhiker's Guide", author=author)
    review1 = Review(text="Brilliant", book=book)
    review2 = Review(text="Timeless", book=book)

    session.add_all([author, book, review1, review2])
    session.commit()

    # Load using AutoFetchable
    loaded_book = Book.load_full(session=session, object_id=book.id, depth=2)  # type: ignore

    assert loaded_book is not None
    assert loaded_book.title == "The Hitchhiker's Guide"

    # Check author was eagerly loaded
    assert loaded_book.author is not None
    assert loaded_book.author.name == "Douglas Adams"

    # Check reviews were eagerly loaded
    assert loaded_book.reviews is not None
    assert len(loaded_book.reviews) == 2
    review_texts = {review.text for review in loaded_book.reviews}
    assert review_texts == {"Brilliant", "Timeless"}
