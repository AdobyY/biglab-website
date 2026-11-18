from django.shortcuts import render
from django.views import defaults


def server_error(request):
    try:
        return render(request, "500.html", {"error_layout": "base.html"}, status=500)
    except Exception:
        # The CMS or the shared layout may itself be the source of the error.
        return defaults.server_error(request)
