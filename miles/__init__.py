"""
Top-level package initialiser for **miles**.

Having this file turns the ``miles`` directory into a proper Python package,
which allows absolute imports such as

    import miles.plugins.plugin
"""

# Re-export the *plugins* sub-package so callers can do
#     import miles.plugins
# without an extra import.
from importlib import import_module

plugins = import_module("miles.plugins")

__all__ = ["plugins"]
