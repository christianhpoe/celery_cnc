# SPDX-FileCopyrightText: 2026 Christian-Hauke Poensgen
# SPDX-FileCopyrightText: 2026 Maximilian Dolling
# SPDX-FileContributor: AUTHORS.md
#
# SPDX-License-Identifier: BSD-3-Clause

"""Shared helpers for logging identifiers."""

from __future__ import annotations

import re

_COMPONENT_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def sanitize_component(component: str) -> str:
    """Return a filesystem-safe component identifier."""
    cleaned = _COMPONENT_RE.sub("_", component).strip("._-")
    return cleaned or "app"
