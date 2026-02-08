import asyncio

import strawberry
from strawberry.types import Info

from core.dbmodels import DBTrack
from Singletons import DBInstance
from .playerservice import get_player_service
from .mapping import map_dbtrack_to_playertrack
from .schemas import PlayerTrack


@strawberry.type
class Subscription:
    """GraphQL Subscription to notify when track changes."""

    @strawberry.subscription
    async def track_changed(self, info: Info) -> PlayerTrack:  # type: ignore
        """
        Subscription that notifies when the next track starts playing
        for the current user.
        """
        user = getattr(info.context, "user", None)
        if user is None:
            raise ValueError("Authentication required")
        player = await get_player_service(user.id)
        while True:
            await asyncio.sleep(1)  # Polling interval
            if player.queue:
                async for session in DBInstance.get_session():
                    track = await session.get(DBTrack, player.queue[0])
                    if track:
                        yield map_dbtrack_to_playertrack(track)  # type: ignore
