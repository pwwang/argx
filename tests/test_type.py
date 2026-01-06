import pytest  # noqa: F401
from pathlib import Path
from argx import ArgumentParser
from panpath import S3Path


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


def test_panpath():
    parser = ArgumentParser()
    parser.add_argument("--foo", type="panpath")
    ns = parser.parse_args(["--foo", "s3://bucket/path"])
    assert isinstance(ns.foo, S3Path)
    assert str(ns.foo) == "s3://bucket/path"

    ns = parser.parse_args(["--foo", "/local/path"])
    assert isinstance(ns.foo, Path)
    assert str(ns.foo) == "/local/path"


def test_unsupported_type():
    parser = ArgumentParser()
    with pytest.raises(ValueError, match="Invalid type"):
        parser.add_argument("--foo", type="unsupported")
