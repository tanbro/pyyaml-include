# Changelog

## 1.0.3

Date: 2018-12-04

- New Feature:

  - Add `base_dir` argument

- Misc:

  - Add some new unit-test
  - Add Python3.7 in circleci 

## 1.0.2

Date: 2018-07-11

- Add:

  - `encoding` argument

- Bugix:

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
