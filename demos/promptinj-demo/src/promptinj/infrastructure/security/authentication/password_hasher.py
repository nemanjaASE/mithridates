import bcrypt


class BcryptPasswordHasher:
    """Hashes passwords with bcrypt and verifies them in constant time.

    Args:
        rounds: The bcrypt cost factor.
    """

    def __init__(self, rounds: int = 10) -> None:
        self._rounds = rounds

    def hash(self, password: str) -> str:
        """Hashes a password with a random salt.

        Args:
            password: The plaintext password.

        Returns:
            The bcrypt hash.
        """
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=self._rounds)).decode()

    def verify(self, password: str, password_hash: str) -> bool:
        """Checks a password against a hash.

        Args:
            password: The plaintext password.
            password_hash: The stored hash.

        Returns:
            Whether they match.
        """
        try:
            return bcrypt.checkpw(password.encode(), password_hash.encode())
        except ValueError:
            return False  # malformed stored hash
