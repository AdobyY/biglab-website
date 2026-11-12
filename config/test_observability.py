"""Exercise SDK startup and Django exception capture without external requests."""

import os
from pathlib import Path
import subprocess
import sys

from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parent.parent


class SentryConfigurationTests(SimpleTestCase):
    def run_settings(self, module, script, **values):
        env = {key: value for key, value in os.environ.items() if not key.startswith("SENTRY_")}
        env.update(
            DJANGO_SETTINGS_MODULE=module,
            DJANGO_SECRET_KEY="test-runtime-key-not-a-deployment-secret",
            DJANGO_ALLOWED_HOSTS="testserver",
            WAGTAILADMIN_BASE_URL="https://testserver",
            DJANGO_SECURE_SSL_REDIRECT="false",
            **values,
        )
        result = subprocess.run(
            [sys.executable, "-c", script], cwd=ROOT, env=env,
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_dsn_disables_monitoring_in_both_serving_settings(self):
        for module in ("config.settings.dev", "config.settings.production"):
            with self.subTest(module=module):
                self.run_settings(module, """
from django.conf import settings
from unittest.mock import patch
with patch('sentry_sdk.init') as initialize:
    assert settings.ALLOWED_HOSTS
initialize.assert_not_called()
""")

    def test_image_build_does_not_initialize_sentry_even_with_a_dsn(self):
        self.run_settings("config.settings.build", """
from django.conf import settings
from unittest.mock import patch
with patch('sentry_sdk.init') as initialize:
    assert settings.SECRET_KEY
initialize.assert_not_called()
""", SENTRY_DSN="https://public@example.invalid/1")

    def test_running_django_captures_errors_without_cms_body_or_local_variables(self):
        script = """
import json
import secrets
import django
import sentry_sdk
from sentry_sdk.transport import Transport
from unittest.mock import patch

events = []
class MemoryTransport(Transport):
    def capture_envelope(self, envelope):
        for item in envelope.items:
            if item.type == 'event':
                events.append(item.payload.json)

initialize = sentry_sdk.init
def initialize_without_network(*args, **kwargs):
    return initialize(*args, **kwargs, transport=MemoryTransport)
with patch('sentry_sdk.init', initialize_without_network):
    django.setup()

from django.conf import settings
from django.test import Client, override_settings
from django.urls import path

def fail(request):
    private_editor_text = request.POST['draft_text']
    raise RuntimeError('Django Sentry integration verification')

urlpatterns = [path('verify/', fail)]
private_text = secrets.token_urlsafe(32)
with override_settings(ROOT_URLCONF=__name__, MIDDLEWARE=[]):
    response = Client(raise_request_exception=False).post('/verify/', {'draft_text':private_text})
assert response.status_code == 500
sentry_sdk.flush(timeout=2)
assert len(events) == 1, len(events)
event = events[0]
assert event['exception']['values'][-1]['type'] == 'RuntimeError'
assert event['environment'] == ('development' if settings.DEBUG else 'production')
assert event['release'] == 'test-railway-commit'
assert private_text not in json.dumps(event)
assert not event.get('request', {}).get('data')
assert all(not f.get('vars') for value in event['exception']['values'] for f in value['stacktrace']['frames'])
options = sentry_sdk.get_client().options
assert options['traces_sample_rate'] == (1.0 if settings.DEBUG else 0.1)
"""
        for module in ("config.settings.dev", "config.settings.production"):
            with self.subTest(module=module):
                self.run_settings(module, script, SENTRY_DSN="https://public@example.invalid/1",
                                  RAILWAY_GIT_COMMIT_SHA="test-railway-commit")

    def test_invalid_trace_sampling_is_reported_at_startup(self):
        script = """
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
try:
    settings.DEBUG
except ImproperlyConfigured as error:
    assert 'SENTRY_TRACES_SAMPLE_RATE' in str(error)
else:
    raise AssertionError('Invalid sampling configuration was accepted')
"""
        for rate in ("not-a-number", "NaN", "1.1"):
            with self.subTest(rate=rate):
                self.run_settings("config.settings.production", script,
                                  SENTRY_DSN="https://public@example.invalid/1", SENTRY_TRACES_SAMPLE_RATE=rate)
