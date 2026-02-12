from __future__ import annotations

import datetime as dt

from Server.mutation import _build_google_user_insert_params
from core.enums import UserRole


def test_google_login_insert_params_have_non_null_dob() -> None:
    now = dt.datetime.now(dt.timezone.utc)
    params = _build_google_user_insert_params(
        token_info={
            "email": "pegasus.ict@gmail.com",
            "given_name": "Mattijs",
            "family_name": "Snepvangers",
        },
        username="pegasus.ict",
        role=UserRole.USER,
        now=now,
    )

    assert params["email"] == "pegasus.ict@gmail.com"
    assert params["username"] == "pegasus.ict"
    assert params["role"] == UserRole.USER.value
    assert params["date_of_birth"] is not None
    assert isinstance(params["date_of_birth"], dt.datetime)
    assert params["created_at"] == now
    assert params["updated_at"] == now
