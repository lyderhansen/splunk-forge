"""Shared pytest setup for FAKE_DATA plugin tests.

Adds templates/runtime/ and data/ to sys.path so tests can import the
modules exactly as they will be imported after copy into a user workspace.
"""
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "templates" / "runtime"))
sys.path.insert(0, str(PLUGIN_ROOT / "data"))
