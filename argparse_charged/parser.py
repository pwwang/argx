from __future__ import annotations

import sys
from typing import Sequence
from pathlib import Path
from gettext import gettext as _
from argparse import (
    SUPPRESS,
    _ArgumentGroup as APArgumentGroup,
    ArgumentParser as APArgumentParser,
    Namespace,
)

from simpleconf import Config

from . import type_
from .utils import (
    get_ns_dest,
    import_pyfile,
    update_actions_with_preset,
    add_attribute,
    showable,
)
from .action import (
    StoreAction,
    StoreConstAction,
    StoreTrueAction,
    StoreFalseAction,
    AppendAction,
    AppendConstAction,
    CountAction,
    ExtendAction,
    ListAction,
    HelpAction,
)
from .formatter import ChargedHelpFormatter


@add_attribute("level", 0)
class ArgumentParser(APArgumentParser):
    """Class to handle command line arguments and configuration files"""

    def __init__(
        self,
        *args,
        exit_on_void=True,
        formatter_class=ChargedHelpFormatter,
        **kwargs,
    ):
        fromfile_prefix_chars = kwargs.pop("fromfile_prefix_chars", "@")
        old_add_help = kwargs.pop("add_help", True)
        kwargs["add_help"] = False
        super().__init__(
            *args,
            **kwargs,
            formatter_class=formatter_class,
            fromfile_prefix_chars=fromfile_prefix_chars,
        )
        self.exit_on_void = exit_on_void

        self.register("action", None, StoreAction)
        self.register("action", "store", StoreAction)
        self.register("action", "store_const", StoreConstAction)
        self.register("action", "store_true", StoreTrueAction)
        self.register("action", "store_false", StoreFalseAction)
        self.register("action", "append", AppendAction)
        self.register("action", "append_const", AppendConstAction)
        self.register("action", "count", CountAction)
        self.register("action", "extend", ExtendAction)
        self.register("action", "list", ListAction)
        self.register("action", "help", HelpAction)
        self.register("type", "py", type_.py)
        self.register("type", "json", type_.json)
        self.register("type", "path", Path)
        self.register("type", "auto", type_.auto)

        default_prefix = (
            '-' if '-' in self.prefix_chars else self.prefix_chars[0]
        )
        if old_add_help is True:
            self.add_argument(
                f"{default_prefix}h",
                f"{default_prefix * 2}help",
                action="help",
                default=SUPPRESS,
                help=_("show help message and exit"),
            )
        elif old_add_help == "+":
            self.add_argument(
                f"{default_prefix}h",
                f"{default_prefix * 2}help",
                f"{default_prefix}h+",
                f"{default_prefix * 2}help+",
                action="help",
                default=SUPPRESS,
                help=_(
                    "show help message (with + to show more options) and exit"
                ),
            )
        self.add_help = old_add_help

    def add_subparser(self, name, **kwargs):
        if self._subparsers is None:
            self._subparsers = self.add_subparsers(
                title=_("subcommands"),
                required=True,
                dest="COMMAND" if self.level == 0 else f"COMMAND{self.level+1}",
            )
        kwargs.setdefault("help", f"The {name} command")
        return self._subparsers.add_parser(name, level=self.level + 1, **kwargs)

    add_command = add_subparser

    def parse_known_args(
        self,
        args: Sequence[str] | None = None,
        namespace: Namespace | None = None,
    ) -> tuple[Namespace, list[str]]:
        """Parse known arguments.

        If no arguments are provided, and exit_on_void is True, then
        an error is given and the program exits.
        """
        if args is None:  # pragma: no cover
            # args default to the system args
            args = sys.argv[1:]
        else:
            # make sure that args are mutable
            args = list(args)

        if not self.fromfile_prefix_chars:
            new_args = args
        else:
            # Setup the defaults if a configuration file is given by @config.ini
            new_args = []
            for arg in args:
                if (
                    not arg
                    or arg[0] not in self.fromfile_prefix_chars
                    or arg.endswith(".txt")
                ):
                    new_args.append(arg)
                else:
                    try:
                        conffile = arg[1:]
                        if conffile.endswith(".py"):
                            conf = import_pyfile(conffile)
                            update_actions_with_preset(self._actions, conf)
                        else:
                            conf = Config.load(conffile)
                            update_actions_with_preset(self._actions, conf)
                    except Exception as e:
                        self.error(f"Cannot import [{conffile}]: {e}")

        # default Namespace built from parser defaults
        if namespace is None:
            namespace = Namespace()

        # add any action defaults that aren't present
        # Do this mainly for namespace actions, like "--group.abc"
        for action in self._actions:
            if "." not in action.dest:
                # Leave the normal actions to the super class
                continue

            ns, last_key = get_ns_dest(namespace, action.dest)
            if not hasattr(ns, last_key):
                setattr(ns, last_key, action.default)

        parsed_args, argv = super().parse_known_args(new_args, namespace)
        if not argv and not args and self.exit_on_void:
            self.error("No arguments provided")

        return parsed_args, argv

    def _add_action(self, action):
        if "." not in action.dest or isinstance(action, APArgumentGroup):
            return super()._add_action(action)

        # Split the destination into a list of keys
        keys = action.dest.split(".")
        group = None

        for i in range(1, len(keys)):
            ns_key = ".".join(keys[: -i])
            for action_group in self._action_groups:
                if (
                    isinstance(action_group, _NamespaceArgumentGroup)
                    and action_group.name == ns_key
                ):
                    group = action_group
                    break
            if group is not None:
                break

        if group is None:
            group = self.add_namespace(keys[0])

        return group._add_action(action)

    def add_namespace(self, name, title=None, **kwargs):
        """Add a namespace to the parser"""
        # Check if the namespace already exists
        for action_group in self._action_groups:
            if (
                isinstance(action_group, _NamespaceArgumentGroup)
                and action_group.name == name
            ):
                raise ValueError(f"Namespace '{name}' already exists")

        if title is None:
            title = f"{_('namespace')} '{name}'"

        group = _NamespaceArgumentGroup(self, title, name=name, **kwargs)
        self._action_groups.append(group)
        return group

    def add_argument_group(self, *args, **kwargs):
        group = _ArgumentGroup(self, *args, **kwargs)
        self._action_groups.append(group)
        return group

    def print_help(self, plus, file=None):
        if file is None:
            file = sys.stdout

        self._print_message(self.format_help(plus=plus), file)

    def format_help(self, plus=True) -> str:

        formatter = self._get_formatter()

        # usage
        formatter.add_usage(self.usage, self._actions,
                            self._mutually_exclusive_groups)

        # description
        formatter.add_text(self.description)

        # positionals, optionals and user-defined groups
        for action_group in self._action_groups:
            if not plus and not showable(action_group):
                for action in action_group._group_actions:
                    # hide them in usage as well
                    action.help = SUPPRESS
                continue
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(action_group._group_actions, plus)
            formatter.end_section()

        # epilog
        formatter.add_text(self.epilog)

        # determine help from format above
        return formatter.format_help()

    def _add_decedents(
        self,
        mutually_exclusive_groups,
        groups,
        namespaces,
        arguments,
        commands,
    ):
        """Add the decedents of the parser"""
        # Add the mutually exclusive groups
        for group_args in mutually_exclusive_groups:
            group_arguments = group_args.pop("arguments", [])
            group = self.add_mutually_exclusive_group(**group_args)
            for argument in group_arguments:
                flags = argument.pop("flags", [])
                group.add_argument(*flags, **argument)

        # Add the groups
        for group_args in groups:
            group_arguments = group_args.pop("arguments", [])
            group = self.add_argument_group(**group_args)
            for argument in group_arguments:
                flags = argument.pop("flags", [])
                group.add_argument(*flags, **argument)

        # Add the namespaces
        for namespace in namespaces:
            namespace_arguments = namespace.pop("arguments", [])
            self.add_namespace(**namespace)
            arguments.extend(namespace_arguments)

        # Add the arguments
        for argument in arguments:
            flags = argument.pop("flags", [])
            self.add_argument(*flags, **argument)

        # Add the commands
        for command_args in commands:
            command_mutually_exclusive_groups = command_args.pop(
                "mutually_exclusive_groups",
                [],
            )
            command_groups = command_args.pop("groups", [])
            command_namespaces = command_args.pop("namespaces", [])
            command_arguments = command_args.pop("arguments", [])
            command_commands = command_args.pop("commands", [])
            command = self.add_command(**command_args)
            command._add_decedents(
                command_mutually_exclusive_groups,
                command_groups,
                command_namespaces,
                command_arguments,
                command_commands,
            )

    def _registry_get(self, registry_name, value, default=None):
        # Allow type to be string
        if (
            registry_name == "type"
            and isinstance(value, str)
            and default == value
        ):
            import builtins
            # "int", "float", "str", "open", etc
            return self._registries[registry_name].get(
                value,
                getattr(builtins, value, None),
            )

        # Not using super() because _ArgumentGroup can also use it
        return APArgumentGroup._registry_get(
            self,
            registry_name,
            value,
            default,
        )

    @classmethod
    def from_config(cls, *configs):
        """Create an ArgumentParser from a configuration file"""
        config = Config.load(*configs)
        mutually_exclusive_groups = config.pop("mutually_exclusive_groups", [])
        groups = config.pop("groups", [])
        namespaces = config.pop("namespaces", [])
        arguments = config.pop("arguments", [])
        commands = config.pop("commands", [])
        parser = cls(**config)
        parser._add_decedents(
            mutually_exclusive_groups,
            groups,
            namespaces,
            arguments,
            commands,
        )
        return parser


@add_attribute("show", True)
class _ArgumentGroup(APArgumentGroup):

    _registry_get = ArgumentParser._registry_get


@add_attribute("name")
class _NamespaceArgumentGroup(_ArgumentGroup):
    ...
