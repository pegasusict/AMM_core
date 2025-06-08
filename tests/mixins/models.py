# models.py

from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from mixins.autofetch import AutoFetchable


class Review(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    book_id: Optional[int] = Field(default=None, foreign_key="book.id")
    book: Optional["Book"] = Relationship(back_populates="reviews")


class Book(AutoFetchable, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    author_id: Optional[int] = Field(default=None, foreign_key="author.id")
    author: Optional["Author"] = Relationship(back_populates="books")
    reviews: List[Review] = Relationship(back_populates="book")


class Author(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    books: List[Book] = Relationship(back_populates="author")
