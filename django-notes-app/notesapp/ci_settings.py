"""Isolated CI settings. App's normal MySQL settings remain unchanged."""
from .settings import *  # noqa: F403

SECRET_KEY = "local-ci-only-not-a-production-secret"
DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "ci.sqlite3",  # noqa: F405
    }
}
# The backend CI does not compile or validate the bundled React frontend.
STATICFILES_DIRS = []
STATIC_ROOT = BASE_DIR / "ci-artifacts" / "static"  # noqa: F405
