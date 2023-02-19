from __future__ import annotations

import sys
from typing import IO, TYPE_CHECKING, Any, Sequence
from pathlib import Path
from gettext import gettext as _
from argparse import (
    SUPPRESS,
    _SubParsersAction,
    _ArgumentGroup as APArgumentGroup,
    ArgumentParser as APArgumentParser,
    Namespace,
)

from simpleconf import Config

from . import type_
from .utils import (
    get_ns_dest,
    import_pyfile,
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

if TYPE_CHECKING:
    from argparse import _ActionT, _FormatterClass


@add_attribute("level", 0)
class ArgumentParser(APArgumentParser):
    """Class to handle command line arguments and configuration files"""

    def __init__(
        self,
        prog: str | None = None,
        usage: str | None = None,
        description: str | None = None,
        epilog: str | None = None,
        parents: Sequence[ArgumentParser] = [],
        formatter_class: _FormatterClass = ChargedHelpFormatter,
        prefix_chars: str = "-",
        fromfile_prefix_chars: str | None = "@",
        argument_default: Any = None,
        conflict_handler: str = "error",
        add_help: bool | str = True,
        allow_abbrev: bool = True,
        exit_on_error: bool = True,
        exit_on_void: bool = False,
    ) -> None:
        old_add_help = add_help
        add_help = False
        kwargs = {
            "prog": prog,
            "usage": usage,
            "description": description,
            "epilog": epilog,
            "parents": parents,
            "formatter_class": formatter_class,
            "prefix_chars": prefix_chars,
            "fromfile_prefix_chars": fromfile_prefix_chars,
            "argument_default": argument_default,
            "conflict_handler": conflict_handler,
            "add_help": add_help,
            "allow_abbrev": allow_abbrev,
        }
        if sys.version_info >= (3, 9):  # pragma: no cover
            kwargs["exit_on_error"] = exit_on_error
        super().__init__(**kwargs)
        self.exit_on_void = exit_on_void

        # Register our actions to override argparse's or add new ones
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

        # Add help option to support + for more options
        default_prefix = (
            "-" if "-" in self.prefix_chars else self.prefix_chars[0]
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
        # restore add_help
        self.add_help = old_add_help  # type: ignore[assignment]

    def add_subparser(self, name: str, **kwargs) -> ArgumentParser | Any:
        """Add a subparser directly.

        Instead of
        >>> subparsers = parser.add_subparsers(...)
        >>> parser_a = subparsers.add_parser("a", ...)
        >>> parser_b = subparsers.add_parser("b", ...)

        Now we can do
        >>> parser_a = parser.add_subparser("a", ...)

        Subparsers are automatically created when needed. This way, the
        title will be set to "subcommands" and the dest will be set to
        "COMMAND" or "COMMAND{level+1}" if the parser is not at level 0
        (main parser). The subparsers will be required.

        If you need to customize the subparsers, you can still use the
        add_subparsers method in standard argparse way.

        Args:
            name (str): The name of the subparser
            **kwargs: The arguments to pass to add_parser()

        Returns:
            ArgumentParser: The subparser
        """
        if self._subparsers is None:
            self._subparsers = self.add_subparsers(  # type: ignore[assignment]
                title=_("subcommands"),
                required=True,
                dest="COMMAND"
                if self.level == 0
                else f"COMMAND{self.level+1}",
            )
        kwargs.setdefault("help", f"The {name} command")
        return self._subparsers.add_parser(
            name, level=self.level + 1, **kwargs
        )

    add_command = add_subparser

    def parse_known_args(
        self,
        args: Sequence[str] | None = None,
        namespace: Namespace | None = None,
    ) -> tuple[Namespace, list[str]]:
        """Parse known arguments.

        Modify to handle exit_on_void and @file to load default values.
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
                        conf = arg[1:]
                        if conf.endswith(".py"):
                            conf = import_pyfile(conf)
                        self.set_defaults_from_configs(conf)
                    except Exception as e:
                        self.error(f"Cannot import [{conf}]: {e}")

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

    def set_defaults_from_configs(
        self,
        *configs: dict | str,
        optionalize: bool = True,
    ) -> None:
        """Set default values from configs.

        Args:
            *configs (dict | str): The configs to load, either a dict or
                a configuration file.
            optionalize (bool): Whether to make the arguments optional if
                they are required.
        """
        conf = Config.load(*configs)
        for action in self._actions:
            if "." not in action.dest and action.dest in conf:
                action.default = conf[action.dest]
                if optionalize:
                    action.required = False
            elif "." in action.dest:
                parts = action.dest.split(".")
                try:
                    cf = conf
                    for part in parts[:-1]:
                        cf = cf[part]
                    action.default = cf[parts[-1]]
                    if optionalize:
                        action.required = False
                except KeyError:
                    continue
            # see if we need to update subparsers
            if isinstance(action, _SubParsersAction):
                for name, subparser in action._name_parser_map.items():
                    if name in conf:
                        subparser.set_defaults_from_configs(
                            conf[name],
                            optionalize=optionalize,
                        )

    def _add_action(self, action: _ActionT) -> _ActionT:
        """Add an action to the parser.

        Modify to handle namespace actions, like "--group.abc"
        """
        if "." not in action.dest or isinstance(action, APArgumentGroup):
            return super()._add_action(action)

        # Split the destination into a list of keys
        keys = action.dest.split(".")
        group = None

        for i in range(1, len(keys)):
            ns_key = ".".join(keys[:-i])
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

    def add_namespace(
        self,
        name: str,
        title: str | None = None,
        **kwargs,
    ) -> _NamespaceArgumentGroup:
        """Add a namespace to the parser, which is actually an argument group

        Args:
            name (str): The name of the namespace
                The name should match the first part of the dest of its actions.
            title (str, optional): The title of the namespace.
            **kwargs: The arguments to pass to add_argument_group()

        Returns:
            _NamespaceArgumentGroup: The namespace
        """
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

    def add_argument_group(self, *args, **kwargs) -> _ArgumentGroup:
        """Add an argument group to the parser.

        Modify to handle show.
        """
        group = _ArgumentGroup(self, *args, **kwargs)
        self._action_groups.append(group)
        return group

    def print_help(  # type: ignore[override]
        self,
        plus: bool = False,
        file: IO[str] | None = None,
    ) -> None:
        """Print the help message.

        Modify to handle plus.
        """
        if file is None:
            file = sys.stdout

        self._print_message(self.format_help(plus=plus), file)

    def format_help(self, plus: bool = True) -> str:
        """Format the help message.

        Modify to handle plus.
        """
        formatter = self._get_formatter()

        # usage
        formatter.add_usage(
            self.usage, self._actions, self._mutually_exclusive_groups
        )

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
            formatter.add_arguments(  # type: ignore[call-arg]
                action_group._group_actions,
                plus,
            )
            formatter.end_section()

        # epilog
        formatter.add_text(self.epilog)

        # determine help from format above
        return formatter.format_help()

    def _add_decedents(
        self,
        mutually_exclusive_groups: list[dict],
        groups: list[dict],
        namespaces: list[dict],
        arguments: list[dict],
        commands: list[dict],
    ) -> None:
        """Add the decedents of the parser"""
        # Add the mutually exclusive groups
        for group_args in mutually_exclusive_groups:
            group_arguments = group_args.pop("arguments", [])
            mgroup = self.add_mutually_exclusive_group(**group_args)
            for argument in group_arguments:
                flags = argument.pop("flags", [])
                mgroup.add_argument(*flags, **argument)

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

    def _registry_get(
        self,
        registry_name: str,
        value: Any,
        default: Any = None,
    ) -> Any:
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
    def from_configs(cls, *configs: dict | str) -> ArgumentParser:
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
