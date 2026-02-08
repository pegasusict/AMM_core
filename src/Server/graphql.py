#  Copyleft 2021-2026 Mattijs Snepvangers.
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

import strawberry
from strawberry.fastapi import BaseContext
from fastapi import Request

from auth.dependencies import get_current_user
from core.dbmodels import DBUser
from .subscription import Subscription
from .mutation import Mutation
from .query import Query

# ------------------ GraphQL Schema ------------------

schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)


class RequestContext(BaseContext):
    request: Request  # type: ignore
    user: DBUser | None = None


async def get_context(request: Request) -> RequestContext:
    try:
        user = await get_current_user(request=request)  # type: ignore
    except Exception:
        user = None
    return RequestContext(request=request, user=user)  # type: ignore
