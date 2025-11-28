"""Constantes globales application (valeurs hardcodées immuables)."""

from __future__ import annotations

import re
from re import Pattern
from typing import Final

# === Date Patterns ===
DATE_PATTERN_YYYY_MM_DD: Final[Pattern[str]] = re.compile(r"^\d{4}-\d{2}-\d{2}$")
