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

"""
This module contains the DB class, which is used to manage the database connection.
It uses the SQLModel library to connect to the database and perform operations on it.
"""

from pathlib import Path
from sqlmodel import SQLModel, select, create_engine, Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from ..Exceptions import InvalidValueError
from ..dbmodels import DBFile, DBTask, Stage, TaskStatus


######################################################################
def set_fields(data: dict, subject: object | None = None) -> object | dict:
    """Setting the nonempty values to the object."""
    if subject is None:
        subject = {}
    for key, value in data.items():
        if value is not None:
            if isinstance(subject, dict):
                subject[key] = value
            else:
                setattr(subject, key, value)
    return subject


########################################################################


class DB:
    """
    The DB class is used to manage the database connection.
    It uses the SQLModel library to connect to the database and perform operations on it.
    """

    def __init__(self, db_url: str = "mysql+pymysql://amm:password@localhost/amm"):
        """Initialize the DB class."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._engine = create_engine(db_url)
            self._session = sessionmaker(bind=self._engine)

    def create_db_and_tables(self):
        """Create DB and Tables."""
        if self._engine is not None:
            SQLModel.metadata.create_all(bind=self._engine)
        else:
            raise RuntimeError("Database engine is not initialized.")

    def get_session(self):
        """Get the database session."""
        with Session(self._engine) as session:
            return session

    def close(self):
        """Close the database session."""
        self._session = None
        if self._engine:
            self._engine.dispose()
            self._engine = None

    def reset(self):
        """Reset the database connection."""
        self.close()
        self.__init__()

    def execute(self, query: str):
        """Execute a query on the database."""
        with Session(self._engine) as session:
            result = session.execute(text(query))
            session.commit()
            return result

    def fetchall(self, query: str):
        """Fetch all results from a query."""
        with Session(self._engine) as session:
            result = session.execute(text(query)).fetchall()
            session.commit()
            return result

    def fetchone(self, query: str):
        """Fetch one result from a query."""
        with Session(self._engine) as session:
            result = session.execute(text(query)).fetchone()
            session.commit()
            return result

    def insert(self, table, values: dict):
        """Insert a record into a table."""
        with Session(self._engine) as session:
            result = session.execute(table.insert().values(values))
            session.commit()
            return result

    def update(self, table, values: dict, where):
        """Update a record in a table."""
        with Session(self._engine) as session:
            result = session.execute(table.update().values(values).where(where))
            session.commit()
            return result

    def delete(self, table, where):
        """Delete a record from a table."""
        with Session(self._engine) as session:
            result = session.execute(table.delete().where(where))
            session.commit()
            return result

    ########################################################################

    def register_picture(self, mbid: str, art_type: str, picture_path: str):
        """Register a picture in the database."""
        return self.insert(
            "pictures",
            {"mbid": mbid, "art_type": art_type, "picture_path": picture_path},
        )

    def register_file(self, filepath: str, metadata: dict):
        """Register file in the database."""
        values = set_fields(metadata)
        if not isinstance(values, dict):
            values = vars(values)
        values["filepath"] = filepath
        return self.insert(table="files", values=values)

    def update_file(self, filepath: str, metadata: dict[str, str | int | Path]):
        """Update file metadata in the database."""
        values = set_fields(metadata)
        if not isinstance(values, dict):
            values = vars(values)
        values["filepath"] = filepath
        file_id = metadata.get("file_id")
        return self.update(table="files", values=values, where=[id, file_id])

    def set_file_stage(self, file_id: int, stage: Stage) -> None:
        """Sets the processed stage for the file."""
        if not isinstance(stage, Stage):
            if isinstance(stage, str) and stage in Stage:
                stage = Stage[stage]
            else:
                raise InvalidValueError(f"Invalid Stage: {stage}")

        session = self.get_session()
        statement = select(DBFile).where(DBFile.id == file_id)
        file = session.exec(statement).first()
        file.stage = stage  # type: ignore
        session.add(file)
        session.commit()
        session.close()

    def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Updates the status of the specified Task."""
        session = self.get_session()
        db_task = session.get_one(DBTask, task_id)
        db_task.status = status
        session.add(db_task)
        session.commit()
        session.close()

    def get_paused_tasks(self) -> list[DBTask]:  # type: ignore
        """Retrieves a list of paused tasks from the database."""
        session = self.get_session()
        db_tasks = session.get(DBTask, DBTask.status == TaskStatus.PAUSED)
        result = []
        if db_tasks is not None:
            for db_task in db_tasks:
                result.append(db_task)
        return result

    def file_exists(self, file_path: str) -> bool:
        session = self.get_session()
        result = session.get_one(DBFile, DBFile.file_path == file_path)
        session.close()
        return result is not None
