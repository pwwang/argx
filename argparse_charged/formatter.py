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

    def _metavar_formatter(self, action, default_metavar):
        """Format metavar in case there are namespace in it"""
        fmt = super()._metavar_formatter(action, default_metavar)

        def format(tuple_size):
            result = fmt(tuple_size)
            return tuple(
                r.split(".")[-1] if isinstance(r, str) else r for r in result
            )

        return format

    def add_arguments(self, actions, plus) -> None:
        """Add arguments to the formatter"""
        for action in actions:
            if not plus and not showable(action):
                action.help = SUPPRESS
            self.add_argument(action)
