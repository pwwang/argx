from __future__ import annotations

import sys
from typing import IO, TYPE_CHECKING, Any, Callable, Sequence
from pathlib import Path
from gettext import gettext as _
from argparse import (
    SUPPRESS,
    _SubParsersAction,
    _ArgumentGroup as APArgumentGroup,
    ArgumentParser as APArgumentParser,
    Namespace,
)

from simpleconf import Config  # type: ignore[import-untyped]

from . import type_
from .utils import (
    format_title,
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
    ClearAppendAction,
    ClearExtendAction,
    NamespaceAction,
    SubParserAction,
    HelpAction,
)
from .formatter import ChargedHelpFormatter

if TYPE_CHECKING:
    from argparse import Action, _FormatterClass


@add_attribute("level", 0)
class ArgumentParser(APArgumentParser):
    """Supercharged ArgumentParser for parsing command line strings into
    Python objects."""

    def __init__(
        self,
        prog: str | None = None,
        usage: str | None = None,
        description: str | None = None,
        epilog: str | None = None,
        parents: Sequence[ArgumentParser] = [],
        formatter_class: _FormatterClass = ChargedHelpFormatter,
        prefix_chars: str = "-",
        fromfile_prefix_chars: str | None = None,
        argument_default: Any = None,
        conflict_handler: str = "error",
        add_help: bool | str | Sequence[str] = True,
        allow_abbrev: bool = True,
        exit_on_error: bool = True,
        exit_on_void: bool = False,
        pre_parse: (
            Callable[[ArgumentParser, Sequence[str], Namespace], None] | None
        ) = None,
    ) -> None:
        """Create an ArgumentParser

        Args:
            prog (str, optional): The program name
            usage (str, optional): The usage message
            description (str, optional): The description message
            epilog (str, optional): The epilog message
            parents (Sequence[ArgumentParser], optional): The parent parsers
            formatter_class (type, optional): The formatter class
            prefix_chars (str, optional): The prefix characters
            fromfile_prefix_chars (str, optional): The prefix characters for
                configuration files
            argument_default (Any, optional): The default value for arguments
            conflict_handler (str, optional): The conflict handler
            add_help (bool | str | Sequence[str], optional): Whether to
                add the help option.
                If True (default), same as "h,help".
                If any option ends with "+", it will add the help option with the
                ability to show more options (e.g. "h+,help+").
                If False, it will not add the help option
            allow_abbrev (bool, optional): Whether to allow abbreviation
            exit_on_error (bool, optional): Whether to exit on error
            exit_on_void (bool, optional): Whether to exit on void arguments
                Added by `argx`.
            pre_parse (Callable[[ArgumentParser], None], optional): The
                function to call before parsing.
                Added by `argx`.
        """
        old_add_help = add_help
        # disable add_help to add it later
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
        self.pre_parse = pre_parse
        self._subparsers_action: _SubParsersAction | None = None

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
        self.register("action", "clear_append", ClearAppendAction)
        self.register("action", "clear_extend", ClearExtendAction)
        self.register("action", "ns", NamespaceAction)
        self.register("action", "namespace", NamespaceAction)
        self.register("action", "parsers", SubParserAction)
        self.register("action", "help", HelpAction)
        self.register("type", "py", type_.py)
        self.register("type", "json", type_.json)
        self.register("type", "path", Path)
        self.register("type", "auto", type_.auto)

        # Add help option to support + for more options
        default_prefix = "-" if "-" in self.prefix_chars else self.prefix_chars[0]
        if old_add_help is not False:
            if old_add_help is True:
                old_add_help = "h,help"

            if isinstance(old_add_help, str):
                old_add_help = old_add_help.split(",")

            old_add_help = [x.strip() for x in old_add_help]
            help_msg = "show this help message and exit"
            if any(x.endswith("+") for x in old_add_help):
                help_msg = f"{help_msg} (with + for more options)"

            old_add_help = [
                (
                    f"{default_prefix * 2}{x}"
                    if len(x.rstrip("+")) > 1
                    else f"{default_prefix}{x}"
                )
                for x in old_add_help
            ]

            self.add_argument(
                *old_add_help,
                action="help",
                default=SUPPRESS,
                help=_(help_msg),
            )

        # restore add_help
        self.add_help = old_add_help  # type: ignore[assignment]

        self._required_actions = self.add_argument_group(
            _("required arguments"),
            order=-1,
        )

    def add_subparsers(self, order: int = 99, **kwargs) -> _SubParsersAction:
        """Add subparsers to the parser.

        Args:
            order (int): The order of the subparsers group
                Added by `argx`.
            **kwargs: The arguments to pass to add_argument_group()

        Returns:
            _SubParsersAction: The subparsers
        """
        action = super().add_subparsers(**kwargs)
        if self._subparsers is not self._positionals:
            self._subparsers.order = order  # type: ignore[assignment]

        # Add parent to subparsers action
        # So that subparsers.add_parser add parent to the sub-parser
        action.parent = self  # type: ignore[assignment]
        return action

    def add_subparser(self, name: str, **kwargs) -> ArgumentParser | Any:
        """Add a subparser directly, a shortcut to add sub-commands by `argx`.

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
        if self._subparsers_action is None:
            self._subparsers_action = self.add_subparsers(
                title=_("subcommands"),
                required=True,
                dest=(
                    "COMMAND"
                    if self.level == 0  # type: ignore[assignment]
                    else f"COMMAND{self.level + 1}"  # type: ignore[assignment]
                ),
            )
        kwargs.setdefault("help", f"The {name} command")
        out = self._subparsers_action.add_parser(name, **kwargs)
        out.level = self.level + 1  # type: ignore[assignment]
        return out

    add_command = add_subparser

    def parse_known_args(  # type: ignore[override]
        self,
        args: Sequence[str] | None = None,
        namespace: Namespace | None = None,
        fromfile_parse: bool = True,
        fromfile_keep: bool = False,
    ) -> tuple[Namespace, list[str]]:
        """Parse known arguments.

        Modify to handle exit_on_void and @file to load default values by `argx`.

        Args:
            args: The arguments to parse.
            namespace: The namespace to use.
            fromfile_parse: Whether to parse @file.
                Added by `argx`.
            fromfile_keep: Whether to keep @file in the unknown arguments.
                Note that @file.txt file will be treated as a normal argument,
                thus, it will be parsed and not kept anyway. This means at
                this point, @file.txt will be expanded right away.
                Added by `argx`.
        """
        if args is None:  # pragma: no cover
            # args default to the system args
            args = sys.argv[1:]
        else:
            # make sure that args are mutable
            args = list(args)

        # default Namespace built from parser defaults
        if namespace is None:
            namespace = Namespace()

        if callable(self.pre_parse):
            new_args = self.pre_parse(self, args, namespace)
            if new_args is not None:
                args = new_args

        # @files to keep in the unknown arguments
        files = []
        # arguments passed to super().parse_known_args() for parsing
        new_args = []

        for arg in args:
            # no fromfile_prefix_chars or normal argument
            if (
                not self.fromfile_prefix_chars
                or not arg
                or arg[0] not in self.fromfile_prefix_chars
            ):
                new_args.append(arg)

            # fromfile_prefix_chars is set
            # and arg is not empty
            # and arg starts with fromfile_prefix_chars

            # @file.txt is special, send it to super().parse_known_args()
            # for parsing
            elif arg.endswith(".txt"):
                new_args.append(arg)
            # @file.py, @file.json, ...
            else:
                if fromfile_keep:
                    # keep @file in the unknown arguments
                    files.append(arg)

                if fromfile_parse:
                    # parse @file to set the default values
                    conf = arg[1:]
                    if conf.endswith(".py"):
                        try:
                            conf: dict | str = import_pyfile(conf)
                        except Exception as e:
                            self.error(f"Cannot import [{conf}]: {e}")
                    self.set_defaults_from_configs(conf)

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
        argv = files + argv
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

    def _add_action(self, action):
        """Add an action to the parser.

        Modify to handle namespace actions, like "--group.abc"
        """
        if isinstance(action, APArgumentGroup) or (
            not isinstance(action, NamespaceAction) and "." not in action.dest
        ):
            if action.required:  # type: ignore[union-attr]
                return self._required_actions._add_action(
                    action  # type: ignore[return-value]
                )
            return super()._add_action(action)  # type: ignore[return-value]

        # Do not transform the keys for namespace action
        action.dest = action.option_strings[0].lstrip(self.prefix_chars)
        # Split the destination into a list of keys
        keys = action.dest.split(".")
        seq = range(len(keys) - 1, 0, -1)
        # Add --ns, --ns.subns also to their now group
        if isinstance(action, NamespaceAction):
            seq = [None] + list(seq)

        group = None
        for i in seq:
            ns_key = ".".join(keys[:i])

            for action_group in self._action_groups:
                if (
                    isinstance(action_group, _NamespaceArgumentGroup)
                    and action_group.name == ns_key  # type: ignore[union-attr]
                ):
                    group = action_group
                    break

            if group is not None:
                break

        if group is None:
            group = self.add_namespace(keys[0])

        return group._add_action(action)

    def get_action(
        self,
        dest: str,
        include_ns_group: bool = False,
    ) -> Action | _NamespaceArgumentGroup | None:
        """Get an action by its destination.

        Added by `argx`.

        Args:
            dest: The destination of the action

        Returns:
            Action: The action. None if not found.
        """
        if include_ns_group:
            for action_group in self._action_groups:
                if isinstance(action_group, _NamespaceArgumentGroup):
                    if action_group.name == dest:  # type: ignore[union-attr]
                        return action_group

        for action in self._actions:
            if action.dest == dest:
                return action

        return None

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
                and action_group.name == name  # type: ignore[union-attr]
            ):
                raise ValueError(f"Namespace '{name}' already exists")

        if title is None:
            title = f"{_('namespace')} <{name}>"

        group = _NamespaceArgumentGroup(self, title, **kwargs)
        group.name = name  # type: ignore[assignment]
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
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)

        # description
        formatter.add_text(self.description)
        # positionals, optionals and user-defined groups
        for action_group in sorted(
            self._action_groups,
            key=lambda x: (x.order, x.title),  # type: ignore[return-value]
        ):
            if not plus and not showable(action_group):
                for action in action_group._group_actions:
                    # hide them in usage as well
                    action.help = SUPPRESS
                continue

            formatter.start_section(
                "\033[1m\033[4m"
                f"{format_title(action_group.title)}"  # type: ignore[arg-type]
                "\033[0m\033[0m"
            )
            formatter.add_text(action_group.description)
            formatter.add_arguments(  # type: ignore[call-arg]
                action_group._group_actions,
                plus,  # type: ignore[arg-type]
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
        if registry_name == "type" and isinstance(value, str) and default == value:
            import builtins

            # "int", "float", "str", "open", etc
            got = self._registries[registry_name].get(
                value,
                getattr(builtins, value, None),
            )
            if not callable(got):
                raise ValueError(f"Invalid type '{value}'")

            return got

        # Not using super() because _ArgumentGroup can also use it
        return APArgumentGroup._registry_get(
            self,  # type: ignore[return-value]
            registry_name,
            value,
            default,
        )

    @classmethod
    def from_configs(cls, *configs: dict | str, **kwargs) -> ArgumentParser:
        """Create an ArgumentParser from a configuration file.

        Added by `argx`.

        Args:
            *configs: The configuration files or dicts to load
            **kwargs: Additional variables to format description of the main
                parser
                >>> parser = ArgumentParser.from_configs(
                >>>   {"description": "Hello {name}"}, name="World"
                >>> )

        Returns:
            ArgumentParser: The ArgumentParser
        """
        config = Config.load(*configs)
        mutually_exclusive_groups = config.pop("mutually_exclusive_groups", [])
        groups = config.pop("groups", [])
        namespaces = config.pop("namespaces", [])
        arguments = config.pop("arguments", [])
        commands = config.pop("commands", [])
        if "description" in config:
            config["description"] = config["description"].format(**kwargs)
        parser = cls(**config)
        parser._add_decedents(
            mutually_exclusive_groups,
            groups,
            namespaces,
            arguments,
            commands,
        )
        return parser


@add_attribute("show", True, "order", 0)
class _ArgumentGroup(APArgumentGroup):
    _registry_get = ArgumentParser._registry_get


@add_attribute("name")
class _NamespaceArgumentGroup(_ArgumentGroup):
    pass
