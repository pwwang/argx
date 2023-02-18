from __future__ import annotations
from typing import TYPE_CHECKING, Any, Sequence
from argparse import (
    _HelpAction,
    _StoreAction,
    _StoreConstAction,
    _AppendAction,
    _AppendConstAction,
    _CountAction,
    # Introduced in python3.9
    # _ExtendAction,
)

from .utils import get_ns_dest, copy_items, add_attribute

if TYPE_CHECKING:
    from argparse import Namespace
    from .parser import ArgumentParser


@add_attribute("show", True)
class StoreAction(_StoreAction):
    def __call__(  # type: ignore[override]
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        ns, dest = get_ns_dest(namespace, self.dest)
        setattr(ns, dest, values)


@add_attribute("show", True)
class StoreConstAction(_StoreConstAction):
    def __call__(  # type: ignore[override]
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        ns, dest = get_ns_dest(namespace, self.dest)
        setattr(ns, dest, self.const)


class StoreTrueAction(StoreConstAction):
    def __init__(self, *args, **kwargs):
        kwargs["const"] = True
        super().__init__(*args, **kwargs)


class StoreFalseAction(StoreConstAction):
    def __init__(self, *args, **kwargs):
        kwargs["const"] = False
        super().__init__(*args, **kwargs)


@add_attribute("show", True)
class AppendAction(_AppendAction):
    def __call__(  # type: ignore[override]
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        ns, dest = get_ns_dest(namespace, self.dest)
        items = getattr(ns, dest, None)
        items = copy_items(items)
        items.append(values)
        setattr(ns, dest, items)


@add_attribute("show", True)
class AppendConstAction(_AppendConstAction):
    def __call__(  # type: ignore[override]
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        ns, dest = get_ns_dest(namespace, self.dest)
        items = getattr(ns, dest, None)
        items = copy_items(items)
        items.append(self.const)
        setattr(ns, dest, items)


@add_attribute("show", True)
class CountAction(_CountAction):
    def __call__(  # type: ignore[override]
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        ns, dest = get_ns_dest(namespace, self.dest)
        value = getattr(ns, dest, None)
        if value is None:
            value = 0
        setattr(ns, dest, value + 1)


class ExtendAction(AppendAction):
    def __call__(  # type: ignore[override]
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        ns, dest = get_ns_dest(namespace, self.dest)
        items = getattr(ns, dest, None)
        items = copy_items(items)
        items.extend(values)
        setattr(ns, dest, items)


class ListAction(AppendAction):
    """Append a list of values to the list of values for a given option"""

    def __init__(self, *args, **kwargs):
        self.received = False
        super().__init__(*args, **kwargs)

    def __call__(  # type: ignore[override]
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        ns, dest = get_ns_dest(namespace, self.dest)
        if not self.received:
            items = []
            self.received = True
        else:
            items = getattr(ns, dest, None)
            items = copy_items(items)

        items.append(values)
        setattr(ns, dest, items)


@add_attribute("show", True)
class HelpAction(_HelpAction):
    def __call__(  # type: ignore[override]
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        parser.print_help(
            plus=(
                (parser.add_help == "+" and "+" in option_string)
                or parser.add_help is True
            )
        )
        parser.exit()
