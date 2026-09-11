import os
import subprocess
import sys
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar, QPushButton,
    QSizePolicy, QMenu,
)
from PySide6.QtCore import Qt, Signal, QSize, QUrl, QThread
from PySide6.QtGui import QPixmap, QDesktopServices, QMouseEvent

from app.models.video_info import VideoInfo
from app.utils.helpers import format_duration, format_file_size, format_speed
from app.utils.i18n import tr


class _ThumbnailLoader(QThread):
    """Background thread to download a thumbnail image."""

    loaded = Signal(bytes)  # raw image data
    failed = Signal()

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self._url = url

    def run(self):
        try:
            import requests
            resp = requests.get(self._url, timeout=5)
            if resp.status_code == 200:
                self.loaded.emit(resp.content)
            else:
                self.failed.emit()
        except Exception:
            self.failed.emit()


class DownloadItemWidget(QWidget):
    """Single download item widget showing thumbnail, info, progress."""

    cancel_requested = Signal(str)  # video_id
    remove_requested = Signal(str)  # video_id
    format_requested = Signal(str)  # video_id — 형식 선택 요청
    clicked = Signal(str)  # video_id — for selection management

    def __init__(self, video_info: VideoInfo, parent=None):
        super().__init__(parent)
        self.video_info = video_info
        self._selected = False
        self._setup_ui()
        self._load_thumbnail()

    def _setup_ui(self):
        self.setObjectName("downloadItem")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumHeight(90)
        self.setMaximumHeight(100)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # Thumbnail
        self.lbl_thumbnail = QLabel()
        self.lbl_thumbnail.setFixedSize(QSize(120, 68))
        self.lbl_thumbnail.setObjectName("thumbnail")
        self.lbl_thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_thumbnail.setScaledContents(True)
        self.lbl_thumbnail.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.lbl_thumbnail)

        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        title_row = QHBoxLayout()
        self.lbl_title = QLabel(self.video_info.title)
        self.lbl_title.setObjectName("itemTitle")
        self.lbl_title.setWordWrap(False)
        self.lbl_title.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.lbl_title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        title_row.addWidget(self.lbl_title)

        # Status Badge
        self.lbl_status_badge = QLabel(tr("status.waiting"))
        self.lbl_status_badge.setObjectName("statusBadge")
        self.lbl_status_badge.setProperty("status", "waiting")
        self.lbl_status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status_badge.setFixedWidth(70)
        title_row.addWidget(self.lbl_status_badge)
        info_layout.addLayout(title_row)

        # Meta info
        meta_parts = []
        if self.video_info.duration:
            meta_parts.append(format_duration(self.video_info.duration))
        if self.video_info.filesize_approx:
            meta_parts.append(format_file_size(self.video_info.filesize_approx))
        if self.video_info.ext:
            meta_parts.append(self.video_info.ext.upper())
        if self.video_info.channel:
            meta_parts.append(self.video_info.channel)

        meta_text = " · ".join(meta_parts) if meta_parts else ""
        self.lbl_meta = QLabel(meta_text)
        self.lbl_meta.setObjectName("itemMeta")
        self.lbl_meta.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        info_layout.addWidget(self.lbl_meta)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("itemProgress")
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        info_layout.addWidget(self.progress_bar)

        layout.addLayout(info_layout, stretch=1)

        # Speed label
        self.lbl_speed = QLabel("")
        self.lbl_speed.setObjectName("itemMeta")
        self.lbl_speed.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_speed.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.lbl_speed)

        # Buttons
        self.btn_folder = QPushButton("📂")
        self.btn_folder.setObjectName("itemFolderButton")
        self.btn_folder.setFixedSize(32, 32)
        self.btn_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_folder.clicked.connect(self._on_open_folder)
        self.btn_folder.setVisible(False)
        layout.addWidget(self.btn_folder)

        self.btn_action = QPushButton("✕")
        self.btn_action.setObjectName("itemActionButton")
        self.btn_action.setFixedSize(32, 32)
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.clicked.connect(self._on_action)
        layout.addWidget(self.btn_action)

    def _update_status_badge(self, status: str, text: str = ""):
        self.lbl_status_badge.setProperty("status", status)
        self.lbl_status_badge.setText(text if text else self._get_status_text(status))
        self.lbl_status_badge.style().unpolish(self.lbl_status_badge)
        self.lbl_status_badge.style().polish(self.lbl_status_badge)

    def _get_status_text(self, status: str) -> str:
        key = f"status.{status}"
        text = tr(key)
        return status if text == key else text

    def _load_thumbnail(self):
        if not self.video_info.thumbnail_url:
            self.lbl_thumbnail.setText("No Image")
            return
        self.lbl_thumbnail.setText("...")
        self._thumb_loader = _ThumbnailLoader(self.video_info.thumbnail_url, self)
        self._thumb_loader.loaded.connect(self._on_thumbnail_loaded)
        self._thumb_loader.failed.connect(self._on_thumbnail_failed)
        self._thumb_loader.start()

    def _on_thumbnail_loaded(self, data: bytes):
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        self.lbl_thumbnail.setPixmap(
            pixmap.scaled(
                120, 68,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _on_thumbnail_failed(self):
        self.lbl_thumbnail.setText("No Image")

    def update_progress(self, data: dict):
        status = data.get("status", "")

        if status == "downloading":
            pct = data.get("progress", 0)
            speed = data.get("speed", 0)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(int(pct))
            self.lbl_speed.setText(format_speed(speed))
            self._update_status_badge("downloading")
            self.video_info.status = "downloading"

        elif status == "processing":
            self.progress_bar.setValue(100)
            self.lbl_speed.setText("")
            self._update_status_badge("processing")

    def set_completed(self, file_path: str):
        self.video_info.status = "completed"
        self.video_info.downloaded_path = file_path
        self.progress_bar.setVisible(False)
        self.lbl_speed.setText("")
        self._update_status_badge("completed")
        self.btn_action.setText("✕")
        self.btn_folder.setVisible(True)

    def set_error(self, msg: str):
        self.video_info.status = "error"
        self.video_info.error_message = msg
        self.progress_bar.setVisible(False)
        self.lbl_speed.setText("")
        self._update_status_badge("error")

    # -- Selection -----------------------------------------------------------

    def set_selected(self, selected: bool):
        self._selected = selected
        # QSS [selected="true"] matches string, not bool
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    @property
    def is_selected(self) -> bool:
        return self._selected

    def mousePressEvent(self, event: QMouseEvent):
        self.clicked.emit(self.video_info.video_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if (self.video_info.status == "completed"
                and self.video_info.downloaded_path
                and os.path.isfile(self.video_info.downloaded_path)):
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(self.video_info.downloaded_path)
            )
        else:
            super().mouseDoubleClickEvent(event)

    # -- Actions --------------------------------------------------------------

    def _on_open_folder(self):
        path = self.video_info.downloaded_path
        if path and os.path.exists(path):
            folder = os.path.dirname(path)
            if sys.platform == "win32":
                subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def _on_action(self):
        if self.video_info.status == "downloading":
            self.cancel_requested.emit(self.video_info.video_id)
        else:
            self.remove_requested.emit(self.video_info.video_id)

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        act_format = menu.addAction("형식 선택...")
        act_format.setEnabled(self.video_info.status != "downloading")
        act_format.triggered.connect(
            lambda: self.format_requested.emit(self.video_info.video_id)
        )

        if (self.video_info.status == "completed"
                and self.video_info.downloaded_path):
            act_open = menu.addAction("파일 열기")
            act_open.triggered.connect(self._on_open_file)
            act_folder = menu.addAction("폴더 열기")
            act_folder.triggered.connect(self._on_open_folder)

        menu.addSeparator()
        act_remove = menu.addAction("목록에서 제거")
        act_remove.triggered.connect(
            lambda: self.remove_requested.emit(self.video_info.video_id)
        )

        menu.exec(event.globalPos())

    def _on_open_file(self):
        path = self.video_info.downloaded_path
        if path and os.path.isfile(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
