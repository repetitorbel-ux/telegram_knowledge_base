from kb_bot.domain.status_machine import can_transition


def test_status_transition_allowed() -> None:
    assert can_transition("New", "To Read") is True
    assert can_transition("Important", "Verified") is True
    assert can_transition("Archive", "Important") is True


def test_status_transition_blocked() -> None:
    assert can_transition("New", "Verified") is False
    assert can_transition("To Read", "New") is False

