"""Configuration pytest globale pour tous les tests."""

import os


def pytest_configure(config):
    """Configure env vars requis avant import des modules de test.

    Cette fonction s'exécute AVANT que pytest n'importe les modules de test,
    ce qui permet de définir les variables d'environnement nécessaires pour
    l'instantiation de Settings() lors de l'import de app.main.

    Utilise setdefault pour ne pas override env vars existantes (ex: .env local).
    """
    os.environ.setdefault("DECODO_USERNAME", "customer-test-country-FR")
    os.environ.setdefault("DECODO_PASSWORD", "test_password")
    os.environ.setdefault("LOG_LEVEL", "INFO")
