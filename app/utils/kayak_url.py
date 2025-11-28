"""Générateur d'URLs Kayak avec remplacement dynamique des dates."""

from __future__ import annotations

import re

from app.core import DATE_PATTERN_YYYY_MM_DD


class KayakUrlError(Exception):
    """Erreur lors de la génération d'URL Kayak."""


def generate_kayak_url(template_url: str, new_dates: list[str]) -> str:
    """Génère une URL Kayak en remplaçant les dates dans le path."""
    for date in new_dates:
        if not DATE_PATTERN_YYYY_MM_DD.match(date):
            msg = f"Date invalide '{date}'. Format attendu : YYYY-MM-DD"
            raise KayakUrlError(msg)

    current_dates = re.findall(r"20\d{2}-\d{2}-\d{2}", template_url)

    if len(current_dates) != len(new_dates):
        msg = (
            f"Nombre de dates incorrect. Template contient {len(current_dates)} dates, "
            f"mais {len(new_dates)} nouvelles dates fournies"
        )
        raise KayakUrlError(msg)

    result_url = template_url
    for old_date, new_date in zip(current_dates, new_dates, strict=True):
        result_url = result_url.replace(old_date, new_date, 1)

    return result_url
