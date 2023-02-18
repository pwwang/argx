from typing import Callable, Iterable, Tuple
from argparse import SUPPRESS, Action, HelpFormatter, _SubParsersAction

from .utils import showable


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
            self.add_argument(action)
