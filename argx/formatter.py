from __future__ import annotations

import re
import string
from typing import TYPE_CHECKING, Callable, Iterable, List, Tuple
from argparse import SUPPRESS, Action, HelpFormatter, _SubParsersAction

from .utils import showable

if TYPE_CHECKING:
    from argparse import _ArgumentGroup


def _wrap_text(text: str, width: int, indent: str = "") -> List[str]:
    """Wrap text to width and keep the indent"""
    import textwrap

    def _wrap_line(line: str) -> List[str]:
        leading_space = line[: len(line) - len(line.lstrip())]
        rest_text = line[len(leading_space) :]
        if rest_text.startswith("- "):
            leading_space += "  "
        return textwrap.wrap(
            line,
            width,
            initial_indent=indent,
            subsequent_indent=leading_space + indent,
        )

    lines = text.splitlines()
    out = []
    for line in lines:
        out.extend(_wrap_line(line))
    return out


class ChargedHelpFormatter(HelpFormatter):
    """Help formatter for pyparam"""

    def _format_action(self, action: Action) -> str:
        """Skip header for subparsers"""
        if isinstance(action, _SubParsersAction):
            parts = []
            for subaction in self._iter_indented_subactions(action):
                parts.append(super()._format_action(subaction))
            return self._join_parts(parts)

        return super()._format_action(action)

    def _format_usage(
        self,
        usage: str | None,
        actions: Iterable[Action],
        groups: Iterable[_ArgumentGroup],
        prefix: str | None,
    ) -> str:
        out = super()._format_usage(usage, actions, groups, prefix)
        len_prefix = len(prefix) if prefix else 5  # "usage:", exclude colon
        prefix, rest = out[: len_prefix], out[len_prefix :]
        return f"\033[1m\033[4m{string.capwords(prefix)}\033[0m\033[0m{rest}"

    def _metavar_formatter(
        self,
        action: Action,
        default_metavar: str,
    ) -> Callable[[int], Tuple[str, ...]]:
        """Format metavar in case there are namespace in it"""
        fmt = super()._metavar_formatter(action, default_metavar)

        def format(tuple_size):
            result = fmt(tuple_size)
            return tuple(
                r.split(".")[-1] if isinstance(r, str) else r for r in result
            )

        return format

    def add_arguments(  # type: ignore[override]
        self,
        actions: Iterable[Action],
        plus: bool,
    ) -> None:
        """Add arguments to the formatter

        Modify to handle plus.
        """
        for action in actions:
            if not plus and not showable(action):
                action.help = SUPPRESS

            if (
                action.help is not SUPPRESS
                and action.default is not None
                and action.default is not SUPPRESS
            ):
                help = action.help or ""

                if not re.search(r"\[(?:no)?default: ", help):
                    sep = "\n" if "\n" in help else " " if help else ""
                    action.help = (
                        f"{help}{sep}[default: %(default)s]"
                    )

            if (
                isinstance(action.help, str)
                and action.help.rstrip().endswith("[nodefault]")
            ):
                action.help = action.help.rstrip()[:-11].rstrip()

            self.add_argument(action)

    def _split_lines(self, text: str, width: int) -> List[str]:
        return _wrap_text(text, width)

    def _fill_text(self, text: str, width: int, indent: str) -> str:
        return "\n".join(_wrap_text(text, width, indent))
