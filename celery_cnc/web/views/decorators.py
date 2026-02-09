"""Typed wrappers for Django view decorators."""

from __future__ import annotations

from collections.abc import Callable

from django.http import HttpResponse
from django.views.decorators.http import require_POST as _require_post


def require_post[ViewFuncT: Callable[..., HttpResponse]](view_func: ViewFuncT) -> ViewFuncT:
    """Typed alias for Django's require_POST decorator."""
    return _require_post(view_func)
