"""Encodes a vector as a pgvector literal, for writing and for querying."""


def vector_literal(vector: list[float]) -> str:
    """Encodes a vector with six decimals.

    Args:
        vector: The vector.

    Returns:
        The pgvector literal.
    """
    return "[" + ",".join(f"{x:.6f}" for x in vector) + "]"
