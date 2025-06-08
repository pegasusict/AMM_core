# -*- coding: utf-8 -*-
#  Copyleft 2021-2025 Mattijs Snepvangers.
#  This file is part of Audiophiles' Music Manager, hereafter named AMM.
#
#  AMM is free software: you can redistribute it and/or modify  it under the terms of the
#   GNU General Public License as published by  the Free Software Foundation, either version 3
#   of the License or any later version.
#
#  AMM is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#   without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#   along with AMM.  If not, see <https://www.gnu.org/licenses/>.
"""This Module provides a mixin for SQLModel models to automatically fetch related objects."""

from typing import Optional, Type, List, Set, TypeVar
from sqlmodel import SQLModel, Session
from sqlalchemy.orm import selectinload, class_mapper, RelationshipProperty, Load
from sqlalchemy.future import select

T = TypeVar("T", bound=SQLModel)


class AutoFetchable(SQLModel):
    @classmethod
    def _recursive_loads(cls, visited: Optional[Set[Type[SQLModel]]] = None, depth: int = 2) -> List[Load]:
        if visited is None:
            visited = set()
        if cls in visited or depth <= 0:
            return []

        visited.add(cls)
        loaders: List[Load] = []

        for prop in class_mapper(cls).iterate_properties:
            if not isinstance(prop, RelationshipProperty):
                continue

            rel_attr = getattr(cls, prop.key)
            loader = selectinload(rel_attr)
            # Add the selectinload for the relationship
            loaders.append(loader)  # type: ignore

            # Recurse into related model
            related_cls = prop.mapper.class_
            nested_loads = related_cls._recursive_loads(visited, depth - 1)  # type: ignore

            for nested in nested_loads:
                # simplified join chaining
                loaders.append(loader.joinedload(nested.path[0]))  # type: ignore

        return loaders

    @classmethod
    def load_full(cls: Type[T], session: Session, object_id: int, depth: int = 2) -> Optional[T]:
        """Load an object by primary key with relationships up to `depth` levels deep."""
        pk = list(cls.__table__.primary_key.columns)[0]  # type: ignore
        stmt = select(cls).where(pk == object_id).options(*cls._recursive_loads(depth=depth))  # type: ignore
        return session.exec(stmt).first()  # type: ignore
