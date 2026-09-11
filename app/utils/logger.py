"""애플리케이션 전역 로깅 설정.

콘솔(stderr)과 회전 파일 핸들러를 함께 구성한다. `setup_logging()`은
여러 번 호출되어도 한 번만 초기화된다.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from app.utils.helpers import app_data_dir

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_MAX_BYTES = 2 * 1024 * 1024
_BACKUP_COUNT = 3
_configured = False


def setup_logging(level: int = logging.INFO) -> None:
    """루트 로거를 초기화한다. 이미 초기화된 경우 아무 것도 하지 않는다."""
    global _configured
    if _configured:
        return
    _configured = True

    root = logging.getLogger()
    root.setLevel(level)

    formatter = logging.Formatter(_LOG_FORMAT)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    try:
        log_dir = os.path.join(app_data_dir(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "app.log"),
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError:
        root.warning("파일 로그 핸들러를 초기화하지 못했습니다.", exc_info=True)


def get_logger(name: str) -> logging.Logger:
    """이름 기반 로거를 반환한다."""
    return logging.getLogger(name)
