# CHANGELOG

## 2.2

> 📅 **Date** 2024-11-9

- New:

  - Add a `flatten` argument. See [#46](https://github.com/tanbro/pyyaml-include/issues/46) for detail

- Bug fix:

  - fix issue if glob_params is not int. See [#48](https://github.com/tanbro/pyyaml-include/pull/48) for detail

- Test:

  - PyPy 3.9 and 3.10 in docker compose based unit-test

- Other update and improvement

## 2.1

> 📅 **Date** 2024-5-5

- Better type hints
- Some optimizations and bugfix

## 2.0.2

> 📅 **Date** 2024-4-20

- Remove custom PyYAML types definition module, use that from `types-PyYAML` instead.
- Add [mypy](https://www.mypy-lang.org/) hook in pre-commit
- Better type hints/annotations

## 2.0.1

> 📅 **Date** 2024-4-9

- 🆕 New Features:
  - #44: Add `py.typed` file, make the package PEP-561 friendly

## 2.0

> 📅 **Date** 2024-3-31

## 2.0b2

> 📅 **Date** 2024-3-27

- ❎ Breaking Changes:
  - data-class attribute order changed in `yaml_include.Constructor`
- Some optimizations and bugfix

## 2.0b1

> 📅 **Date** 2024-3-11

- ❎ Breaking Changes:
  - namespace changed to `yaml_include`

- 🆕 New Features:
  - `Data` class for include statement.
  - `autoload` attribute for `Constructor` class, controlling if open and parse including files, or return a `Data` object.
  - `Representer` class for YAML dumping.
  - `load` and `lazy_load` function - recursive open and parse for `Data` object.

## 2.0.a2

> 📅 **Date** 2024-3-3

- 🆕 New Features:
  - Custom loader

## 2.0.a1

> 📅 **Date** 2024-1-27

- 🆕 New Features:
  - Introduce [fsspec][] to open including files. Now we can include files from local filesystem, s3, http, sftp ...
  - New parameters for the tag in YAML

- ❎ Incompatible Changes:
  - Drop python support blow 3.8
  - The tag constructor class `YamlIncludeConstructor` renamed to `Constructor`

- ❌ Removed:
  - Readers for JSON, TOML, INI ... YAML only now
  - The argument `relative` and `encoding`  was removed from the tag class's `load` method.
  - Anchor (Maybe recovered in future)

## 1.3.2

Date: 2023-12-25 🎅🤶

- Fix:
  - Correct license field in pyproject.toml #39

- Misc:
  - Update ruff hooks

## 1.3.1

Date: 2023-06-29

- Remove:
  - No longer support python version earlier than 3.7

- New:
  - New feature: relative include for PyYAML's pure python loaders

- Misc:
  - Migrate project's build configure to `pyproject.toml` completely
  - Improved CI

- Docs:
  - New Sphinx-Docs theme: furo.

## 1.3

Date: 2022-04-24

- New:
  - PyYAML 6.0 supported

- Misc:
  - Better CI processes

## 1.2

Date: 2019-02-03

- New:
  - non YAML file including

- Misc:
  - adjust docs
  - add pip and conda configure file of development environment

- Fix:
  - add `PlainTextReader` into `__all__` list of `readers` module

## 1.1

Date: 2019-03-18

- Change:
  - Update PyYAML to 5.*
  - Rename: Argument `loader_class` of `YamlIncludeConstructor.add_to_loader_class()` (former: `loader_cls`)

## 1.0.4

Date: 2019-01-07

- Change:

  - rename: `TAG` ==> `DEFAULT_TAG_NAME`
  - add: `encoding` argument

- Fix:

  - A wrong logging text format

- Misc:

  - add: `.pylintrc`

## 1.0.3

Date: 2018-12-04

- New Feature:

  - Add `base_dir` argument

- Misc:

  - Add some new unit-test
  - Add Python3.7 in CircleCI

## 1.0.2

Date: 2018-07-11

- Add:

  - `encoding` argument

- Bug fix:

  - encoding error if non-ascii characters on non-utf8 os.

## 1.0.1

Date: 2018-07-03

- Add:

  - Old Python2.6 and new Python3.7 compatibilities

  - class method `add_to_loader_class`

    A class method to add the constructor itself into YAML loader class

  - Sphinx docs

- Change:

  - Rename module file `include.py` to `constructor.py`

  - Rename class data member `DEFAULT_TAG` to `TAG`

## 1.0

Date: 2018-06-08

[fsspec]: https://github.com/fsspec/filesystem_spec/ "Filesystem Spec (fsspec) is a project to provide a unified pythonic interface to local, remote and embedded file systems and bytes storage."
