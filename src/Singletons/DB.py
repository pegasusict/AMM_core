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

from sqlalchemy import create_engine
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
        """
        Initialize the DB class.

        :param db_url: The URL of the database.
        """
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._engine = create_engine(db_url)
            self._session = sessionmaker(bind=self._engine)()

    def get_session(self):
        """
        Get the database session.

        :return: The database session.
        """
        return self._session

    def close(self):
        """
        Close the database session.
        """
        if self._session:
            self._session.close()
            self._session = None
        if self._engine:
            self._engine.dispose()
            self._engine = None

    def reset(self):
        """
        Reset the database connection.
        """
        self.close()
        self.__init__()

    def execute(self, query: str):
        """
        Execute a query on the database.
        :param query: The query to execute.
        :return: The result of the query.
        """
        session = self.get_session()
        result = session.execute(query)
        session.commit()
        return result

    def fetchall(self, query: str):
        """
        Fetch all results from a query.
        :param query: The query to execute.
        :return: The results of the query.
        """
        session = self.get_session()
        result = session.execute(query).fetchall()
        session.commit()
        return result

    def fetchone(self, query: str):
        """
        Fetch one result from a query.
        :param query: The query to execute.
        :return: The result of the query.
        """
        session = self.get_session()
        result = session.execute(query).fetchone()
        session.commit()
        return result

    def insert(self, table: str, values: dict):
        """
        Insert a record into a table.
        :param table: The name of the table.
        :param values: The values to insert.
        :return: The result of the insert operation.
        """
        session = self.get_session()
        result = session.execute(table.insert().values(values))
        session.commit()
        return result

    def update(self, table: str, values: dict, where: str):
        """
        Update a record in a table.
        :param table: The name of the table.
        :param values: The values to update.
        :param where: The condition for the update.
        :return: The result of the update operation.
        """
        session = self.get_session()
        result = session.execute(table.update().values(values).where(where))
        session.commit()
        return result

    def delete(self, table: str, where: str):
        """
        Delete a record from a table.
        :param table: The name of the table.
        :param where: The condition for the delete.
        :return: The result of the delete operation.
        """
        session = self.get_session()
        result = session.execute(table.delete().where(where))
        session.commit()
        return result

    def create_table(self, table):
        """
        Create a table in the database.
        :param table: The table to create.
        :return: The result of the create operation.
        """
        session = self.get_session()
        result = session.execute(table.create())
        session.commit()
        return result

    def drop_table(self, table):
        """
        Drop a table from the database.
        :param table: The table to drop.
        :return: The result of the drop operation.
        """
        session = self.get_session()
        result = session.execute(table.drop())
        session.commit()
        return result

    def get_all_tables(self):
        """
        Get all tables in the database.
        :return: A list of all tables in the database.
        """
        session = self.get_session()
        result = session.execute("SHOW TABLES")
        session.commit()
        return [row[0] for row in result.fetchall()]

    def get_table_columns(self, table: str):
        """
        Get all columns in a table.
        :param table: The name of the table.
        :return: A list of all columns in the table.
        """
        session = self.get_session()
        result = session.execute(f"SHOW COLUMNS FROM {table}")
        session.commit()
        return [row[0] for row in result.fetchall()]

    def get_table_info(self, table: str):
        """
        Get information about a table.
        :param table: The name of the table.
        :return: A dictionary with information about the table.
        """
        session = self.get_session()
        result = session.execute(f"SHOW TABLE STATUS LIKE '{table}'")
        session.commit()
        return dict(result.fetchone())

    def get_table_row_count(self, table: str):
        """
        Get the number of rows in a table.
        :param table: The name of the table.
        :return: The number of rows in the table.
        """
        session = self.get_session()
        result = session.execute(f"SELECT COUNT(*) FROM {table}")
        session.commit()
        return result.fetchone()[0]

    def get_table_size(self, table: str):
        """
        Get the size of a table.
        :param table: The name of the table.
        :return: The size of the table in bytes.
        """
        session = self.get_session()
        result = session.execute(f"SHOW TABLE STATUS LIKE '{table}'")
        session.commit()
        return result.fetchone()[6]

    def get_table_indexes(self, table: str):
        """
        Get all indexes in a table.
        :param table: The name of the table.
        :return: A list of all indexes in the table.
        """
        session = self.get_session()
        result = session.execute(f"SHOW INDEX FROM {table}")
        session.commit()
        return [row[2] for row in result.fetchall()]

    def get_table_primary_key(self, table: str):
        """
        Get the primary key of a table.
        :param table: The name of the table.
        :return: The primary key of the table.
        """
        session = self.get_session()
        result = session.execute(f"SHOW KEYS FROM {table} WHERE Key_name = 'PRIMARY'")
        session.commit()
        return [row[4] for row in result.fetchall()]

    def get_table_foreign_keys(self, table: str):
        """
        Get all foreign keys in a table.
        :param table: The name of the table.
        :return: A list of all foreign keys in the table.
        """
        session = self.get_session()
        result = session.execute(f"SHOW CREATE TABLE {table}")
        session.commit()
        return [row[1] for row in result.fetchall()]

    def get_table_constraints(self, table: str):
        """
        Get all constraints in a table.
        :param table: The name of the table.
        :return: A list of all constraints in the table.
        """
        session = self.get_session()
        result = session.execute(f"SHOW CREATE TABLE {table}")
        session.commit()
        return [row[1] for row in result.fetchall()]

    def get_table_triggers(self, table: str):
        """
        Get all triggers in a table.
        :param table: The name of the table.
        :return: A list of all triggers in the table.
        """
        session = self.get_session()
        result = session.execute(f"SHOW TRIGGERS LIKE '{table}'")
        session.commit()
        return [row[0] for row in result.fetchall()]