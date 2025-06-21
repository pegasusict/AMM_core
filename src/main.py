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

"""Base file for AMM core functionality."""

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from enums import AppStatus
from GraphQL.graphql import GraphQL
from Tasks.taskmanager import TaskManager
from Singletons import DB
from dbmodels import DBFile

STAGE = AppStatus.DEVELOPMENT
DEBUG = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    task_manager = TaskManager()

    yield  # App runs here.

    # Shutdown
    task_manager.shutdown()


app = FastAPI(lifespan=lifespan)

db = DB()


def start_graphql_server(app: FastAPI, path: str = "/"):
    """
    Start the GraphQL server with the given FastAPI application.

    :param app: The FastAPI application instance.
    :param path: The path to add the GraphQL route to. Default is "/".
    """
    graphql = GraphQL(app)
    graphql.add_graphql_route(path)
    graphql.run()


@app.get("/stream/{file_id}")
def stream_file(file_id: int):
    session: Session = db.get_session()
    db_file: DBFile = session.get_one(DBFile, DBFile.id == file_id)
    file_path = Path(db_file.file_path)

    if not file_path.exists():
        return {"error": "File not found."}

    def iterfile():
        with open(file_path, mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(iterfile(), media_type="audio/mpeg")


def main():
    """Main function to run the AMM core functionality."""
    load_dotenv()
    start_graphql_server(app, "/")


if __name__ == "__main__":
    main()
