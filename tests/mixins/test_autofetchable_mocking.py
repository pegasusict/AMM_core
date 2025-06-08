# test_autofetchable_mocking.py

from unittest.mock import MagicMock, patch
from sqlmodel import SQLModel
from mixins.autofetch import AutoFetchable


class DummyModel(AutoFetchable, SQLModel):
    pass


def test_load_full_triggers_recursive_loader():
    mock_session = MagicMock()
    dummy_class = DummyModel

    # Simulate a primary key for the dummy model
    dummy_class.__table__.primary_key.columns = [MagicMock()]  # type: ignore
    dummy_class.__name__ = "DummyModel"

    with patch.object(AutoFetchable, "_build_recursive_loads", return_value=[]) as mock_loader:
        # Call load_full (static method inherited by DummyModel)
        DummyModel.load_full(session=mock_session, object_id=123, depth=2)

        # Ensure recursive loader was called
        mock_loader.assert_called_once_with(depth=2)

        # Ensure SQL execution was triggered
        mock_session.exec.assert_called_once()
