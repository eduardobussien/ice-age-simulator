"""The version lives in two places; make sure they never drift apart."""
import re
from pathlib import Path

import python_sim

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def test_core_version_matches_pyproject():
    # Parsed with a regex rather than tomllib so it also runs on Python < 3.11.
    match = re.search(r'^version\s*=\s*"([^"]+)"', PYPROJECT.read_text(), re.M)
    assert match, "no version line found in pyproject.toml"
    assert python_sim.__version__ == match.group(1)
