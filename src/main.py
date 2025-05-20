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


def main():
    """Main function to run the AMM core functionality."""
    load_dotenv(".env")

    app = FastAPI()

    graphql = GraphQL(app)
    graphql.add_graphql_route("/")
    graphql.run()


if __name__ == "__main__":
    main()
