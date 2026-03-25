ALLOWED_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "New": {"To Read", "Important", "Archive", "Outdated"},
    "To Read": {"Important", "Verified", "Archive", "Outdated"},
    "Important": {"Verified", "Archive", "Outdated", "To Read"},
    "Verified": {"Important", "Archive", "Outdated"},
    "Archive": {"Important", "Outdated"},
    "Outdated": {"Important", "Archive"},
}


def can_transition(current_status: str, target_status: str) -> bool:
    if current_status == target_status:
        return True
    return target_status in ALLOWED_STATUS_TRANSITIONS.get(current_status, set())

