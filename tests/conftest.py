from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.fixtures.app_one import app as app_one
from tests.fixtures.app_two import app as app_two

if TYPE_CHECKING:
    from celery import Celery


@pytest.fixture
def celery_app_one() -> Celery:
    return app_one


@pytest.fixture
def celery_app_two() -> Celery:
    return app_two
