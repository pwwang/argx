import pytest  # noqa: F401
from pathlib import Path
from argparse_charged import ArgumentParser


def test_exit_on_void():
    parser = ArgumentParser(exit_on_void=False, fromfile_prefix_chars=None)
    parser.add_argument("--foo", action="store_true", default=False)
    ns = parser.parse_args([])
    assert ns.foo is False

    parser = ArgumentParser(exit_on_void=True)
    parser.add_argument("--foo", action="store_true", default=False)
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_add_subparser_directly():
    parser = ArgumentParser()
    subparser_foo = parser.add_subparser("foo", help="The foo command")
    subparser_bar = parser.add_subparser("bar")
    assert "foo" in subparser_foo.prog
    assert "bar" in subparser_bar.prog
    help_str = parser.format_help()
    assert "foo" in help_str
    assert "The bar command" in help_str
    assert "  {foo,bar}" not in help_str

    # by default, a command is required
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_namespace_options():
    parser = ArgumentParser()
    parser.add_argument("--foo.bar", action="store_true", default=False)
    parser.add_argument("--foo.baz.qux", action="store_true", default=False)
    parsed = parser.parse_args(["--foo.bar", "--foo.baz.qux"])
    assert parsed.foo.bar is True
    assert parsed.foo.baz.qux is True

    help_str = parser.format_help()
    assert "namespace 'foo'" in help_str

    with pytest.raises(ValueError):
        parser.add_namespace("foo")


def test_load_defaults_from_file():
    defaultsfile = Path(__file__).parent / "configs" / "defaults.toml"
    parser = ArgumentParser()
    parser.add_argument("-a", required=True, type=int)
    command = parser.add_command("status")
    command.add_argument("--branch")
    parsed = parser.parse_args([f"@{defaultsfile}", "status"])
    assert parsed.a == 1
    assert parsed.branch == "dev"

    defaultspy = Path(__file__).parent / "configs" / "defaults.py"
    parser = ArgumentParser()
    parser.add_argument("--ns.v", required=True, type=int)
    parser.add_argument("--ns.vv", required=True, type=int)
    parsed = parser.parse_args([f"@{defaultspy}", "--ns.vv", "3"])
    assert parsed.ns.v == 2
    assert parsed.ns.vv == 3

    bad_defaultspy = Path(__file__).parent / "configs" / "bad_defaults.py"
    parser = ArgumentParser()
    parser.add_argument("--ns.v", required=True, type=int)
    with pytest.raises(SystemExit):
        parser.parse_args([f"@{bad_defaultspy}"])


def test_load_from_config():
    configfile = Path(__file__).parent / "configs" / "config.toml"
    parser = ArgumentParser.from_configs(configfile)
    parsed = parser.parse_args("-d cmd1 cmd11 -f 1".split())
    assert parsed.COMMAND == "cmd1"
    assert parsed.COMMAND2 == "cmd11"
