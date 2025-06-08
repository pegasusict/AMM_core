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
    """Mixin to support recursive eager loading of SQLModel relationships."""

    @classmethod
    def load_full(cls: Type[SQLModel], session: Session, object_id: int, depth: int = 2) -> Optional[SQLModel]:
        """
        Load an instance with all relationships eagerly loaded up to a certain depth.

        Args:
            session (Session): SQLModel session instance.
            object_id (int): Primary key of the object.
            depth (int): Depth of recursive eager loading.

        Returns:
            Optional[SQLModel]: The loaded object or None.
        """
        pk_col = list(cls.__table__.primary_key.columns)[0]  # type: ignore
        options = cls._recursive_selectinload(depth=depth)  # type: ignore
        stmt = select(cls).where(pk_col == object_id).options(*options)
        return session.exec(stmt).first()  # type: ignore

    @classmethod
    def _recursive_selectinload(cls, depth: int, visited: Optional[Set[Type[SQLModel]]] = None) -> List[Load]:
        """
        Recursively builds eager loading options using selectinload.

        Args:
            depth (int): How deep to load relationships.
            visited (Optional[Set]): Track visited classes to avoid infinite loops.

        Returns:
            List[Load]: List of SQLAlchemy Load objects.
        """
        visited = visited or set()
        if cls in visited or depth <= 0:
            return []

        visited.add(cls)
        return cls._get_relationship_loads(visited, depth)

    @classmethod
    def _get_relationship_loads(cls, visited: Set[Type[SQLModel]], depth: int) -> List[Load]:
        """Return selectinload options for all relationships."""
        options: List[Load] = []

        for rel_prop in class_mapper(cls).iterate_properties:
            if not isinstance(rel_prop, RelationshipProperty):
                continue

            rel_attr = getattr(cls, rel_prop.key)
            loader = selectinload(rel_attr)
            options.append(loader)  # type: ignore

            related_cls = rel_prop.mapper.class_
            nested_options = related_cls._recursive_selectinload(depth - 1, visited.copy())  # type: ignore

            for nested in nested_options:
                try:
                    options.append(loader.subqueryload_all(nested._to_bind))  # type: ignore
                except Exception:
                    # fallback silently if the loader isn't subquery-loadable
                    continue

        return options
