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

from dotenv import load_dotenv
from fastapi import FastAPI

from GraphQL.GraphQL import GraphQL
from .Tasks.taskmanager import TaskManager

app = FastAPI()


def start_graphql_server(app: FastAPI, path: str = "/"):
    """
    Start the GraphQL server with the given FastAPI application.

    :param app: The FastAPI application instance.
    :param path: The path to add the GraphQL route to. Default is "/".
    """
    graphql = GraphQL(app)
    graphql.add_graphql_route(path)
    graphql.run()


def start_taskmanager():
    """
    Placeholder function for starting the task manager.
    This function can be implemented to handle background tasks.
    """
    tm = TaskManager()
    _ = tm.list_tasks()


@app.on_event("shutdown")
async def on_shutdown():
    task_manager = TaskManager()
    task_manager._pause_all_running_tasks()


def main():
    """Main function to run the AMM core functionality."""
    load_dotenv(".env")

    start_graphql_server(app, "/")
    start_taskmanager()


if __name__ == "__main__":
    main()
