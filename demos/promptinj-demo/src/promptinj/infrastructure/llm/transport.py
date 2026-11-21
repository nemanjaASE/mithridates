"""Exceptions that mean the model could not be reached.

Verified against langchain-ollama 1.1.0, ollama 0.6.3 and httpx 0.28.1. `ValueError` is
not included, so a `ValueError` raised by this code is not reported as unavailability.
"""
import httpx
import ollama

TRANSPORT_FAILURES: tuple[type[BaseException], ...] = (
    # Connect refused, DNS failure, read/connect timeout, and a non-2xx response.
    httpx.HTTPError,
    # The client could not build or send the request.
    ollama.RequestError,
    # The Ollama API answered with an error: model not pulled, bad options, overload.
    ollama.ResponseError,
)
