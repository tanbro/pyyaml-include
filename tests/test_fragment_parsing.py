"""
Tests for the internal `path:key.subkey` fragment-splitting logic, specifically that it
does not misparse a Windows drive letter (``C:\\...`` / ``C:/...``) as a fragment separator.

These exercise the string-splitting logic directly (via `FRAGMENT_PATTERN`), so they run on
any OS -- no real Windows filesystem is required.
"""

from yaml_include.constructor import FRAGMENT_PATTERN


def _split(urlpath):
    """Mirror the splitting logic in `Constructor.load`."""
    match = FRAGMENT_PATTERN.search(urlpath)
    if match:
        return urlpath[: match.start()], urlpath[match.start() + 1 :]
    return urlpath, None


class TestFragmentSplittingVsDriveLetters:
    def test_windows_backslash_path_not_split(self):
        urlpath, objpath = _split(r"C:\Users\foo\bar.yaml")
        assert urlpath == r"C:\Users\foo\bar.yaml"
        assert objpath is None

    def test_windows_forward_slash_path_not_split(self):
        urlpath, objpath = _split("C:/Users/foo/bar.yaml")
        assert urlpath == "C:/Users/foo/bar.yaml"
        assert objpath is None

    def test_plain_fragment_still_split(self):
        urlpath, objpath = _split("path/to/file.yaml:top.mid.leaf")
        assert urlpath == "path/to/file.yaml"
        assert objpath == "top.mid.leaf"

    def test_single_level_fragment_still_split(self):
        urlpath, objpath = _split("fragment.yaml:top")
        assert urlpath == "fragment.yaml"
        assert objpath == "top"

    def test_no_fragment_no_colon(self):
        urlpath, objpath = _split("plain/path.yaml")
        assert urlpath == "plain/path.yaml"
        assert objpath is None
