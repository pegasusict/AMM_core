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
GraphQL Server class for handling GraphQL queries and mutations.
This class is used to add a GraphQL route to the FastAPI application.
"""


from fastapi import FastAPI
import uvicorn


class GraphQL:
    """
    GraphQL Server class for handling GraphQL queries and mutations.
    This class is used to add a GraphQL route to the FastAPI application.
    """

    def __init__(self, app: FastAPI):
        self.app = app

    def add_graphql_route(self, path: str):
        """
        GraphQL Server class for handling GraphQL queries and mutations.
        This class is used to add a GraphQL route to the FastAPI application.
        """

        @self.app.get(path)
        async def graphql_endpoint():
            return {"message": "GraphQL endpoint"}
        # Here you would add the actual GraphQL logic, such as schema and resolvers
        # For now, we just return a placeholder message
        # You can also add a POST method for handling GraphQL queries

        @self.app.post(path)
        async def graphql_post_endpoint():
            """GraphQL POST endpoint for handling GraphQL queries and mutations."""
            #todo: how to get the json data?
            return

    def run(self):
        """Run the GraphQL server."""
        uvicorn.run(self.app, host="127.0.1", port=8000)