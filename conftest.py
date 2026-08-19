"""Repo-root conftest: guarantees `import hodge` and `import rig` resolve.

pytest inserts the directory containing the rootdir conftest.py onto sys.path,
so this file existing is what makes the single-file instrument (hodge.py, at the
repo root per spec 11) importable from tests without any packaging step.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
