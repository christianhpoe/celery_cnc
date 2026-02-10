from __future__ import annotations

from typing import TYPE_CHECKING

from celery_cnc.config import LoggingConfigFile
from celery_cnc.core.logging.adapters.file import FileLogController

if TYPE_CHECKING:
    from pathlib import Path


def test_file_log_controller_writes_rotating_file(tmp_path: Path) -> None:
    config = LoggingConfigFile(log_dir=tmp_path, log_rotation_hours=1)
    controller = FileLogController()

    controller.configure(config)
    logger = controller.get_logger("cnc-test")
    logger.info("hello log")
    controller.shutdown()

    log_files = list(tmp_path.glob("celery_cnc-cnc-test.log*"))
    assert log_files, "log file should be created"
    content = log_files[0].read_text(encoding="utf-8")
    assert "hello log" in content
