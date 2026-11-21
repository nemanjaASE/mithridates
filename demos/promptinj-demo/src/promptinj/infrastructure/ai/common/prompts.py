"""Prompt templates as `.md` files, with per-assistant overrides.

    _default/<stem>.md          the template every assistant gets
    <assistant name>/<stem>.md  an assistant's replacement for it

An override may contain `{default}`, which is replaced by the default template. A missing
template raises `ConfigurationError` at startup. Only templates are format strings; the
question, the context and the user id are inserted as values.
"""
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from string import Formatter

from ....application.errors import ConfigurationError
from ....domain.entities import RetrievedChunk

DEFAULT_DIR = "_default"
_SUFFIX = ".md"


def render_context(chunks: list[RetrievedChunk]) -> str:
    """Renders retrieved documents as the text the model sees.

    Args:
        chunks: The retrieved documents.

    Returns:
        The context text.
    """
    lines = [f"- {chunk.text}" for chunk in chunks]
    return "\n".join(lines) if lines else "- (no matching documents)"


class UnsupportedTemplate(ValueError):
    """A template uses `str.format` syntax other than a simple `{name}`."""


def _placeholders(template: str) -> set[str]:
    """Returns the placeholder names a template uses.

    Only simple `{name}` placeholders are allowed; literal braces are written `{{` and `}}`.

    Args:
        template: The template text.

    Returns:
        The placeholder names.

    Raises:
        UnsupportedTemplate: The template uses positional fields, attribute or index access,
            format specs or conversions.
    """
    names: set[str] = set()
    for _, field, spec, conversion in Formatter().parse(template):
        if field is None:
            continue
        if field == "" or field.isdigit():
            raise UnsupportedTemplate(f"positional placeholder {{{field}}}")
        if "." in field or "[" in field:
            raise UnsupportedTemplate(f"attribute or index access in {{{field}}}")
        if spec:
            raise UnsupportedTemplate(f"format specification in {{{field}:{spec}}}")
        if conversion:
            raise UnsupportedTemplate(f"conversion in {{{field}!{conversion}}}")
        names.add(field)
    return names


@dataclass(frozen=True)
class PromptSet:
    """The templates of one assistant, resolved against `_default`."""

    name: str
    templates: Mapping[str, str]

    def __contains__(self, stem: str) -> bool:
        """Whether a template with this stem exists."""
        return stem in self.templates

    def raw(self, stem: str) -> str:
        """Returns a template's text.

        Args:
            stem: The template name.

        Returns:
            The unrendered template.

        Raises:
            ConfigurationError: The assistant has no such template.
        """
        try:
            return self.templates[stem]
        except KeyError:
            raise ConfigurationError(
                f"Assistant {self.name!r} did not declare the prompt {stem!r}."
            ) from None

    def validate(self, available: Iterable[str]) -> None:
        """Checks that every placeholder will be supplied.

        Args:
            available: The placeholder names the caller will supply.

        Raises:
            ConfigurationError: A template uses a placeholder that is not available.
        """
        known = set(available)
        for stem, template in self.templates.items():
            try:
                used = _placeholders(template)
            except UnsupportedTemplate as exc:
                raise ConfigurationError(
                    f"Prompt {self.name}/{stem}{_SUFFIX} uses {exc}. Only simple named "
                    "placeholders like {current_user_id} are supported."
                ) from None
            unknown = used - known
            if unknown:
                raise ConfigurationError(
                    f"Prompt {self.name}/{stem}{_SUFFIX} uses "
                    f"{', '.join(sorted(repr(u) for u in unknown))}, which nothing "
                    f"supplies. Available: {', '.join(sorted(known))}."
                )

    def render(self, stem: str, **values: object) -> str:
        """Renders a template.

        Args:
            stem: The template name.
            **values: The values to insert.

        Returns:
            The rendered text.

        Raises:
            ConfigurationError: The template is missing or a value is not supplied.
        """
        try:
            return self.raw(stem).format(**values)
        except KeyError as exc:
            raise ConfigurationError(
                f"Prompt {self.name}/{stem}{_SUFFIX} uses the placeholder {exc.args[0]!r}, "
                "which nothing supplies."
            ) from None


class PromptLoader:
    """Reads the prompt templates at startup.

    Args:
        root: The prompt directory.
    """

    def __init__(self, root: Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        """The prompt directory."""
        return self._root

    def load(self, name: str, stems: tuple[str, ...]) -> PromptSet:
        """Loads an assistant's templates.

        Args:
            name: The assistant name.
            stems: The template names the assistant needs.

        Returns:
            The templates.

        Raises:
            ConfigurationError: A template is missing.
        """
        return PromptSet(name=name, templates={s: self._template(name, s) for s in stems})

    def _template(self, name: str, stem: str) -> str:
        """Returns the assistant's template, with `{default}` resolved."""
        default = self._read(self._root / DEFAULT_DIR / f"{stem}{_SUFFIX}")
        override = self._read(self._root / name / f"{stem}{_SUFFIX}")
        if override is None:
            if default is None:
                raise ConfigurationError(
                    f"No prompt {stem}{_SUFFIX} for assistant {name!r}: looked in "
                    f"{self._root / name} and {self._root / DEFAULT_DIR}."
                )
            return default
        if "{default}" in override:
            if default is None:
                raise ConfigurationError(
                    f"{name}/{stem}{_SUFFIX} refers to {{default}}, but "
                    f"{DEFAULT_DIR}/{stem}{_SUFFIX} does not exist."
                )
            override = override.replace("{default}", default)
        return override

    @staticmethod
    def _read(path: Path) -> str | None:
        """Returns a file's text, or None if it does not exist."""
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8").strip()
