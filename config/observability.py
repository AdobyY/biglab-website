"""Shared Sentry configuration for serving Django, enabled only with a DSN."""

import os

from django.core.exceptions import ImproperlyConfigured
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


def configure_sentry(*, debug):
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        return

    raw_rate = os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "1.0" if debug else "0.1")
    try:
        trace_rate = float(raw_rate)
    except ValueError as error:
        raise ImproperlyConfigured("SENTRY_TRACES_SAMPLE_RATE must be a number from 0 to 1.") from error
    if not 0 <= trace_rate <= 1:
        raise ImproperlyConfigured("SENTRY_TRACES_SAMPLE_RATE must be a number from 0 to 1.")

    sentry_sdk.init(
        dsn=dsn,
        environment=os.environ.get("SENTRY_ENVIRONMENT") or ("development" if debug else "production"),
        release=os.environ.get("SENTRY_RELEASE") or os.environ.get("RAILWAY_GIT_COMMIT_SHA") or None,
        integrations=[DjangoIntegration(), LoggingIntegration(capture_sentry_logs=True)],
        traces_sample_rate=trace_rate,
        send_default_pii=False,
        include_local_variables=False,
        max_request_body_size="never",
    )
