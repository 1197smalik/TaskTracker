"""Smoke tests for backend project discovery and importability."""

from taskmaster_backend import __version__


def test_package_version_is_defined() -> None:
    assert __version__ == "0.1.0"
