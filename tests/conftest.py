from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api import app as app_module
from services.translation_service import TranslationService


@pytest.fixture
def translation_service():
    return TranslationService()


@pytest.fixture
def client(tmp_path: Path):
    feedback_file = tmp_path / "feedback.json"
    app_module.FEEDBACK_FILE_PATH = feedback_file
    app_module.feedback_store.clear()

    app_module.app.config.update(
        TESTING=True,
        RATELIMIT_ENABLED=True,
        RATELIMIT_DEFAULT="10 per minute",
        RATELIMIT_HEADERS_ENABLED=True,
    )

    with app_module.app.test_client() as test_client:
        yield test_client

    app_module.feedback_store.clear()
