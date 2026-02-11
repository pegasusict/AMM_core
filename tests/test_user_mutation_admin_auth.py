from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

pytest.importorskip("dotenv")

from core.enums import UserRole
from Server.mutation import Mutation, DBInstance
from Server.schemas import UserCreateInput, UserUpdateInput


class _FakeSession:
    def __init__(self, existing_user: SimpleNamespace | None = None) -> None:
        self.existing_user = existing_user
        self.added: list[SimpleNamespace] = []
        self.deleted: SimpleNamespace | None = None
        self.committed = False

    def add(self, obj: SimpleNamespace) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, obj: SimpleNamespace) -> None:
        if obj.id is None:
            obj.id = 123

    async def get(self, _model: type[object], _user_id: int) -> SimpleNamespace | None:
        return self.existing_user

    async def delete(self, user: SimpleNamespace) -> None:
        self.deleted = user


def _info_with_role(role: UserRole | str) -> SimpleNamespace:
    return SimpleNamespace(context=SimpleNamespace(user=SimpleNamespace(id=1, role=role)))


@pytest.mark.parametrize("method_name,args", [("create_user", tuple()), ("update_user", (1,)), ("delete_user", (1,))])
def test_user_mutations_require_admin_role(monkeypatch: pytest.MonkeyPatch, method_name: str, args: tuple[object, ...]) -> None:
    async def _unexpected_session_gen():
        raise AssertionError("DB session should not be opened when caller is not admin")
        yield  # pragma: no cover

    monkeypatch.setattr(DBInstance, "get_session", staticmethod(lambda: _unexpected_session_gen()))
    mutation = Mutation()
    info = _info_with_role(UserRole.USER)

    if method_name == "create_user":
        data = UserCreateInput(username="newuser", email="newuser@example.com", password_hash="hash")
        coro = mutation.create_user(info, data)
    elif method_name == "update_user":
        data = UserUpdateInput(username="updated")
        coro = mutation.update_user(info, args[0], data)  # type: ignore[arg-type]
    else:
        coro = mutation.delete_user(info, args[0])  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Admin role required"):
        asyncio.run(coro)


def test_create_user_succeeds_for_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession()

    async def _session_gen():
        yield session

    monkeypatch.setattr(DBInstance, "get_session", staticmethod(lambda: _session_gen()))
    mutation = Mutation()
    info = _info_with_role("ADMIN")

    data = UserCreateInput(
        username="newadmincreateduser",
        email="newadmincreateduser@example.com",
        password_hash="hash",
    )
    created = asyncio.run(mutation.create_user(info, data))

    assert created.username == "newadmincreateduser"
    assert session.committed is True
    assert session.added
