import os
import sys
from collections import deque
from typing import Dict, Optional, Any
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStatusBar, QApplication,
    QMessageBox, QInputDialog, QMenuBar, QMenu, QFileDialog,
    QSystemTrayIcon, QDialog,
)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence, QIcon

from app.widgets.toolbar import ToolBar
from app.widgets.tab_bar import TabBar
from app.widgets.download_list import DownloadList
from app.widgets.download_item import DownloadItemWidget
from app.models.video_info import VideoInfo
from app.models.database import DownloadDatabase
from app.models import session_state
from app.utils.helpers import is_youtube_url, resource_path
from app.utils.settings_manager import SettingsManager
from app.utils.i18n import tr, get_language, set_language
from app.version import RELEASES_PAGE, __version__


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app.title"))
        self.setMinimumSize(900, 600)
        self.resize(1000, 650)

        # App icon
        self._ico_path = resource_path("app", "resources", "app_icon.ico")
        self._app_icon = QIcon(self._ico_path)
        if not self._app_icon.isNull():
            self.setWindowIcon(self._app_icon)

        self._settings = SettingsManager()
        self.db = DownloadDatabase()
        self._workers: Dict[str, Any] = {}
        self._download_queue: deque = deque()  # queued VideoInfo objects
        self._info_worker: Optional[Any] = None
        self._update_worker: Optional[Any] = None
        self._app_update_worker: Optional[Any] = None
        self._app_update_silent = False
        self._force_quit = False
        self._downloads_paused = False

        self._setup_menubar()
        self._setup_ui()
        self._setup_tray()
        self._connect_signals()
        self._load_stylesheet()
        self._start_bridge_server()

        # 창 표시 후 무거운 작업 지연 실행
        QTimer.singleShot(0, self._load_history)
        QTimer.singleShot(50, self._restore_session)
        QTimer.singleShot(100, self._auto_check_ytdlp_update)
        QTimer.singleShot(150, self._auto_check_app_update)

    def _setup_menubar(self):
        menubar = self.menuBar()
        self._menu_actions = []  # [(action, i18n_key)]
        self._menus = {}         # i18n_key -> QMenu

        def add_menu(title_key: str, parent_menu=None) -> QMenu:
            if parent_menu is None:
                menu = menubar.addMenu(tr(title_key))
            else:
                menu = QMenu(tr(title_key), self)
                parent_menu.addMenu(menu)
            self._menus[title_key] = menu
            return menu

        def add_action(menu, key: str, slot, shortcut=None, enabled=True):
            act = QAction(tr(key), self)
            if shortcut:
                act.setShortcut(QKeySequence(shortcut))
            act.setEnabled(enabled)
            act.triggered.connect(slot)
            menu.addAction(act)
            self._menu_actions.append((act, key))
            return act

        # 파일 메뉴
        file_menu = add_menu("menu.file")
        add_action(file_menu, "action.paste_link", self._on_paste)
        file_menu.addSeparator()
        add_action(file_menu, "action.change_save_path", self._change_save_path)
        add_action(file_menu, "action.open_save_folder", self._open_save_folder)
        file_menu.addSeparator()
        add_action(file_menu, "action.exit", self.close, shortcut="Alt+F4")

        # 수정 메뉴
        edit_menu = add_menu("menu.edit")
        add_action(edit_menu, "action.paste_link_ellipsis", self._on_paste,
                   shortcut="Ctrl+V")
        edit_menu.addSeparator()

        watch_later_menu = add_menu("menu.watch_later", edit_menu)
        add_action(watch_later_menu, "action.playlist_download",
                   lambda: self._download_playlist_type("watch_later"))
        add_action(watch_later_menu, "action.playlist_subscribe",
                   lambda: self._subscribe_playlist("watch_later"), enabled=False)

        liked_menu = add_menu("menu.liked", edit_menu)
        add_action(liked_menu, "action.playlist_download",
                   lambda: self._download_playlist_type("liked"))
        add_action(liked_menu, "action.playlist_subscribe",
                   lambda: self._subscribe_playlist("liked"), enabled=False)

        edit_menu.addSeparator()
        add_action(edit_menu, "action.pause_all", self._pause_all)
        add_action(edit_menu, "action.resume_all", self._resume_all)
        add_action(edit_menu, "action.remove_all", self._remove_all)

        # 보기 메뉴
        view_menu = add_menu("menu.view")
        add_action(view_menu, "tab.all", lambda: self.tab_bar._on_tab_click("전체"))
        add_action(view_menu, "tab.video", lambda: self.tab_bar._on_tab_click("동영상"))
        add_action(view_menu, "tab.audio", lambda: self.tab_bar._on_tab_click("오디오"))
        add_action(view_menu, "tab.playlist",
                   lambda: self.tab_bar._on_tab_click("재생 목록"))

        # 도구 메뉴
        tools_menu = add_menu("menu.tools")
        add_action(tools_menu, "action.control_panel", self._show_control_panel)
        add_action(tools_menu, "action.preferences", self._show_preferences)
        add_action(tools_menu, "action.license", self._show_license, enabled=False)
        add_action(tools_menu, "action.check_update", self._check_update)
        tools_menu.addSeparator()
        add_action(tools_menu, "action.ytdlp_update", self._update_ytdlp)

        # 도움말 메뉴
        help_menu = add_menu("menu.help")
        add_action(help_menu, "action.about", self._show_about)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        self.toolbar = ToolBar()
        self.toolbar.setObjectName("toolbar")
        layout.addWidget(self.toolbar)

        # Tab bar
        self.tab_bar = TabBar()
        self.tab_bar.setObjectName("tabBarWidget")
        layout.addWidget(self.tab_bar)

        # Download list
        self.download_list = DownloadList()
        layout.addWidget(self.download_list, stretch=1)

        # Control panel (overlay, right-side)
        from app.widgets.control_panel import ControlPanel
        self.control_panel = ControlPanel(central)
        self.control_panel.setVisible(False)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(tr("msg.ready"))

    def _setup_tray(self):
        """Initialize system tray icon with context menu."""
        self.tray_icon = QSystemTrayIcon(self)
        if not self._app_icon.isNull():
            self.tray_icon.setIcon(self._app_icon)
        else:
            self.tray_icon.setIcon(self.style().standardIcon(
                self.style().StandardPixmap.SP_ComputerIcon
            ))
        self.tray_icon.setToolTip("Stock Video Automator")

        tray_menu = QMenu(self)
        self._tray_actions = []
        act_show = QAction(tr("tray.open"), self)
        act_show.triggered.connect(self._tray_show)
        tray_menu.addAction(act_show)
        self._tray_actions.append((act_show, "tray.open"))

        tray_menu.addSeparator()

        act_quit = QAction(tr("tray.exit"), self)
        act_quit.triggered.connect(self._tray_quit)
        tray_menu.addAction(act_quit)
        self._tray_actions.append((act_quit, "tray.exit"))

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)

        if self._settings.run_in_background:
            self.tray_icon.show()

    def _tray_show(self):
        self.showNormal()
        self.activateWindow()

    def _tray_quit(self):
        self._force_quit = True
        self.close()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._tray_show()

    def _connect_signals(self):
        self.toolbar.paste_clicked.connect(self._on_paste)
        self.tab_bar.tab_changed.connect(self._on_tab_changed)
        self.download_list.count_changed.connect(self.tab_bar.set_count)
        self.download_list.cancel_requested.connect(self._cancel_download)
        self.download_list.format_requested.connect(self._on_format_requested)

        # Control panel signals
        self.control_panel.preferences_requested.connect(self._show_preferences)
        self.control_panel.login_requested.connect(self._on_youtube_login)
        self.control_panel.liked_download_requested.connect(
            lambda: self._download_playlist_type("liked")
        )
        self.control_panel.watch_later_requested.connect(
            lambda: self._download_playlist_type("watch_later")
        )
        self.control_panel.license_requested.connect(self._show_license)
        self.control_panel.support_requested.connect(self._show_support)

        # Search filter
        self.tab_bar.search_changed.connect(self._on_search_filter)

        # Sort
        self.tab_bar.sort_changed.connect(self.download_list.sort_items)

    def _load_stylesheet(self):
        qss_path = resource_path("app", "resources", "style.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _retranslate_ui(self):
        """언어 변경 시 메뉴/툴바/탭바/제어판 텍스트를 갱신한다."""
        self.setWindowTitle(tr("app.title"))
        for key, menu in self._menus.items():
            menu.setTitle(tr(key))
        for act, key in self._menu_actions:
            act.setText(tr(key))
        for act, key in getattr(self, "_tray_actions", []):
            act.setText(tr(key))
        self.toolbar.retranslate()
        self.tab_bar.retranslate()
        self.control_panel.retranslate()
        self.download_list.retranslate()
        self.status_bar.showMessage(tr("msg.ready"))

    # ── MCP Bridge Server ─────────────────────────────────────

    def _start_bridge_server(self):
        from app.bridge.bridge_server import BridgeServer
        self._bridge_server = BridgeServer(self, parent=self)
        self._bridge_server.start()

    # ── Load history ───────────────────────────────────────────

    def _load_history(self):
        records = self.db.get_all_records()
        for rec in reversed(records):  # oldest first
            vi = VideoInfo(
                url=rec.get("url", ""),
                video_id=rec.get("video_id", ""),
                title=rec.get("title", ""),
                channel=rec.get("channel", ""),
                duration=rec.get("duration") or 0,
                thumbnail_url=rec.get("thumbnail_url", ""),
                filesize_approx=rec.get("filesize") or 0,
                ext=rec.get("format", "mp4"),
                status="completed",
                downloaded_path=rec.get("file_path", ""),
                download_type=rec.get("download_type", "video"),
                selected_quality=rec.get("quality", ""),
            )
            widget = self.download_list.add_item(vi)
            widget.set_completed(vi.downloaded_path)

        count = len(records)
        if count > 0:
            self.status_bar.showMessage(tr("msg.loaded_history", count=count))

    # ── Session persistence (앱 재시작 후 이어받기) ──────────

    def _restore_session(self):
        """이전 실행에서 완료되지 않은 다운로드를 일시정지 상태로 복원한다."""
        try:
            items = session_state.load()
        except Exception:
            return
        if not items:
            return

        for vi in items:
            vi.status = "paused"
            widget = self.download_list.add_item(vi)
            if widget:
                widget._update_status_badge("paused")

        self.status_bar.showMessage(tr("msg.restored", count=len(items)))

    _ACTIVE_STATUSES = {"downloading", "paused", "waiting", "pending"}

    def _persist_active_downloads(self):
        """진행 중/대기 중/일시정지된 다운로드 목록을 디스크에 저장한다."""
        items = [
            item.video_info
            for item in self.download_list.get_all_items()
            if item.video_info.status in self._ACTIVE_STATUSES
        ]
        session_state.save(items)

    # ── Paste / URL handling ─────────────────────────────────

    def _on_paste(self):
        clipboard = QApplication.clipboard()
        url = clipboard.text().strip() if clipboard else ""

        if not url or not is_youtube_url(url):
            url, ok = QInputDialog.getText(
                self, tr("dlg.url_input"), tr("dlg.url_prompt"),
                text=url,
            )
            if not ok or not url:
                return
            if not is_youtube_url(url):
                QMessageBox.warning(self, tr("dlg.error"), tr("dlg.invalid_url"))
                return

        self._fetch_info(url)

    def _fetch_info(self, url: str):
        if self._info_worker and self._info_worker.isRunning():
            QMessageBox.information(
                self, tr("dlg.notice"), tr("dlg.info_loading")
            )
            return

        self.status_bar.showMessage(tr("msg.fetching_info"))
        from app.workers.info_worker import InfoWorker
        self._info_worker = InfoWorker(url)
        self._info_worker.info_ready.connect(self._on_info_ready)
        self._info_worker.playlist_ready.connect(self._on_playlist_ready)
        self._info_worker.error.connect(self._on_info_error)
        self._info_worker.status_message.connect(self.status_bar.showMessage)
        self._info_worker.start()

    def _collect_options(self) -> dict:
        """현재 툴바 설정을 DownloadWorker 인자 형태로 수집한다."""
        return {
            "save_dir": self.toolbar.save_path,
            "download_type": self.toolbar.download_type,
            "quality": self.toolbar.quality,
            "fmt": self.toolbar.format,
            "subtitle": self.toolbar.subtitle_enabled,
            "subtitle_lang": self.toolbar.subtitle_lang,
            "audio_track": self.toolbar.audio_track,
            "frame_rate": self.toolbar.frame_rate,
            "codec": self.toolbar.codec,
            "format_selector": "",
        }

    def _on_info_ready(self, video_info: VideoInfo):
        video_info.download_type = self.toolbar.download_type
        video_info.selected_quality = self.toolbar.quality
        video_info.ext = self.toolbar.format
        video_info.options = self._collect_options()

        self.download_list.add_item(video_info)
        self._start_download(video_info)
        self.status_bar.showMessage(tr("msg.download_start"))

    def _on_playlist_ready(self, videos: list):
        self.status_bar.showMessage(tr("msg.playlist_found", count=len(videos)))
        for vi in videos:
            vi.download_type = self.toolbar.download_type
            vi.selected_quality = self.toolbar.quality
            vi.ext = self.toolbar.format
            vi.options = self._collect_options()
            self.download_list.add_item(vi)
            self._start_download(vi)

    def _on_info_error(self, msg: str):
        self.status_bar.showMessage(tr("msg.error_occurred"))
        QMessageBox.warning(self, tr("dlg.error"), msg)

    # ── Download management ──────────────────────────────────

    def _start_download(self, video_info: VideoInfo):
        """Queue or start a download respecting concurrent limit."""
        max_concurrent = self._settings.concurrent_downloads
        if len(self._workers) >= max_concurrent:
            self._download_queue.append(video_info)
            widget = self.download_list.get_item(video_info.video_id)
            if widget:
                widget._update_status_badge("waiting")
            self._persist_active_downloads()
            return

        self._launch_worker(video_info)

    def _launch_worker(self, video_info: VideoInfo):
        from app.workers.download_worker import DownloadWorker
        # 저장된 옵션이 일부만 있어도 기본값으로 채워 항상 완전한 옵션을 구성한다
        options = {**self._collect_options(), **(video_info.options or {})}
        worker = DownloadWorker(video_info=video_info, **options)
        worker.progress.connect(self._on_download_progress)
        worker.finished.connect(self._on_download_finished)
        worker.error.connect(self._on_download_error)
        worker.paused.connect(self._on_download_paused)
        self._workers[video_info.video_id] = worker
        worker.start()
        self._persist_active_downloads()

    def _process_queue(self):
        """Start queued downloads if slots are available."""
        if self._downloads_paused:
            return
        max_concurrent = self._settings.concurrent_downloads
        while self._download_queue and len(self._workers) < max_concurrent:
            vi = self._download_queue.popleft()
            self._launch_worker(vi)

    def _on_download_progress(self, video_id: str, data: dict):
        widget = self.download_list.get_item(video_id)
        if widget:
            widget.update_progress(data)

    def _on_download_finished(self, video_id: str, file_path: str):
        widget = self.download_list.get_item(video_id)
        if widget:
            widget.set_completed(file_path)
            vi = widget.video_info
            self.db.add_record(
                url=vi.url,
                video_id=vi.video_id,
                title=vi.title,
                channel=vi.channel,
                thumbnail_url=vi.thumbnail_url,
                file_path=file_path,
                fmt=vi.ext,
                quality=vi.selected_quality,
                filesize=vi.filesize_approx,
                duration=vi.duration,
                download_type=vi.download_type,
            )

        self._workers.pop(video_id, None)
        self._process_queue()
        self._persist_active_downloads()

        active = len(self._workers)
        queued = len(self._download_queue)
        if active > 0:
            msg = tr("msg.downloading_progress", active=active)
            if queued > 0:
                msg += tr("msg.queued", queued=queued)
            msg += ")"
            self.status_bar.showMessage(msg)
        else:
            self.status_bar.showMessage(tr("msg.all_complete"))

        # Notifications
        title = widget.video_info.title if widget else video_id
        if self._settings.notify_download_complete:
            if self._settings.notify_tray and self.tray_icon.isVisible():
                self.tray_icon.showMessage(
                    tr("notify.complete"), title,
                    QSystemTrayIcon.MessageIcon.Information, 3000,
                )
            if self._settings.notify_sound:
                self._play_notification_sound()

        if widget:
            self.control_panel.update_notification(
                tr("notify.complete"), widget.video_info.title
            )

        self._reapply_sort()

    def _on_download_error(self, video_id: str, msg: str):
        widget = self.download_list.get_item(video_id)
        if widget:
            widget.set_error(msg)
        self._workers.pop(video_id, None)
        self._process_queue()
        self._persist_active_downloads()
        self._reapply_sort()
        self.status_bar.showMessage(tr("msg.error", message=msg))

        # Error notification
        if self._settings.notify_download_error:
            title = widget.video_info.title if widget else video_id
            if self._settings.notify_tray and self.tray_icon.isVisible():
                self.tray_icon.showMessage(
                    tr("notify.error"), f"{title}\n{msg}",
                    QSystemTrayIcon.MessageIcon.Warning, 5000,
                )

    def _on_download_paused(self, video_id: str):
        widget = self.download_list.get_item(video_id)
        if widget:
            widget.video_info.status = "paused"
            widget._update_status_badge("paused")
        self._workers.pop(video_id, None)
        self._process_queue()
        self._persist_active_downloads()
        self._reapply_sort()
        self.status_bar.showMessage(tr("msg.download_paused"))

    def _play_notification_sound(self):
        """운영체제 공통 알림음을 재생한다."""
        if sys.platform == "win32":
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
                return
            except Exception:
                pass
        try:
            QApplication.beep()
        except Exception:
            pass

    def _cancel_download(self, video_id: str):
        worker = self._workers.get(video_id)
        if worker:
            worker.cancel()

    def _on_format_requested(self, video_id: str):
        widget = self.download_list.get_item(video_id)
        if not widget:
            return
        vi = widget.video_info

        if vi.status == "downloading":
            QMessageBox.information(
                self, tr("dlg.notice"), tr("dlg.downloading_no_change")
            )
            return
        if not vi.formats:
            QMessageBox.information(
                self, tr("dlg.format_title"), tr("dlg.format_no_info")
            )
            return

        from app.widgets.format_dialog import FormatDialog
        dlg = FormatDialog(vi, self.toolbar.download_type, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        selector = dlg.selected_selector()
        vi.options = {**self._collect_options(), **(vi.options or {})}
        vi.options["format_selector"] = selector
        if selector:
            self.status_bar.showMessage(
                tr("msg.format_download", label=dlg.selected_label())
            )
        else:
            self.status_bar.showMessage(tr("msg.current_settings_download"))
        vi.status = "pending"
        widget._update_status_badge("waiting")
        self._start_download(vi)

    # ── Tab / Search filtering ──────────────────────────────

    def _apply_filters(self):
        """Apply both tab filter and search text filter."""
        tab_name = self.tab_bar.current_tab
        search_text = self.tab_bar.search_input.text().strip().lower()

        for item in self.download_list.get_all_items():
            # Tab filter
            if tab_name == "전체":
                tab_match = True
            elif tab_name == "동영상":
                tab_match = item.video_info.download_type == "video"
            elif tab_name == "오디오":
                tab_match = item.video_info.download_type == "audio"
            elif tab_name == "재생 목록":
                tab_match = item.video_info.is_playlist
            else:
                tab_match = True

            # Search filter
            if search_text:
                title = (item.video_info.title or "").lower()
                channel = (item.video_info.channel or "").lower()
                search_match = search_text in title or search_text in channel
            else:
                search_match = True

            item.setVisible(tab_match and search_match)

    def _on_tab_changed(self, tab_name: str):
        self._apply_filters()

    def _on_search_filter(self, text: str):
        self._apply_filters()

    def _reapply_sort(self):
        """현재 정렬 설정으로 목록을 다시 정렬한다."""
        key = self.tab_bar._sort_key
        ascending = self.tab_bar._sort_ascending
        self.download_list.sort_items(key, ascending)

    # ── Menu actions ────────────────────────────────────────

    def _change_save_path(self):
        path = QFileDialog.getExistingDirectory(
            self, tr("dlg.choose_folder"), self.toolbar.save_path
        )
        if path:
            self.toolbar._save_path = path
            display = self.toolbar._get_display_path()
            self.toolbar.btn_save_path.setText(f"📂 {display}  ▾")
            self.toolbar.save_path_changed.emit(path)

    def _open_save_folder(self):
        path = self.toolbar.save_path
        if os.path.isdir(path):
            if sys.platform == "win32":
                os.startfile(path)
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _clear_list(self):
        for item in list(self.download_list.get_all_items()):
            if item.video_info.status != "downloading":
                self.download_list._remove_item(item.video_info.video_id)

    def _clear_history(self):
        reply = QMessageBox.question(
            self, tr("dlg.confirm"), tr("dlg.clear_history"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_all()
            self._clear_list()
            self.status_bar.showMessage(tr("msg.history_cleared"))

    def _pause_all(self):
        self._downloads_paused = True
        paused = 0

        # 진행 중인 다운로드는 partial 파일을 남기고 일시정지
        for vid, worker in list(self._workers.items()):
            worker.pause()
            paused += 1

        # 대기 중인 항목도 일시정지 상태로 전환하고 큐를 비운다
        while self._download_queue:
            vi = self._download_queue.popleft()
            widget = self.download_list.get_item(vi.video_id)
            if widget:
                widget.video_info.status = "paused"
                widget._update_status_badge("paused")
            paused += 1

        self._persist_active_downloads()
        if paused > 0:
            self.status_bar.showMessage(tr("msg.paused_count", count=paused))
        else:
            self.status_bar.showMessage(tr("msg.nothing_to_pause"))

    def _resume_all(self):
        self._downloads_paused = False
        resumed = 0
        for item in self.download_list.get_all_items():
            if item.video_info.status == "paused":
                item.video_info.status = "downloading"
                item._update_status_badge("waiting")
                self._start_download(item.video_info)
                resumed += 1
        self._process_queue()
        self._persist_active_downloads()
        if resumed > 0:
            self.status_bar.showMessage(tr("msg.resumed_count", count=resumed))
        else:
            self.status_bar.showMessage(tr("msg.nothing_to_resume"))

    def _remove_all(self):
        reply = QMessageBox.question(
            self, tr("dlg.confirm"), tr("dlg.remove_all_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Cancel active downloads first
            for worker in list(self._workers.values()):
                worker.cancel()
            self._workers.clear()
            self._download_queue.clear()
            self._downloads_paused = False

            for item in list(self.download_list.get_all_items()):
                self.download_list._remove_item(item.video_info.video_id)
            self._persist_active_downloads()
            self.status_bar.showMessage(tr("msg.removed_all"))

    def _has_cookies(self) -> bool:
        return bool(self._settings.get_cookie_browser_name())

    def _download_playlist_type(self, playlist_type: str):
        if playlist_type == "watch_later":
            label, url = tr("dlg.watch_later_label"), ":ytwatchlater"
        else:
            label, url = tr("dlg.liked_label"), ":ytfav"

        if not self._has_cookies():
            QMessageBox.information(
                self, tr("dlg.login_required"),
                tr("dlg.login_body", label=label),
            )
            return

        self.status_bar.showMessage(tr("msg.loading_playlist", label=label))
        self._fetch_info(url)

    def _subscribe_playlist(self, playlist_type: str):
        if playlist_type == "watch_later":
            label = tr("dlg.watch_later_label")
        else:
            label = tr("dlg.liked_label")
        QMessageBox.information(
            self, tr("dlg.notice"),
            tr("dlg.subscribe_body", label=label),
        )

    def _show_control_panel(self):
        self.control_panel.toggle()

    def _on_youtube_login(self):
        QMessageBox.information(
            self, tr("dlg.youtube_login_title"),
            tr("dlg.youtube_login_body"),
        )
        self._open_preferences(4)

    def _show_support(self):
        QMessageBox.information(
            self, tr("dlg.support_title"), tr("dlg.support_body")
        )

    def _show_preferences(self):
        self._open_preferences(0)

    def _open_preferences(self, page_index: int = 0):
        from app.widgets.preferences_dialog import PreferencesDialog
        dlg = PreferencesDialog(self)
        dlg.page_advanced.edit_path.setText(self.toolbar.save_path)
        dlg.settings_changed.connect(self._on_settings_changed)
        dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        if page_index:
            dlg._select_page(page_index)
        dlg.show()

    def _on_settings_changed(self):
        """React to preference changes."""
        s = self._settings

        # 언어 변경 반영
        if s.language != get_language():
            set_language(s.language)
            self._retranslate_ui()

        # Sync save path from settings to toolbar
        save_path = s.default_save_path
        if save_path and save_path != self.toolbar.save_path:
            self.toolbar._save_path = save_path
            display = self.toolbar._get_display_path()
            self.toolbar.btn_save_path.setText(f"📂 {display}  ▾")

        # Show/hide tray icon based on background setting
        if s.run_in_background:
            self.tray_icon.show()
        else:
            self.tray_icon.hide()

    def _show_license(self):
        QMessageBox.information(
            self, tr("dlg.license_title"), tr("dlg.license_body")
        )

    def _check_update(self):
        if self._app_update_worker and self._app_update_worker.isRunning():
            QMessageBox.information(
                self, tr("dlg.notice"), tr("dlg.already_checking")
            )
            return
        self._run_app_update_check(silent=False)

    def _auto_check_app_update(self):
        """설정이 켜져 있으면 시작 시 조용히 앱 업데이트를 확인한다."""
        if self._settings.auto_update:
            self._run_app_update_check(silent=True)

    def _run_app_update_check(self, silent: bool = False):
        from app.workers.app_update_worker import AppUpdateWorker
        self._app_update_silent = silent
        self._app_update_worker = AppUpdateWorker()
        self._app_update_worker.finished.connect(self._on_app_update_result)
        if not silent:
            self.status_bar.showMessage(tr("msg.update_checking"))
        self._app_update_worker.start()

    def _on_app_update_result(self, success: bool, info: dict):
        silent = self._app_update_silent
        if not success:
            if not silent:
                QMessageBox.warning(
                    self, tr("dlg.update_check_fail"),
                    info.get("error", tr("dlg.unknown_error")),
                )
                self.status_bar.showMessage(tr("msg.ready"))
            return

        if info.get("update_available"):
            latest = info.get("latest_version", "")
            reply = QMessageBox.question(
                self, tr("dlg.update_available_title"),
                tr("dlg.update_available_body",
                   latest=latest,
                   current=info.get("current_version", "")),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                QDesktopServices.openUrl(
                    QUrl(info.get("html_url") or RELEASES_PAGE)
                )
            self.status_bar.showMessage(
                tr("msg.update_available", version=latest), 5000
            )
        elif not silent:
            QMessageBox.information(
                self, tr("dlg.latest_title"),
                tr("dlg.latest_body", version=info.get("current_version", "")),
            )
            self.status_bar.showMessage(tr("msg.ready"))

    # ── yt-dlp update ────────────────────────────────────────

    def _auto_check_ytdlp_update(self):
        """프로그램 시작 시 자동으로 yt-dlp 업데이트 체크."""
        self._run_ytdlp_update(silent=True)

    def _update_ytdlp(self):
        """사용자가 수동으로 yt-dlp 업데이트 실행."""
        if self._update_worker and self._update_worker.isRunning():
            QMessageBox.information(
                self, tr("dlg.notice"), tr("dlg.already_updating")
            )
            return
        self._run_ytdlp_update(silent=False)

    def _run_ytdlp_update(self, silent: bool = False):
        import sys
        from app.workers.update_worker import YtDlpUpdateWorker
        self._update_silent = silent
        self._update_worker = YtDlpUpdateWorker(python_path=sys.executable)
        self._update_worker.status_message.connect(self._on_update_status)
        self._update_worker.finished.connect(self._on_update_finished)
        self._update_worker.start()

    def _on_update_status(self, msg: str):
        self.status_bar.showMessage(msg)

    def _on_update_finished(self, success: bool, msg: str):
        if self._update_silent:
            # 자동 체크: 상태바에만 표시
            if success:
                self.status_bar.showMessage(msg, 5000)
            else:
                self.status_bar.showMessage(
                    tr("msg.ytdlp_fail", message=msg), 5000
                )
        else:
            # 수동 업데이트: 메시지박스로 결과 표시
            if success:
                QMessageBox.information(self, tr("dlg.ytdlp_update_title"), msg)
            else:
                QMessageBox.warning(
                    self, tr("dlg.ytdlp_update_fail_title"), msg
                )
            self.status_bar.showMessage(tr("msg.ready"))

    def _show_about(self):
        QMessageBox.about(
            self, tr("app.title"),
            f"{tr('app.title')} v{__version__}\n\n"
            f"{tr('dlg.about_body')}"
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        central = self.centralWidget()
        if central and hasattr(self, 'control_panel'):
            self.control_panel.reposition(
                central.width(), central.height()
            )

    def closeEvent(self, event):
        # Minimize to tray if background running is enabled
        if self._settings.run_in_background and not self._force_quit:
            event.ignore()
            self.hide()
            if self.tray_icon.isVisible():
                self.tray_icon.showMessage(
                    tr("app.title"),
                    tr("msg.background_running"),
                    QSystemTrayIcon.MessageIcon.Information, 2000,
                )
            return

        # Actually quit: persist active downloads, stop bridge, cancel workers
        self._persist_active_downloads()
        if hasattr(self, '_bridge_server'):
            self._bridge_server.stop()
        for worker in self._workers.values():
            if hasattr(worker, 'cancel'):
                worker.cancel()
                worker.wait(2000)
        self.tray_icon.hide()
        event.accept()
