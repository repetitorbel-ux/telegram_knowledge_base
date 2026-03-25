class DomainError(Exception):
    pass


class DuplicateEntryError(DomainError):
    def __init__(self, dedup_hash: str) -> None:
        super().__init__("Duplicate entry detected")
        self.dedup_hash = dedup_hash


class TopicNotFoundError(DomainError):
    pass


class EntryNotFoundError(DomainError):
    pass


class StatusNotFoundError(DomainError):
    pass


class InvalidStatusTransitionError(DomainError):
    pass
