"""Authenticator adapters: vulnerable and safe."""
from .safe_sql_authenticator import SafeSqlAuthenticator
from .vulnerable_sql_authenticator import VulnerableSqlAuthenticator

__all__ = ["SafeSqlAuthenticator", "VulnerableSqlAuthenticator"]
