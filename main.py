import sys
import multiprocessing


def _install_excepthook(logger):
    """처리되지 않은 예외를 로그로 남긴다."""
    def _hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logger.critical(
            "처리되지 않은 예외", exc_info=(exc_type, exc_value, exc_tb)
        )
    sys.excepthook = _hook


def main():
    import os
    import ctypes

    # Ensure the project root is in the path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from app.utils.logger import setup_logging, get_logger
    setup_logging()
    logger = get_logger(__name__)
    _install_excepthook(logger)

    # Windows taskbar icon fix
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "stockvideoautomator.app.1.0"
        )

    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QIcon
    from app.utils.helpers import resource_path

    app = QApplication(sys.argv)
    app.setApplicationName("Stock Video Automator")
    app.setStyle("Fusion")

    # 환경 설정 초기화 (deno, ffmpeg 경로 탐색 등)
    from app.utils.helpers import setup_environment
    setup_environment()

    # App icon — show() 전에 QApplication에 먼저 설정
    icon_path = resource_path("app", "resources", "app_icon.ico")
    icon = QIcon(icon_path)
    if not icon.isNull():
        app.setWindowIcon(icon)

    from app.main_window import MainWindow

    window = MainWindow()

    # Windows 작업표시줄 아이콘 강제 반영: hide→show 사이클
    # 투명 상태로 첫 show를 수행해 깜빡임 방지
    if sys.platform == "win32":
        window.setWindowOpacity(0)
        window.show()
        app.processEvents()
        window.hide()
        app.processEvents()
        window.setWindowOpacity(1)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
