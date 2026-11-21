"""Graph node that runs the spec's output filters on the model's output."""
from collections.abc import Callable

from .....application.errors import ConfigurationError
from ..deps import RagDeps
from ..spec import RagSpec
from ..state import RagState


def make_guard_output(spec: RagSpec, deps: RagDeps) -> Callable[[RagState], dict]:
    """Creates the node that checks the model's output.

    Args:
        spec: The assistant's specification.
        deps: The registered output filters.

    Returns:
        The node function.

    Raises:
        ConfigurationError: The spec names an unregistered filter.
    """
    try:
        filters = [deps.output_filters[name] for name in spec.output_filters]
    except KeyError as exc:
        raise ConfigurationError(
            f"Assistant {spec.name!r} asks for the output filter {exc.args[0]!r}, "
            f"which is not registered. Known: {', '.join(sorted(deps.output_filters))}."
        ) from None

    def guard_output(state: RagState) -> dict:
        """Returns the first block reason a filter reports, if any."""
        text = state.get("raw_output", "")
        reason = next((r for f in filters if (r := f.inspect(text))), None)
        return {"block_reason": reason}

    return guard_output
