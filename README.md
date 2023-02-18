# argparse-charged

[![pypi][1]][2] [![tag][3]][2] [![codacy quality][4]][5] [![codacy quality][6]][5] ![github action][7] ![pyver][8]

Supercharged argparse for Python

## Installation

```bash
pip install -U argparse-charged
```

## Features

- Option `exit_on_void`: Exit with error if no arguments are provided
- Subcommand shortcut: Adding subcommands directly, without `parser.add_subparsers()`
- Namespace arguments: Access arguments like `--foo.bar` as `args.foo.bar`
- Brief help message for massive arguments: Show only the most important arguments in the help message
- Defaults from file: Read default values from a configuration file by API or from command line
- List action: Store a list of values. Different from `append` and `extend`, the initial value is cleared.
- Addtional types: Some additional types to convert the values of arguments
- Configuration file to create the parser: Instead of creating the parser by code, you can also create it by a configuration file
- Backward compatibility: All features are optional. You can use `argparse-charged` as a drop-in replacement for `argparse`.

### Option `exit_on_void`

If all arguments are optional, `argparse` will not raise an error if no arguments are provided. This is not always desirable. `argparse-charged` provides the option `exit_on_void` to change this behavior. If `exit_on_void` is set to `True` and no arguments are provided, `argparse-charged` will exit with an error (No arguments provided).

```python
import argparse_charged as argparse

parser = argparse.ArgumentParser(exit_on_void=True)
parser.add_argument('--foo', action='store_true')

args = parser.parse_args([])
# No arguments provided
# standard argparse produces: Namespace(foo=False)
```

### Subcommand shortcut

`argparse` requires to subparsers first and then add the subcommands to the subparsers.
`argparse-charged` allows to add subcommands directly to the main parser.

```python
# standard argparse
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(title='subcommands')
parser_a = subparsers.add_parser('a')
parser_b = subparsers.add_parser('b')

# argparse-charged
parser = argparse.ArgumentParser()
parser.add_command('a')  # or parser.add_subparser('a')
parser.add_command('b')
# args = parser.parse_args(['a'])
# Namespace(COMMAND='a')
```

The `subparsers` is added automatically with the title `subcommands` and the `dest` is set to `COMMAND`. You can add subcommands to subcommands directly, then the `dest` is set to `COMMAND2`, `COMMAND3`, etc. If you want to change the behavior, you can always fall back to the standard `argparse` way.

### Namespace arguments

The values of arguments like `--foo.bar` can be accessed as `vars(args)['foo.bar']`. With `argparse-charged` you can access them as `args.foo.bar`.

The arguments `--foo.bar`, `--foo.baz` and `--foo.qux` are automatically grouped in a namespace `foo`.

```python
import argparse_charged as argparse

parser = argparse.ArgumentParser()
parser.add_argument('--foo.bar', type=int)
parser.add_argument('--foo.baz', type=int)
parser.add_argument('--foo.qux', type=int)

parser.print_help()
```

```shell
usage: test.py [-h] [--foo.bar BAR] [--foo.baz BAZ] [--foo.qux QUX]

optional arguments:
  -h, --help            show this help message and exit

namespace 'foo':
  --foo.bar BAR
  --foo.baz BAZ
  --foo.qux QUX
```

You can modify the namespace by adding the namespace manually before adding the arguments.

```python
import argparse_charged as argparse

parser = argparse.ArgumentParser()
parser.add_namespace('foo', title="Foo's options")
parser.add_argument('--foo.bar', type=int)
parser.add_argument('--foo.baz', type=int)
parser.add_argument('--foo.qux', type=int)

parser.print_help()
```

```shell
usage: test.py [-h] [--foo.bar BAR] [--foo.baz BAZ] [--foo.qux QUX]

optional arguments:
  -h, --help            show this help message and exit

Foo's options:
    --foo.bar BAR
    --foo.baz BAZ
    --foo.qux QUX
```

### Brief help message for massive arguments

If you have a lot of arguments, the help message can be very long. `argparse-charged` allows to show only the most important arguments in the help message.

```python
import argparse_charged as argparse

# Advanced help options to show the brief help message or the full help message
parser = argparse.ArgumentParser(add_help='+')
parser.add_argument('--foo', type=int)
parser.add_argument('--bar', type=int, show=False)
parser.parse_args(['--help'])
```

```shell
usage: test.py [-h] [--foo FOO]

optional arguments:
  -h, --help, -h+, --help+
                        show help message (with + to show more options) and exit
  --foo FOO
```

With `parser.parse_args(['--help+'])` you can show the full help message.

```shell
usage: test.py [-h] [--foo FOO] [--bar BAR]

optional arguments:
  -h, --help, -h+, --help+
                        show help message (with + to show more options) and exit
  --foo FOO
  --bar BAR
```

