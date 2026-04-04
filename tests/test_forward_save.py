import os
from types import SimpleNamespace

os.environ.pop("SSLKEYLOGFILE", None)

from kb_bot.bot.handlers.forward_save import _is_forward_like_message


def test_is_forward_like_message_detects_forward_origin() -> None:
    message = SimpleNamespace(
        forward_origin=object(),
        forward_from=None,
        forward_from_chat=None,
        forward_sender_name=None,
        is_automatic_forward=False,
    )
    assert _is_forward_like_message(message) is True


def test_is_forward_like_message_detects_automatic_forward() -> None:
    message = SimpleNamespace(
        forward_origin=None,
        forward_from=None,
        forward_from_chat=None,
        forward_sender_name=None,
        is_automatic_forward=True,
    )
    assert _is_forward_like_message(message) is True


def test_is_forward_like_message_returns_false_for_regular_message() -> None:
    message = SimpleNamespace(
        forward_origin=None,
        forward_from=None,
        forward_from_chat=None,
        forward_sender_name=None,
        is_automatic_forward=False,
    )
    assert _is_forward_like_message(message) is False
