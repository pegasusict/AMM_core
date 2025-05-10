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
It uses the SQLalchemy library to connect to the database and perform operations on it.
"""
from sqlmodel import SQLModel
from sqlmodel import create_engine, Session
from sqlalchemy.orm import sessionmaker

class DB:
    """
    The DB class is used to manage the database connection.
    It uses the SQLalchemy library to connect to the database and perform operations on it.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DB, cls).__new__(cls)
            cls._instance._engine = None
            cls._instance._session = None
        return cls._instance

    def __init__(self, db_url: str = "mysql+pymysql://amm:password@localhost/amm"):
        """Initialize the DB class."""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._engine = create_engine(db_url)
            self._session = sessionmaker(bind=self._engine)

    def create_db_and_tables(self):
        """Create DB and Tables."""
        SQLModel.metadata.create_all(self._engine)

    def get_session(self):
        """Get the database session."""
        with Session(self._engine) as session:
            yield session

    def close(self):
        """Close the database session."""
        if self._session:
            self._session.close()
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
        session = self.get_session()
        result = session.execute(query)
        session.commit()
        return result

    def fetchall(self, query: str):
        """Fetch all results from a query."""
        session = self.get_session()
        result = session.execute(query).fetchall()
        session.commit()
        return result

    def fetchone(self, query: str):
        """Fetch one result from a query."""
        session = self.get_session()
        result = session.execute(query).fetchone()
        session.commit()
        return result

    def insert(self, table: str, values: dict):
        """Insert a record into a table."""
        session = self.get_session()
        result = session.execute(table.insert().values(values))
        session.commit()
        return result

    def update(self, table: str, values: dict, where: str):
        """Update a record in a table."""
        session = self.get_session()
        result = session.execute(table.update().values(values).where(where))
        session.commit()
        return result

    def delete(self, table: str, where: str):
        """Delete a record from a table."""
        session = self.get_session()
        result = session.execute(table.delete().where(where))
        session.commit()
        return result

    def get_table_row_count(self, table: str):
        """Get the number of rows in a table."""
        session = self.get_session()
        result = session.execute(f"SELECT COUNT(*) FROM {table}")
        session.commit()
        return result.fetchone()[0]

########################################################################
    def set_fields(self, data:dict, subject:object|None=None) -> object|dict:
        """Setting the nonempty values to the object."""
        if subject is None:
            subject = {}
        for key, value in data:
            if value is not None:
                subject.key = value
        return subject

########################################################################

    def register_picture(self, mbid:str, art_type:str, picture_path:str):
        """Register a picture in the database."""
        return self.insert("pictures", {"mbid": mbid, "art_type": art_type, "picture_path": picture_path})

    def register_file(self, filepath:str, metadata:dict):
        """Register metadata in the database."""
        values = self.set_fields(metadata)
        values.filepath = filepath
        return self.insert(table="files",values=values)
