"""Configuration pytest pour tests d'intégration.

Applique automatiquement le marker @pytest.mark.integration à tous les tests
du répertoire integration/.
"""

import pytest

pytestmark = pytest.mark.integration
