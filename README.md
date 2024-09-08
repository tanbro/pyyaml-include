# pyyaml-include

[![GitHub tag](https://img.shields.io/github/tag/tanbro/pyyaml-include.svg)](https://github.com/tanbro/pyyaml-include)
[![Python Package](https://github.com/tanbro/pyyaml-include/workflows/Python%20package/badge.svg)](https://github.com/tanbro/pyyaml-include/actions?query=workflow%3A%22Python+package%22)
[![Documentation Status](https://readthedocs.org/projects/pyyaml-include/badge/?version=latest)](https://pyyaml-include.readthedocs.io/en/latest/)
[![PyPI](https://img.shields.io/pypi/v/pyyaml-include.svg)](https://pypi.org/project/pyyaml-include/)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=tanbro_pyyaml-include&metric=alert_status)](https://sonarcloud.io/dashboard?id=tanbro_pyyaml-include)

An extending constructor of [PyYAML][]: include other [YAML][] files into current [YAML][] document.

In version `2.0`, [fsspec][] was introduced. With it, we can even include files by HTTP, SFTP, S3 ...

> ⚠️ **Warning** \
> “pyyaml-include” `2.0` is **NOT compatible** with `1.0`

## Install

```bash
pip install "pyyaml-include"
```

Since we are using [fsspec][] to open including files from v2.0, an installation can be performed like below, if want to open remote files:

- for files on website:

  ```bash
  pip install "pyyaml-include" fsspec[http]
  ```

- for files on S3:

  ```bash
  pip install "pyyaml-include" fsspec[s3]
  ```

- see [fsspec][]'s documentation for more

> 🔖 **Tip** \
> “pyyaml-include” depends on [fsspec][], it will be installed no matter including local or remote files.

## Basic usages

Consider we have such [YAML][] files:

```
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

To include `1.yml`, `2.yml` in `0.yml`, we shall:

1. Register a `yaml_include.Constructor` to [PyYAML][]'s loader class, with `!inc` as it's tag:

   ```python
   import yaml
   import yaml_include

   # add the tag
   yaml.add_constructor("!inc", yaml_include.Constructor(base_dir='/your/conf/dir'))
   ```

1. Write `!inc` tags in `0.yaml`:

   ```yaml
   file1: !inc include.d/1.yml
   file2: !inc include.d/1.yml
   ```

1. Load it

   ```python
   with open('0.yml') as f:
      data = yaml.full_load(f)
   print(data)
   ```

   we'll get:

   ```python
   {'file1':{'name':'1'},'file2':{'name':'2'}}
   ```

1. (optional) the constructor can be unregistered:

   ```python
   del yaml.Loader.yaml_constructors["!inc"]
   del yaml.UnSafeLoader.yaml_constructors["!inc"]
   del yaml.FullLoader.yaml_constructors["!inc"]
   ```

### Include in Mapping

If `0.yml` was:

```yaml
file1: !inc include.d/1.yml
file2: !inc include.d/2.yml
```

We'll get:

```yaml
file1:
  name: "1"
file2:
  name: "2"
```

### Include in Sequence

If `0.yml` was:

```yaml
files:
  - !inc include.d/1.yml
  - !inc include.d/2.yml
```

We'll get:

```yaml
files:
  - name: "1"
  - name: "2"
```

## Advanced usages

### Wildcards

File name can contain shell-style wildcards. Data loaded from the file(s) found by wildcards will be set in a sequence.

That is, a list will be returned when including file name contains wildcards.
Length of the returned list equals number of matched files:

If `0.yml` was:

```yaml
files: !inc include.d/*.yml
```

We'll get:

```yaml
files:
  - name: "1"
  - name: "2"
```

- when only 1 file matched, length of list will be 1
- when there are no files matched, an empty list will be returned

We support `**`, `?` and `[..]`. We do not support `^` for pattern negation.
The `maxdepth` option is applied on the first `**` found in the path.

> ❗ **Important**
>
> - Using the `**` pattern in large directory trees or remote file system (S3, HTTP ...) may consume an inordinate amount of time.
> - There is no method like lazy-load or iteration, all data of found files returned to the YAML doc-tree are fully loaded in memory, large amount of memory may be needed if there were many or big files.

### Work with fsspec

In `v2.0`, we use [fsspec][] to open including files, thus we can include files from many different sources, such as local file system, S3, HTTP, SFTP ...

For example, we can include a file from website in YAML:

```yaml
conf:
  logging: !inc http://domain/etc/app/conf.d/logging.yml
```

In such situations, when creating a `Constructor` constructor, a [fsspec][] filesystem object shall be set to `fs` argument.

For example, if want to include files from website, we shall:

1. create a `Constructor` with a [fsspec][] HTTP filesystem object as it's `fs`:

   ```python
   import yaml
   import fsspec
   import yaml_include

   http_fs = fsspec.filesystem("http", client_kwargs={"base_url": f"http://{HOST}:{PORT}"})

   ctor = yaml_include.Constructor(fs=http_fs, base_dir="/foo/baz")
   yaml.add_constructor("!inc", ctor, yaml.Loader)
   ```

1. then, write a [YAML][] document to include files from `http://${HOST}:${PORT}`:

   ```yaml
   key1: !inc doc1.yml    # relative path to "base_dir"
   key2: !inc ./doc2.yml  # relative path to "base_dir" also
   key3: !inc /doc3.yml   # absolute path, "base_dir" does not affect
   key3: !inc ../doc4.yml # relative path one level upper to "base_dir"
   ```

1. load it with [PyYAML][]:

   ```python
   yaml.load(yaml_string, yaml.Loader)
   ```

Above [YAML][] snippet will be loaded like:

- `key1`: pared YAML of `http://${HOST}:${PORT}/foo/baz/doc1.yml`
- `key2`: pared YAML of `http://${HOST}:${PORT}/foo/baz/doc2.yml`
- `key3`: pared YAML of `http://${HOST}:${PORT}/doc3.yml`
- `key4`: pared YAML of `http://${HOST}:${PORT}/foo/doc4.yml`

> 🔖 **Tip** \
> Check [fsspec][]'s documentation for more

---

> ℹ️ **Note** \
> If `fs` argument is omitted, a `"file"`/`"local"` [fsspec][] filesystem object will be used automatically. That is to say:
>
> ```yaml
> data: !inc: foo/baz.yaml
> ```
>
> is equivalent to (if no `base_dir` was set in `Constructor()`):
>
> ```yaml
> data: !inc: file://foo/baz.yaml
> ```
>
> and
>
> ```python
> yaml.add_constructor("!inc", Constructor())
> ```
>
> is equivalent to:
>
> ```python
> yaml.add_constructor("!inc", Constructor(fs=fsspec.filesystem("file")))
> ```

### Parameters in YAML

As a callable object, `Constructor` passes YAML tag parameters to [fsspec][] for more detailed operations.

The first argument is `urlpath`, it's fixed and must-required, either positional or named.
Normally, we put it as a string after the tag(eg: `!inc`), just like examples above.

However, there are more parameters.

- in a sequence way, parameters will be passed to python as positional arguments, like `*args` in python function. eg:

  ```yaml
  files: !inc [include.d/**/*.yaml, {maxdepth: 1}, {encoding: utf16}]
  ```

- in a mapping way, parameters will be passed to python as named arguments, like `**kwargs` in python function. eg:

  ```yaml
  files: !inc {urlpath: /foo/baz.yaml, encoding: utf16}
  ```

But the format of parameters has multiple cases, and differs variably in different [fsspec][] implementation backends.

- If a scheme/protocol(“`http://`”, “`sftp://`”, “`file://`”, etc.) is defined, and there is no wildcard in `urlpath`, `Constructor` will invoke [`fsspec.open`](https://filesystem-spec.readthedocs.io/en/stable/api.html#fsspec.open) directly to open it. Which means `Constructor`'s `fs` will be ignored, and a new standalone `fs` will be created implicitly.

  In this situation, `urlpath` will be passed to `fsspec.open`'s first argument, and all other parameters will also be passed to the function.

  For example,

  - the [YAML][] snippet

    ```yaml
    files: !inc [file:///foo/baz.yaml, r]
    ```

    will cause python code like

    ```python
    with fsspec.open("file:///foo/baz.yaml", "r") as f:
        yaml.load(f, Loader)
    ```

  - and the [YAML][] snippet

    ```yaml
    files: !inc {urlpath: file:///foo/baz.yaml, encoding: utf16}
    ```

    will cause python code like

    ```python
    with fsspec.open("file:///foo/baz.yaml", encoding="utf16") as f:
        yaml.load(f, Loader)
    ```

- If `urlpath` has wildcard, and also scheme in it, `Constructor` will:

  Invoke [fsspec][]'s [`open_files`](https://filesystem-spec.readthedocs.io/en/stable/api.html#fsspec.open_files) function to search, open and load files, and return the results in a list. [YAML][] include statement's parameters are passed to `open_files` function.

- If `urlpath` has wildcard, and no scheme in it, `Constructor` will:

  1. invoke corresponding [fsspec][] implementation backend's [`glob`](https://filesystem-spec.readthedocs.io/en/stable/api.html#fsspec.spec.AbstractFileSystem.glob) method to search files,
  1. then call [`open`](https://filesystem-spec.readthedocs.io/en/stable/api.html#fsspec.spec.AbstractFileSystem.open) method to open each found file(s).

  `urlpath` will be passed as the first argument to both `glob` and `open` method of the corresponding [fsspec][] implementation backend, and other parameters will also be passed to `glob` and `open` method as their following arguments.

  In the case of wildcards, what need to pay special attention to is that there are **two separated parameters** after `urlpath`, the first is for `glob` method, and the second is for `open` method. Each of them could be either sequence, mapping or scalar, corresponds single, positional and named argument(s) in python. For example:

  - If we want to include every `.yml` file in directory `etc/app` recursively with max depth at 2, and open them in utf-16 codec, we shall write the [YAML][] as below:

    ```yaml
    files: !inc ["etc/app/**/*.yml", {maxdepth: !!int "2"}, {encoding: utf16}]
    ```

    it will cause python code like:

    ```python
    for file in local_fs.glob("etc/app/**/*.yml", maxdepth=2):
        with local_fs.open(file, encoding="utf16") as f:
            yaml.load(f, Loader)
    ```

  - Since `maxdepth` is the seconde argument after `path` in `glob` method, we can also write the [YAML][] like this:

    ```yaml
    files: !inc ["etc/app/**/*.yml", [!!int "2"]]
    ```

    The parameters for `open` is omitted, means no more arguments except `urlpath` is passed.

    it will cause python code like:

    ```python
    for file in local_fs.glob("etc/app/**/*.yml", 2):
        with local_fs.open(file) as f:
            yaml.load(f, Loader)
    ```

  - The two parameters can be in a mapping form, and name of the keys are `"glob"` and `"open"`. for example:

    ```yaml
    files: !inc {urlpath: "etc/app/**/*.yml", glob: [!!int "2"], open: {encoding: utf16}}
    ```

  > ❗ **Important** \
  > [PyYAML][] sometimes takes scalar parameter of custom constructor as string, we can use a ‘Standard YAML tag’ to ensure non-string data type in the situation.
  >
  > For example, following [YAML][] snippet may cause an error:
  >
  > ```yaml
  > files: !inc ["etc/app/**/*.yml", open: {intParam: 1}]
  > ```
  >
  > Because [PyYAML][] treats `{"intParam": 1}` as `{"intParam": "1"}`, which makes python code like `fs.open(path, intParam="1")`. To prevent this, we shall write the [YAML][] like:
  >
  > ```yaml
  > files: !inc ["etc/app/**/*.yml", open: {intParam: !!int 1}]
  > ```
  >
  > where `!!int` is a ‘Standard YAML tag’ to force integer type of `maxdepth` argument.
  >
  > > ℹ️ **Note** \
  > > `BaseLoader`, `SafeLoader`, `CBaseLoader`, `CSafeLoader` do **NOT** support ‘Standard YAML tag’.
  > ---
  > > 🔖 **Tip** \
  > > `maxdepth` argument of [fsspec][] `glob` method is already force converted by `Constructor`, no need to write a `!!int` tag on it.

- Else, `Constructor` will invoke corresponding [fsspec][] implementation backend's [`open`](https://filesystem-spec.readthedocs.io/en/stable/api.html#fsspec.spec.AbstractFileSystem.open) method to open the file, parameters beside `urlpath` will be passed to the method.

### Absolute and Relative URL/Path

When the path after include tag (eg: `!inc`) is not a full protocol/scheme URL and not starts with `"/"`, `Constructor` tries to join the path with `base_dir`, which is a argument of `Constructor.__init__()`.
If `base_dir` is omitted or `None`, the actually including file path is the path in defined in [YAML][] without a change, and different [fsspec][] filesystem will treat them differently. In local filesystem, it will be `cwd`.

For remote filesystem, `HTTP` for example, the `base_dir` can not be `None` and usually be set to `"/"`.

Relative path does not support full protocol/scheme URL format, `base_dir` does not effect for that.

For example, if we register such a `Constructor` to [PyYAML][]:

```python
import yaml
import fsspec
import yaml_include

yaml.add_constructor(
    "!http-include",
    yaml_include.Constructor(
        fsspec.filesystem("http", client_kwargs={"base_url": f"http://{HOST}:{PORT}"}),
        base_dir="/sub_1/sub_1_1"
    )
)
```

then, load following [YAML][]:

```yaml
xyz: !http-include xyz.yml
```

the actual URL to access is `http://$HOST:$PORT/sub_1/sub_1_1/xyz.yml`

### Flatten sequence object in multiple matched files

Consider we have such a YAML:

```yaml
items: !include "*.yaml"
```

If every file matches `*.yaml` contains a sequence object at the top level in it, what parsed and loaded will be:

```yaml
items: [
    [item 0 of 1st file, item 1 of 1st file, ... , item n of 1st file, ...],
    [item 0 of 2nd file, item 1 of 2nd file, ... , item n of 2nd file, ...],
    # ....
    [item 0 of nth file, item 1 of nth file, ... , item n of nth file, ...],
    # ...
]
```

It's a 2-dim array, because YAML content of each matched file is treated as a member of the list(sequence).

But if `flatten` parameter was set to `true`, like:

```yaml
items: !include {urlpath: "*.yaml", flatten: true}
```

we'll get:

```yaml
items: [
    item 0 of 1st file, item 1 of 1st file, ... , item n of 1st file,  # ...
    item 0 of 2nd file, item 1 of 2nd file, ... , item n of 2nd file,  # ...
    # ....
    item 0 of n-th file, item 1 of n-th file, ... , item n of n-th file,  # ...
    # ...
]
```

> ℹ️ **Note**
>
> - Only available when multiple files were matched.
> - **Every matched file should have a Sequence object in its top level**, or a `TypeError` exception may be thrown.

### Serialization

When load [YAML][] string with include statement, the including files are default parsed into python objects. Thant is, if we call `yaml.dump()` on the object, what dumped is the parsed python object, and can not serialize the include statement itself.

To serialize the statement, we shall first create an `yaml_include.Constructor` object whose **`autoload` is `False`**:

```python
import yaml
import yaml_include

ctor = yaml_include.Constructor(autoload=False)
```

then add both Constructor for Loader and Representer for Dumper:

```python
yaml.add_constructor("!inc", ctor)

rpr = yaml_include.Representer("inc")
yaml.add_representer(yaml_include.Data, rpr)
```

Now, the including files will not be loaded when call `yaml.load()`, and `yaml_include.Data` objects will be placed at the positions where include statements are.

continue above code:

```python
yaml_str = """
- !inc include.d/1.yaml
- !inc include.d/2.yaml
"""

d0 = yaml.load(yaml_str, yaml.Loader)
# Here, "include.d/1.yaml" and "include.d/2.yaml" not be opened or loaded.
# d0 is like:
# [Data(urlpath="include.d/1.yaml"), Data(urlpath="include.d/2.yaml")]

# serialize d0
s = yaml.dump(d0)
print(s)
# ‘s’ will be:
# - !inc 'include.d/1.yaml'
# - !inc 'include.d/2.yaml'

# de-serialization
ctor.autoload = True # re-open auto load
# then load, the file "include.d/1.yaml" and "include.d/2.yaml" will be opened and loaded.
d1 = yaml.load(s, yaml.Loader)

# Or perform a recursive opening / parsing on the object:
d2 = yaml_include.load(d0) # d2 is equal to d1
```

`autoload` can be used in a `with` statement:

```python
ctor = yaml_include.Constructor()
# autoload is True here

with ctor.managed_autoload(False):
    # temporary set autoload to False
    yaml.full_load(YAML_TEXT)
# autoload restore True automatic
```

### Include JSON or TOML

We can include files in different format other than [YAML][], like [JSON][] or [TOML][] -- ``custom_loader`` is for that.

> 📑 **Example** \
> For example:
>
> ```python
> import json
> import tomllib as toml
> import yaml
> import yaml_include
>
> # Define loader function
> def my_loader(urlpath, file, Loader):
>     if urlpath.endswith(".json"):
>         return json.load(file)
>     if urlpath.endswith(".toml"):
>         return toml.load(file)
>     return yaml.load(file, Loader)
>
> # Create the include constructor, with the custom loader
> ctor = yaml_include.Constructor(custom_loader=my_loader)
>
> # Add the constructor to YAML Loader
> yaml.add_constructor("!inc", ctor, yaml.Loader)
>
> # Then, json files will can be loaded by std-lib's json module, and the same to toml files.
> s = """
> json: !inc "*.json"
> toml: !inc "*.toml"
> yaml: !inc "*.yaml"
> """
>
> yaml.load(s, yaml.Loader)
> ```

## Develop

1. clone the repo:

   ```bash
   git clone https://github.com/tanbro/pyyaml-include.git
   cd pyyaml-include
   ```

1. create then activate a python virtual-env:

   ```bash
   python -m venv .venv
   .venv/bin/activate
   ```

1. install development requirements and the project itself in editable mode:

   ```bash
   pip install -r requirements.txt
   ```

Now you can work on it.

## Test

read: `tests/README.md`

[YAML]: http://yaml.org/ "YAML: YAML Ain't Markup Language™"
[PyYaml]: https://pypi.org/project/PyYAML/ "PyYAML is a full-featured YAML framework for the Python programming language."
[fsspec]: https://github.com/fsspec/filesystem_spec/ "Filesystem Spec (fsspec) is a project to provide a unified pythonic interface to local, remote and embedded file systems and bytes storage."
[JSON]: https://json.io/ "JSON (JavaScript Object Notation) is a lightweight data-interchange format. It is easy for humans to read and write"
[TOML]: https://toml.io/ "TOML aims to be a minimal configuration file format that's easy to read due to obvious semantics."
