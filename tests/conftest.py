"""Make `python_sim` importable under pytest.

If the package is installed (for example via `pip install .`), the tests use
that build, which includes the compiled `_core` extension. Only when it is not
importable do we fall back to the repo root (the source tree), appended rather
than prepended so an installed build is never shadowed by an un-built checkout.
"""
import importlib.util
import sys
from pathlib import Path

if importlib.util.find_spec("python_sim") is None:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
