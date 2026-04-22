"""Pytest bootstrap: expose `custom_components/` on sys.path for tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "custom_components"))
