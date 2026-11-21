from dataclasses import dataclass, field


@dataclass(frozen=True)
class DatabaseServer:
    """Host, port and name of the database."""

    host: str
    port: int
    name: str


@dataclass(frozen=True)
class DatabaseCredentials:
    """User and password of one database account."""

    user: str
    password: str = field(repr=False)  # must not end up in the log via repr()
