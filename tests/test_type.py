import pytest  # noqa: F401
from argx import ArgumentParser


def test_py():
    parser = ArgumentParser()
    parser.add_argument("--foo", type="py")
    ns = parser.parse_args(["--foo", "{'a': 1}"])
    assert ns.foo == {"a": 1}


def test_json():
    parser = ArgumentParser()
    parser.add_argument("--foo", type="json")
    ns = parser.parse_args(["--foo", '{"a": 1}'])
    assert ns.foo == {"a": 1}


def test_auto():
    parser = ArgumentParser()
    parser.add_argument("--foo", type="auto")
    ns = parser.parse_args(["--foo", '{"a": 1}'])
    assert ns.foo == {"a": 1}

    ns = parser.parse_args(["--foo", 'TRUE'])
    assert ns.foo is True

    ns = parser.parse_args(["--foo", 'FALSE'])
    assert ns.foo is False

    ns = parser.parse_args(["--foo", 'NONE'])
    assert ns.foo is None

    ns = parser.parse_args(["--foo", 'xy'])
    assert ns.foo == 'xy'
