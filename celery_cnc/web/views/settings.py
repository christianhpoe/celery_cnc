"""Settings page views."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.shortcuts import render

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

_THEMES: tuple[tuple[str, str], ...] = (
    ("monokai", "Monokai"),
    ("darkula", "Darkula"),
    ("generic", "Generic"),
    ("dark", "Dark"),
    ("white", "White"),
    ("solaris", "Solaris"),
)


def settings_page(request: HttpRequest) -> HttpResponse:
    """Render the settings page."""
    return render(
        request,
        "settings.html",
        {
            "title": "Settings",
            "themes": _THEMES,
        },
    )
