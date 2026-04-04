import os

os.environ.pop("SSLKEYLOGFILE", None)

from kb_bot.bot.router import build_router


def _first_message_handler_name(router) -> str | None:
    handlers = router.message.handlers
    if not handlers:
        return None
    callback = handlers[0].callback
    return getattr(callback, "__name__", None)


def test_forward_save_router_has_priority_over_fsm_message_handlers() -> None:
    root = build_router(None)
    names = [_first_message_handler_name(sub_router) for sub_router in root.sub_routers]
    forward_index = names.index("save_forward_handler")
    menu_index = names.index("topic_create_name")
    assert forward_index < menu_index
