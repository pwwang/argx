from __future__ import annotations

from argparse import Namespace
from typing import TYPE_CHECKING, Any, Callable, Type

if TYPE_CHECKING:
    from os import PathLike


def import_pyfile(pyfile: PathLike | str) -> dict:
    """Import a python file and return the globals dictionary"""
    import importlib.util

    spec = importlib.util.spec_from_file_location("config", pyfile)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return module.args
    except AttributeError:
        raise AttributeError("No `args` variables found") from None


def get_ns_dest(namespace: Namespace, dest: str) -> tuple[Namespace, str]:
    """Get the namespace and the last part of the dest to update"""
    if "." not in dest:
        return namespace, dest

    # Split the destination into a list of keys
    keys = dest.split(".")
    ns = namespace
    for key in keys[:-1]:
        value = getattr(ns, key, None)
        if value is None:
            value = Namespace()
            setattr(ns, key, value)
        ns = value

    return ns, keys[-1]


def copy_items(items: Any) -> Any:  # pragma: no cover
    """Copy items if needed, copied from argparse"""
    if items is None:
        return []
    # The copy module is used only in the 'append' and 'append_const'
    # actions, and it is needed only when the default value isn't a list.
    # Delay its import for speeding up the common case.
    if type(items) is list:
        return items[:]
    import copy
    return copy.copy(items)


def add_attribute(attr: str, default: Any = None) -> Callable[[Type], Type]:
    """Add an attribute to a class, working as a decorator"""
    def deco(cls):
        old_init = cls.__init__

        def new_init(self, *args, **kwargs):
            value = kwargs.pop(attr, default)
            setattr(self, attr, value)
            old_init(self, *args, **kwargs)

        cls.__init__ = new_init
        return cls

    return deco


def showable(obj: Any) -> bool:
    """Return True if the object is showable"""
    return getattr(obj, "show", True)