You can also set `show=False` for argument groups.

### Defaults from files

With standard `argparse`, when `fromfile_prefix_chars` is set, the arguments can be read from a file. The file can be specified with `@filename`. The arguments in the file are separated by newlines by default.

With `argparse-charged`, `fromfile_prefix_chars` is set to `@` by default. Other than a text file to provide command line arguments, you can also provide other types of configuration files. The extension of the file can be `.json`, `.yaml`, `ini`, `env` or `.toml`.

```python
import argparse_charged as argparse

parser = argparse.ArgumentParser()
parser.add_argument('--foo', type=int)
parser.add_argument('--bar', type=int)
parser.add_argument('--baz', type=int)

# config.json
# { "foo": 1, "bar": 2, "baz": 3 }
args = parser.parse_args(['@config.json'])
# Namespace(foo=1, bar=2, baz=3)
```

```json
{
  "foo": 1,
  "bar": 2,
  "baz": 3
}
```

You can also use `set_defaults_from_configs` method:

```python
parser.set_defaults_from_configs('config.json')
```

### List action

The `list` action is similar to `append` and `extend`, but the initial value is cleared.

This is useful when you want to accept a new list of values from the command line, instead of appending to the existing list or default.

```python
import argparse_charged as argparse

parser = argparse.ArgumentParser()
parser.add_argument('--foo', action='list', default=[1, 2, 3], type=int)
parser.add_argument('--bar', action='append', default=[1, 2, 3], type=int)

args = parser.parse_args('--foo 4 --foo 5 --bar 4 --bar 5'.split())
# Namespace(foo=[4, 5], bar=[1, 2, 3, 4, 5])
```

### Additional types

`parser.add_argument()` accepts `type` as a function to convert the argument value. It has to be a callable that accepts a single string argument and returns the converted value. While `argparse-charged` supports string for `type` so it can be configured in the configuration file. Builtin functions and types can also be specified by its name.

We also have additional types:

```python
import argparse_charged as argparse

parser = argparse.ArgumentParser()
parser.add_argument('--foo', type='py')
parser.add_argument('--bar', type='json')
parser.add_argument('--baz', type='path')
parser.add_argument('--qux', type='auto')

args = parser.parse_args(
    '--foo 1 --bar {"a":1} --baz path/to/file --qux true'.split()
)
# Namespace(foo=1, bar={'a': 1}, baz=PosixPath('path/to/file'), qux=True)
```

- `py`: Python expression. The string is evaluated by `ast.literal_eval`.
- `json`: JSON string. The string is loaded by `json.loads`.
- `path`: Path string. The string is converted by `pathlib.Path`.
- `auto`: Automatic type conversion.
  - `True` if the string is `True/TRUE/true`
  - `False` if the string is `False/FALSE/false`
  - An integer if the string can be converted to an integer
  - A float if the string can be converted to a float
  - A dict if the string is a JSON string
  - The string itself otherwise

### Configuration file to create the parser

You can create the parser from a configuration file.

```python
import argparse_charged as argparse

# config.json
# {
#   "prog": "myprog",
#   "arguments": [ {"flags": ["-a", "--abc"], "help": "Optiona a help"} ]
# }
parser = argparse.ArgumentParser.from_configs('config.json')
parser.print_help()
```

```shell
usage: myprog [-h] [-a ABC]

optional arguments:
  -h, --help            show help message and exit
  -a ABC, --abc ABC     Optiona a help
```

### Backward compatibility

All features are optional. You can use `argparse-charged` as a drop-in replacement for `argparse`.

`argparse-charged` supports python `3.7+`. Some of the later-introduced features are also supported in python 3.7. For example, `exit_on_error` is added in python 3.9, `argparse-charged` supports in python 3.7 and python 3.8. `extend` action is added in python 3.8, `argparse-charged` supports in python 3.7.

[1]: https://img.shields.io/pypi/v/argparse-charged.svg?style=flat-square
[2]: https://pypi.org/project/argparse-charged/
[3]: https://img.shields.io/github/tag/pwwang/argparse-charged.svg?style=flat-square
[4]: https://img.shields.io/codacy/grade/c5eaafcde482437b901b1acd2b70420e.svg?style=flat-square
[5]: https://app.codacy.com/gh/pwwang/argparse-charged/dashboard
[6]: https://img.shields.io/codacy/coverage/c5eaafcde482437b901b1acd2b70420e.svg?style=flat-square
[7]: https://img.shields.io/github/actions/workflow/status/pwwang/argparse-charged/build.yml?style=flat-square
[8]: https://img.shields.io/pypi/pyversions/argparse-charged.svg?style=flat-square
