"""Secret-free settings for image-time collectstatic only; never serve requests."""

from .base import *

DEBUG = False
# A public build-only constant, not a runtime credential or an environment secret.
SECRET_KEY = "collectstatic-only-not-for-serving-requests"
ALLOWED_HOSTS = []
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
STORAGES["staticfiles"]["BACKEND"] = (
    "whitenoise.storage.CompressedStaticFilesStorage"
)
