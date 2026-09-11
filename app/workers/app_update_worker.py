"""GitHub Releases를 조회해 앱 자체 업데이트 여부를 확인하는 워커."""

from PySide6.QtCore import QThread, Signal

from app.utils.logger import get_logger
from app.version import RELEASES_API, __version__, is_newer

logger = get_logger(__name__)


class AppUpdateWorker(QThread):
    """GitHub Releases API로 최신 버전을 확인한다."""

    finished = Signal(bool, dict)  # success, info

    def run(self):
        import requests

        try:
            response = requests.get(
                RELEASES_API,
                timeout=10,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": f"StockVideoAutomator/{__version__}",
                },
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.info("앱 업데이트 확인 실패: %s", e)
            self.finished.emit(False, {"error": str(e)})
            return

        latest = data.get("tag_name") or data.get("name") or ""
        assets = data.get("assets") or []
        info = {
            "latest_version": latest,
            "current_version": __version__,
            "update_available": is_newer(latest, __version__),
            "name": data.get("name", ""),
            "body": data.get("body", ""),
            "html_url": data.get("html_url", ""),
            "assets": [
                {
                    "name": a.get("name", ""),
                    "url": a.get("browser_download_url", ""),
                }
                for a in assets
            ],
        }
        self.finished.emit(True, info)
