"""Local CMS sandbox settings; the launcher supplies isolated data paths."""
from django.core.exceptions import ImproperlyConfigured

from .dev import *

sandbox_root = BASE_DIR / ".impeccable" / "manual-testing"
if not Path(DATABASES["default"]["NAME"]).resolve().is_relative_to(sandbox_root.resolve()) or not MEDIA_ROOT.resolve().is_relative_to(sandbox_root.resolve()):
    raise ImproperlyConfigured("Start the isolated test site using .impeccable/manual-testing/manual_test.py.")

SESSION_COOKIE_NAME = "biglab_test_sessionid"
CSRF_COOKIE_NAME = "biglab_test_csrftoken"
WAGTAIL_SITE_NAME = "BIG Lab — Test sandbox"
WAGTAILADMIN_BASE_URL = "http://127.0.0.1:8020/admin"
