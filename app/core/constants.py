"""Constantes globales application (valeurs hardcodées immuables)."""

from __future__ import annotations

import re
from typing import Final, Pattern

# === Date Patterns ===
DATE_PATTERN_YYYY_MM_DD: Final[Pattern[str]] = re.compile(r"^\d{4}-\d{2}-\d{2}$")
