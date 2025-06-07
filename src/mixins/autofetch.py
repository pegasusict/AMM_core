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

from typing import Optional, Type, List, Set
from sqlmodel import SQLModel, Session
from sqlalchemy.orm import selectinload, class_mapper, RelationshipProperty, Load
from sqlalchemy.future import select


class AutoFetchable(SQLModel):
    @classmethod
    def _build_recursive_loads(
        cls, visited: Optional[Set[Type[SQLModel]]] = None, depth: int = 2
    ) -> List[Load]:
        if visited is None:
            visited = set()
        if cls in visited or depth == 0:
            return []
        visited.add(cls)

        options = []
        for prop in class_mapper(cls).iterate_properties:
            if isinstance(prop, RelationshipProperty):
                rel_attr = getattr(cls, prop.key)
                loader = selectinload(rel_attr)
                options.append(loader)

                related_class = prop.mapper.class_
                nested = related_class._build_recursive_loads(visited.copy(), depth - 1)
                for sub_loader in nested:
                    options.append(loader.subqueryload_all(sub_loader._to_bind))  # type: ignore
        return options

    @classmethod
    def load_full(
        cls: Type[SQLModel], session: Session, object_id: int, depth: int = 2
    ) -> Optional[SQLModel]:
        """Load an object by primary key with all relationships eagerly loaded."""
        pk_col = list(cls.__table__.primary_key.columns)[0]  # type: ignore
        options = cls._build_recursive_loads(depth=depth)  # type: ignore
        stmt = select(cls).where(pk_col == object_id).options(*options)
        return session.exec(statement=stmt).first()  # type: ignore
