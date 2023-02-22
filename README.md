# argx

[![pypi][1]][2] [![tag][3]][2] [![codacy quality][4]][5] [![codacy quality][6]][5] ![github action][7] ![pyver][8]

Supercharged argparse for Python

## Installation

```bash
pip install -U argx
```

## Features enhanced or added

- [Option `exit_on_void`](#option-exit_on_void): Exit with error if no arguments are provided
- [Subcommand shortcut](#subcommand-shortcut): Adding subcommands directly, without `parser.add_subparsers()`
- [Namespace arguments](#namespace-arguments): Access arguments like `--foo.bar` as `args.foo.bar`
- [Brief help message for massive arguments](#brief-help-message-for-massive-arguments): Show only the most important arguments in the help message
- [Default value in argument help](#default-value-in-argument-help): Show the default value in the help message of arguments
- [Newlines kept in help](#newlines-kept-in-help): Newlines are kept in argument help if any
- [Defaults from file](#defaults-from-files): Read default values from a configuration file by API or from command line
- [List action](#list-action): Store a list of values. Different from `append` and `extend`, the initial value is cleared.
- [Grouping required arguments by default](#grouping-required-arguments-by-default): Put required arguments in 'required arguments' group, instead of 'optional arguments' group
- [Order of groups in help message](#order-of-groups-in-help-message): Allow to add an `order` attribute to groups to change the order of groups in help message
- [Addtional types](#additional-types): Some additional types to convert the values of arguments
- [Configuration file to create the parser](#configuration-file-to-create-the-parser): Instead of creating the parser by code, you can also create it by a configuration file
- [Backward compatibility](#backward-compatibility): All features are optional. You can use `argx` as a drop-in replacement for `argparse`.

### Option `exit_on_void`

If all arguments are optional, `argparse` will not raise an error if no arguments are provided. This is not always desirable. `argx` provides the option `exit_on_void` to change this behavior. If `exit_on_void` is set to `True` and no arguments are provided, `argx` will exit with an error (No arguments provided).

```python
import argx as argparse

parser = argparse.ArgumentParser(exit_on_void=True)
parser.add_argument('--foo', action='store_true')

args = parser.parse_args([])
# No arguments provided
# standard argparse produces: Namespace(foo=False)
```

### Subcommand shortcut

`argparse` requires to create subparsers first and then add the subcommands to the subparsers.
`argx` allows to add subcommands directly to the main parser.

```python
# standard argparse
parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(title='subcommands')
parser_a = subparsers.add_parser('a')
parser_b = subparsers.add_parser('b')

# argx
parser = argparse.ArgumentParser()
parser.add_command('a')  # or parser.add_subparser('a')
parser.add_command('b')
# args = parser.parse_args(['a'])
# Namespace(COMMAND='a')
```

The `subparsers` is added automatically with the title `subcommands` and the `dest` is set to `COMMAND`. You can add subcommands to subcommands directly, then the `dest` is set to `COMMAND2`, `COMMAND3`, etc. If you want to change the behavior, you can always fall back to the standard `argparse` way.

### Namespace arguments

The values of arguments like `--foo.bar` can be accessed as `vars(args)['foo.bar']`. With `argx` you can access them as `args.foo.bar`.

The arguments `--foo.bar`, `--foo.baz` and `--foo.qux` are automatically grouped in a namespace `foo`.

```python
import argx as argparse

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
import argx as argparse

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

You can also add a namespace action argument to take a json that can be parsed as a dict:

```python
import argx as argparse

parser = argparse.ArgumentParser()
parser.add_argument('--foo', action="namespace") # or action="ns"
parser.add_argument('--foo.bar', type=int)
parser.add_argument('--foo.baz', type=int)
parser.add_argument('--foo.qux', type=int)

parser.parse_args(['--foo', '{"bar": 1, "baz": 2, "qux": 3}', '--foo.qux', '4'])
# Namespace(foo=Namespace(bar=1, baz=2, qux=4))
```

### Brief help message for massive arguments

If you have a lot of arguments, the help message can be very long. `argx` allows to show only the most important arguments in the help message.

```python
import argx as argparse

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

### Default value in argument help

With `argparse`, the default value is not shown in the help message. With `argx`, the default value is added to the help message automatically.

```python
import argx as argparse

parser = argparse.ArgumentParser()
parser.add_argument('--foo', type=int, default=1)
parser.add_argument('--bar', type=int, default=2, help='bar [default: two]')
parser.add_argument('--baz', type=int, default=3, help='baz [nodefault]')
parser.print_help()
```

```shell
usage: test.py [-h] [--foo FOO]

optional arguments:
  -h, --help            show help message and exit
  --foo FOO             [default: 1]
  --bar BAR             bar [default: two]
  --baz BAZ             baz
```

### Newlines kept in help

By default, `argparse` replaces the newlines with spaces in the argument help message. However, sometimes you want to keep the newlines. With `argx`, if there is not newline, it is handled as the default behavior. If there is a newline, the newlines and spaces are kept.

```python
import argx as argparse

parser = argparse.ArgumentParser()
parser.add_argument('--foo', help='foo\n- bar\n  indent also kept')
parser.print_help()
```

```shell
usage: test.py [-h] [--foo FOO]

optional arguments:
  -h, --help            show this help message and exit
  --foo FOO             foo
                        - bar
                          indent also kept
```

### Defaults from files

With standard `argparse`, when `fromfile_prefix_chars` is set, the arguments can be read from a file. The file can be specified with `@filename`. The arguments in the file are separated by newlines by default.

With `argx`, Other than a text file to provide command line arguments, you can also provide other types of configuration files. The extension of the file can be `.json`, `.yaml`, `.ini`, `.env` or `.toml`.

```python
import argx as argparse

parser = argparse.ArgumentParser()
parser.add_argument('--foo', type=int)
parser.add_argument('--bar', type=int)
parser.add_argument('--baz', type=int)

# config.json
# { "foo": 1, "bar": 2, "baz": 3 }
args = parser.parse_args(['@config.json'])
# Namespace(foo=1, bar=2, baz=3)
```

You can also use `set_defaults_from_configs` method:

```python
parser.set_defaults_from_configs('config.json')
```

### List action

The `list` action is similar to `append` and `extend`, but the initial value is cleared.

This is useful when you want to accept a new list of values from the command line, instead of appending to the existing list or default.

```python
import argx as argparse

parser = argparse.ArgumentParser()
parser.add_argument('--foo', action='list', default=[1, 2, 3], type=int)
parser.add_argument('--bar', action='append', default=[1, 2, 3], type=int)

args = parser.parse_args('--foo 4 --foo 5 --bar 4 --bar 5'.split())
# Namespace(foo=[4, 5], bar=[1, 2, 3, 4, 5])
```

### Grouping required arguments by default

By default, `argparse` puts both `required=True` and `required=False` arguments in the same group (optional arguments), which is sometimes confusing. `argx` groups `required=True` arguments in a separate group (required arguments).

```python
import argx as argparse

parser = argparse.ArgumentParser()
parser.add_argument('--foo')
parser.add_argument('--bar', required=True)

parser.print_help()
```

```shell
usage: test.py [-h] [--foo FOO] --bar BAR

required arguments:
  --bar BAR

optional arguments:
  -h, --help            show help message and exit
  --foo FOO
```

### Order of groups in help message

Allow to add an `order` attribute to groups to change the order of groups in help message

```python
import argx as argparse

parser = argparse.ArgumentParser()
group1 = parser.add_argument_group('group1', order=2)
group1.add_argument('--foo')
group2 = parser.add_argument_group('group2', order=1)
group2.add_argument('--bar')

parser.print_help()
```

```shell
usage: test.py [-h] [--bar BAR] [--foo FOO]

optional arguments:
  -h, --help            show help message and exit

group2:
  --bar BAR

group1:
  --foo FOO
```

The order by default is 0. The groups with the same order are sorted by title. Groups with small numbers are displayed first. `required arguments` has a `order` of -1.

### Additional types

`parser.add_argument()` accepts `type` as a function to convert the argument value. It has to be a callable that accepts a single string argument and returns the converted value. While `argx` supports string for `type` so it can be configured in the configuration file. Builtin functions and types can also be specified by its name.

We also have additional types:

```python
import argx as argparse

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
  - `None` if the string is `None/NONE/none`
  - An integer if the string can be converted to an integer
  - A float if the string can be converted to a float
  - A dict if the string is a JSON string
  - The string itself otherwise

### Configuration file to create the parser

You can create the parser from a configuration file.

```python
import argx as argparse

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

All features are optional. You can use `argx` as a drop-in replacement for `argparse`.

`argx` supports python `3.7+`. Some of the later-introduced features are also supported in python 3.7. For example, `extend` action is added in python 3.8, `argx` supports in python 3.7.

[1]: https://img.shields.io/pypi/v/argx.svg?style=flat-square
[2]: https://pypi.org/project/argx/
[3]: https://img.shields.io/github/tag/pwwang/argx.svg?style=flat-square
[4]: https://img.shields.io/codacy/grade/c5eaafcde482437b901b1acd2b70420e.svg?style=flat-square
[5]: https://app.codacy.com/gh/pwwang/argx/dashboard
[6]: https://img.shields.io/codacy/coverage/c5eaafcde482437b901b1acd2b70420e.svg?style=flat-square
[7]: https://img.shields.io/github/actions/workflow/status/pwwang/argx/build.yml?style=flat-square
[8]: https://img.shields.io/pypi/pyversions/argx.svg?style=flat-square
