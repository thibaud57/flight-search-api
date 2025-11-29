"""Générateur d'URLs Google Flights avec remplacement dynamique des dates."""

from __future__ import annotations

import base64
import binascii
import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from app.core.constants import DATE_PATTERN_YYYY_MM_DD


class GoogleFlightsUrlError(Exception):
    """Erreur lors de la génération d'URL Google Flights."""


def generate_google_flights_url(template_url: str, new_dates: list[str]) -> str:
    """
    Génère une URL Google Flights en remplaçant les dates dans le paramètre tfs encodé.
    """
    for date in new_dates:
        if not DATE_PATTERN_YYYY_MM_DD.match(date):
            msg = f"Date invalide '{date}'. Format attendu : YYYY-MM-DD"
            raise GoogleFlightsUrlError(msg)

    parsed = urlparse(template_url)
    query_params = parse_qs(parsed.query)

    if "tfs" not in query_params:
        msg = "Paramètre 'tfs' manquant dans l'URL template"
        raise GoogleFlightsUrlError(msg)

    tfs_encoded = query_params["tfs"][0]

    try:
        tfs_decoded = base64.urlsafe_b64decode(tfs_encoded + "==")
    except (ValueError, TypeError, binascii.Error) as e:
        msg = f"Erreur décodage base64 du paramètre tfs: {e}"
        raise GoogleFlightsUrlError(msg) from e

    current_dates = re.findall(rb"20\d{2}-\d{2}-\d{2}", tfs_decoded)
    if len(current_dates) != len(new_dates):
        msg = (
            f"Nombre de dates incorrect. Template contient {len(current_dates)} dates, "
            f"mais {len(new_dates)} nouvelles dates fournies"
        )
        raise GoogleFlightsUrlError(msg)

    tfs_modified = tfs_decoded
    for old_date, new_date in zip(current_dates, new_dates, strict=True):
        tfs_modified = tfs_modified.replace(old_date, new_date.encode())

    tfs_new_encoded = base64.urlsafe_b64encode(tfs_modified).decode().rstrip("=")

    query_params["tfs"] = [tfs_new_encoded]
    new_query = urlencode(query_params, doseq=True)
    new_url = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        )
    )

    return new_url
