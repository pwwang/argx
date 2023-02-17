import pytest  # noqa: F401
from argparse_charged import ArgumentParser
from argparse_charged.action import (
    StoreAction,
    StoreConstAction,
    StoreTrueAction,
    StoreFalseAction,
    AppendAction,
    AppendConstAction,
    CountAction,
    ExtendAction,
    ListAction,
)


def test_store():
    parser = ArgumentParser()
    parser.add_argument("--foo", action=StoreAction)
    ns = parser.parse_args(["--foo", "bar"])
    assert ns.foo == "bar"

    parser.add_argument("--bar.baz", action=StoreAction)
    ns = parser.parse_args(["--bar.baz", "qux"])
    assert ns.bar.baz == "qux"


def test_store_const():
    parser = ArgumentParser()
    parser.add_argument("--foo", action=StoreConstAction, const="bar")
    ns = parser.parse_args(["--foo"])
    assert ns.foo == "bar"

    parser.add_argument("--bar.baz", action=StoreConstAction, const="qux")
    ns = parser.parse_args(["--bar.baz"])
    assert ns.bar.baz == "qux"


def test_store_true():
    parser = ArgumentParser()
    parser.add_argument("--foo", action=StoreTrueAction)
    ns = parser.parse_args(["--foo"])
    assert ns.foo is True

    parser.add_argument("--bar.baz", action=StoreTrueAction)
    ns = parser.parse_args(["--bar.baz"])
    assert ns.bar.baz is True


def test_store_false():
    parser = ArgumentParser()
    parser.add_argument("--foo", action=StoreFalseAction)
    ns = parser.parse_args(["--foo"])
    assert ns.foo is False

    parser.add_argument("--bar.baz", action=StoreFalseAction)
    ns = parser.parse_args(["--bar.baz"])
    assert ns.bar.baz is False


def test_append():
    parser = ArgumentParser()
    parser.add_argument("--foo", action=AppendAction)
    ns = parser.parse_args(["--foo", "bar"])
    assert ns.foo == ["bar"]

    parser.add_argument("--bar.baz", action=AppendAction)
    ns = parser.parse_args(["--bar.baz", "qux"])
    assert ns.bar.baz == ["qux"]


def test_append_const():
    parser = ArgumentParser()
    parser.add_argument("--foo", action=AppendConstAction, const="bar")
    ns = parser.parse_args(["--foo"])
    assert ns.foo == ["bar"]

    parser.add_argument("--bar.baz", action=AppendConstAction, const="qux")
    ns = parser.parse_args(["--bar.baz"])
    assert ns.bar.baz == ["qux"]


def test_count():
    parser = ArgumentParser()
    parser.add_argument("--foo", action=CountAction)
    ns = parser.parse_args(["--foo"])
    assert ns.foo == 1

    parser.add_argument("--bar.baz", action=CountAction)
    ns = parser.parse_args(["--bar.baz"])
    assert ns.bar.baz == 1

    parser.add_argument("--bar.v", "-v", action=CountAction)
    ns = parser.parse_args(["-vvv"])
    assert ns.bar.v == 3


def test_extend():
    parser = ArgumentParser()
    parser.add_argument("--foo", nargs="+", action=ExtendAction)
    ns = parser.parse_args(["--foo", "bar", "--foo", "baz", "qux"])
    assert ns.foo == ['bar', 'baz', 'qux']

    parser.add_argument("--bar.baz", nargs="+", action=ExtendAction)
    ns = parser.parse_args(["--bar.baz", "qux", "--bar.baz", "quux", "quuz"])
    assert ns.bar.baz == ['qux', 'quux', 'quuz']

    parser.add_argument("--bar.v", "-v", nargs="+", action=ExtendAction)
    ns = parser.parse_args(["-vvv"])
    assert ns.bar.v == ["vv"]


def test_list():
    parser = ArgumentParser()
    parser.add_argument("--foo", action=ListAction, default=["a"])
    ns = parser.parse_args(["--foo", "bar", "--foo", "baz"])
    assert ns.foo == ['bar', 'baz']

    parser = ArgumentParser()
    parser.add_argument("--foo", action="append", default=["a"])
    ns = parser.parse_args(["--foo", "bar", "--foo", "baz"])
    assert ns.foo == ['a', 'bar', 'baz']

    parser = ArgumentParser()
    parser.add_argument("--bar.baz", action=ListAction, default=["a"])
    ns = parser.parse_args(["--bar.baz", "qux", "--bar.baz", "quux"])
    assert ns.bar.baz == ['qux', 'quux']

    parser = ArgumentParser()
    parser.add_argument("--bar.baz", action="append", default=["a"])
    ns = parser.parse_args(["--bar.baz", "qux", "--bar.baz", "quux"])
    assert ns.bar.baz == ['a', 'qux', 'quux']

    parser.add_argument("--bar.v", "-v", action=ListAction)
    ns = parser.parse_args(["-vvv"])
    assert ns.bar.v == ["vv"]


def test_help():
    parser = ArgumentParser()
    parser.add_argument(
        "--foo", action=StoreAction, help="foo help", show=False
    )
    help_str = parser.format_help()
    assert "foo help" in help_str

    parser = ArgumentParser(add_help="+")
    parser.add_argument(
        "--foo", action=StoreAction, help="foo help", show=False
    )
    help_str = parser.format_help()
    assert "foo help" in help_str
    help_str = parser.format_help(plus=False)
    assert "foo help" not in help_str

    parser = ArgumentParser(add_help="+")
    parser.add_namespace("ns", show=False)
    parser.add_argument("--ns.a", action=StoreAction, help="a help")
    parser.add_argument("--ns.b", action=StoreAction, help="b help")
    help_str = parser.format_help(plus=False)
    assert "'ns'" not in help_str


def test_help_parse(capsys):
    parser = ArgumentParser(add_help="+")
    parser.add_namespace("ns", show=False)
    parser.add_argument("--ns.a", action=StoreAction, help="a help")
    parser.add_argument("--ns.b", action=StoreAction, help="b help")

    with pytest.raises(SystemExit):
        parser.parse_args(["--help+"])

    assert "'ns'" in capsys.readouterr().out

    parser = ArgumentParser()
    parser.add_namespace("ns", show=False)
    parser.add_argument("--ns.a", action=StoreAction, help="a help")
    parser.add_argument("--ns.b", action=StoreAction, help="b help")

    with pytest.raises(SystemExit):
        parser.parse_args(["--help"])

    assert "'ns'" in capsys.readouterr().out
