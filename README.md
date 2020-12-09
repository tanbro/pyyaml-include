# pyyaml-include

[![CircleCI](https://img.shields.io/circleci/project/github/tanbro/pyyaml-include.svg)](https://circleci.com/gh/tanbro/workflows/pyyaml-include)
[![Documentation Status](https://readthedocs.org/projects/pyyaml-include/badge/?version=stable)](https://pyyaml-include.readthedocs.io/en/stable/?badge=stable)
[![GitHub tag](https://img.shields.io/github/tag/tanbro/pyyaml-include.svg)](https://github.com/tanbro/pyyaml-include)
[![PyPI](https://img.shields.io/pypi/v/pyyaml-include.svg)](https://pypi.org/project/pyyaml-include/)
[![PyPI - License](https://img.shields.io/pypi/l/pyyaml-include.svg)](https://pypi.org/project/pyyaml-include/)
[![PyPI - Format](https://img.shields.io/pypi/format/pyyaml-include.svg)](https://pypi.org/project/pyyaml-include/)
[![PyPI - Status](https://img.shields.io/pypi/status/pyyaml-include.svg)](https://pypi.org/project/pyyaml-include/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyyaml-include.svg)](https://pypi.org/project/pyyaml-include/)
[![PyPI - Implementation](https://img.shields.io/pypi/implementation/pyyaml-include.svg)](https://pypi.org/project/pyyaml-include/)

An extending constructor of [PyYAML][]: include [YAML][] files into [YAML][] document.

## Install

```sh
pip install pyyaml-include
```

## Usage

Consider we have such [YAML] files:

```sh
├── 0.yml
└── include.d
    ├── 1.yml
    └── 2.yml
```

- `1.yml` 's content:

  ```yaml
  name: "1"
  ```

- `2.yml` 's content:

  ```yaml
  name: "2"
  ```

To include `1.yml`, `2.yml` in `0.yml`, we shall add `YamlIncludeConstructor` to [PyYAML]'s loader, then add an `!include` tag in `0.yaml`:

```python
import yaml
from yamlinclude import YamlIncludeConstructor

YamlIncludeConstructor.add_to_loader_class(loader_class=yaml.FullLoader, base_dir='/your/conf/dir')

with open('0.yml') as f:
    data = yaml.load(f, Loader=yaml.FullLoader)

print(data)
```

### Mapping

If `0.yml` was:

```yaml
file1: !include include.d/1.yml
file2: !include include.d/2.yml
```

We'll get:

```yaml
file1:
  name: "1"
file2:
  name: "2"
```

### Sequence

If `0.yml` was:

```yaml
files:
  - !include include.d/1.yml
  - !include include.d/2.yml
```

We'll get:

```yaml
files:
  - name: "1"
  - name: "2"
```

> ℹ **Note**:
>
> File name can be either absolute (like `/usr/conf/1.5/Make.yml`) or relative (like `../../cfg/img.yml`).

### Wildcards

File name can contain shell-style wildcards. Data loaded from the file(s) found by wildcards will be set in a sequence.

That is to say, a list will be returned when including file name contains wildcards.
Length of the returned list equals number of matched files:

- when only 1 file matched, length of list will be 1
- when there are no files matched, an empty list will be returned

If `0.yml` was:

```yaml
files: !include include.d/*.yml
```

We'll get:

```yaml
files:
  - name: "1"
  - name: "2"
```

> ℹ **Note**:
>
> - For `Python>=3.5`, if `recursive` argument of `!include` [YAML] tag is `true`, the pattern `“**”` will match any files and zero or more directories and subdirectories.
> - Using the `“**”` pattern in large directory trees may consume an inordinate amount of time because of recursive search.

In order to enable `recursive` argument, we shall set it in `Mapping` or `Sequence` arguments mode:

- Arguments in `Sequence` mode:

  ```yaml
  !include [tests/data/include.d/**/*.yml, true]
  ```

- Arguments in `Mapping` mode:

  ```yaml
  !include {pathname: tests/data/include.d/**/*.yml, recursive: true}
  ```

### Non YAML files

This extending constructor can now load data from non YAML files, supported file types are:

- `json`
- `toml` (only available when [toml](https://pypi.org/project/toml/) installed)
- `ini`

The constructor read non YAML files by different readers according to a pattern table defined in `src/yamlinclude/readers.py`.

Default reader table can be replaced by a custom `reader_map` when call `add_to_loader_class`.

[YAML]: http://yaml.org/
[PyYaml]: https://pypi.org/project/PyYAML/
