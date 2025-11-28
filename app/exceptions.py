"""Exceptions custom pour flight-search-api."""


class CaptchaDetectedError(Exception):
    """Levée quand un captcha est détecté dans le HTML."""

    def __init__(self, url: str, captcha_type: str) -> None:
        self.url = url
        self.captcha_type = captcha_type
        super().__init__(f"Captcha {captcha_type} detected at {url}")


class ParsingError(Exception):
    """Levée quand le parsing HTML échoue."""

    def __init__(
        self, message: str, html_size: int = 0, flights_found: int = 0
    ) -> None:
        self.html_size = html_size
        self.flights_found = flights_found
        super().__init__(message)


class NetworkError(Exception):
    """Levée lors d'erreurs réseau."""

    def __init__(
        self, url: str, status_code: int | None = None, attempts: int = 1
    ) -> None:
        self.url = url
        self.status_code = status_code
        self.attempts = attempts
        msg = f"Network error at {url}"
        if status_code:
            msg += f" (status: {status_code})"
        super().__init__(msg)


class SessionCaptureError(Exception):
    """Levée quand la capture de session échoue (cookies vides ou erreur)."""

    def __init__(self, provider: str, reason: str) -> None:
        self.provider = provider
        self.reason = reason
        super().__init__(f"Session capture failed for {provider}: {reason}")
