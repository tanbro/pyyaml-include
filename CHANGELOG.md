# Changelog

## 1.2

Date: 2019-02-03

- New:
  - non YAML file including

- Misc:
  - adjust docs
  - add pip and conda configure file of development environment

- Fix:
  - add `PlainTextReader` into `__all__` list of `reders` module 

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
