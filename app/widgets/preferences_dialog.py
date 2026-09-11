"""Preferences dialog – mirrors 4K Video Downloader+ settings UI."""

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QStackedWidget, QFrame, QLineEdit, QSpinBox,
    QCheckBox, QFileDialog, QSizePolicy, QApplication,
)
from PySide6.QtCore import Qt, Signal, QSize, QEvent
from PySide6.QtGui import QFont, QPainter, QColor, QPen

from app.utils.settings_manager import SettingsManager


# ── Toggle switch ────────────────────────────────────────────────

class ToggleSwitch(QWidget):
    """Custom iOS-style toggle switch matching 4K Video Downloader+ design."""

    toggled = Signal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedSize(46, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = checked

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, val: bool):
        self._checked = val
        self.update()

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.update()
        self.toggled.emit(self._checked)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        radius = h / 2

        if self._checked:
            # ON: green filled track
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(76, 175, 80))
            painter.drawRoundedRect(0, 0, w, h, radius, radius)
            # White knob on right
            knob_d = h - 4
            knob_x = w - knob_d - 2
            painter.setBrush(QColor(255, 255, 255))
            painter.drawEllipse(int(knob_x), 2, int(knob_d), int(knob_d))
        else:
            # OFF: dark outline track
            painter.setPen(QPen(QColor(100, 100, 100), 2))
            painter.setBrush(QColor(50, 50, 50))
            painter.drawRoundedRect(1, 1, w - 2, h - 2, radius, radius)
            # Light gray knob on left
            knob_d = h - 4
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(180, 180, 180))
            painter.drawEllipse(2, 2, int(knob_d), int(knob_d))

        painter.end()


# ── Sidebar menu item ────────────────────────────────────────────

class SidebarItem(QWidget):
    """Single clickable sidebar menu entry."""

    clicked = Signal()

    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(parent)
        self.setObjectName("prefSidebarItem")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(42)
        self._selected = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        self.lbl_icon = QLabel(icon_text)
        self.lbl_icon.setObjectName("prefSidebarIcon")
        self.lbl_icon.setFixedWidth(24)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.lbl_icon)

        self.lbl_text = QLabel(label)
        self.lbl_text.setObjectName("prefSidebarText")
        self.lbl_text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.lbl_text, stretch=1)

    def set_selected(self, selected: bool):
        self._selected = selected
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


# ── Toggle row helper ────────────────────────────────────────────

def _make_toggle_row(text: str, checked: bool = False, desc: str = "") -> tuple:
    """Create a row with label + toggle switch, optionally with a description."""
    container = QWidget()
    container.setObjectName("prefToggleRow")
    outer = QVBoxLayout(container)
    outer.setContentsMargins(0, 8, 0, 8)
    outer.setSpacing(4)

    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)

    lbl = QLabel(text)
    lbl.setObjectName("prefLabel")
    lbl.setWordWrap(True)
    lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    row.addWidget(lbl, stretch=1)

    toggle = ToggleSwitch(checked)
    row.addWidget(toggle)
    outer.addLayout(row)

    if desc:
        lbl_desc = QLabel(desc)
        lbl_desc.setObjectName("prefDesc")
        lbl_desc.setWordWrap(True)
        outer.addWidget(lbl_desc)

    return container, toggle


def _make_separator() -> QFrame:
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setObjectName("prefSeparator")
    return sep


# ── Page: 일반 ───────────────────────────────────────────────────

class GeneralPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("prefPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(0)

        # Title
        title = QLabel("일 반")
        title.setObjectName("prefPageTitle")
        layout.addWidget(title)
        layout.addWidget(_make_separator())

        # 언어
        lbl_lang = QLabel("언어")
        lbl_lang.setObjectName("prefLabel")
        layout.addSpacing(12)
        layout.addWidget(lbl_lang)
        layout.addSpacing(4)

        self.combo_lang = QComboBox()
        self.combo_lang.setObjectName("prefCombo")
        self.combo_lang.addItems(["한국어", "English", "日本語", "中文"])
        self.combo_lang.setFixedHeight(36)
        layout.addWidget(self.combo_lang)

        layout.addSpacing(8)
        layout.addWidget(_make_separator())

        # Toggles
        row1, self.toggle_background = _make_toggle_row(
            "그것이 닫혔을 때 백그라운드에서 실행하기"
        )
        layout.addWidget(row1)
        layout.addWidget(_make_separator())

        row2, self.toggle_autostart = _make_toggle_row(
            "시스템 시작 시 자동으로 시작"
        )
        layout.addWidget(row2)
        layout.addWidget(_make_separator())

        row3, self.toggle_autoupdate = _make_toggle_row(
            "새로운 앱 업데이트를 자동으로 다운로드하기"
        )
        layout.addWidget(row3)
        layout.addWidget(_make_separator())

        row4, self.toggle_beta = _make_toggle_row(
            "베타 버전 설치",
            desc="베타 버전은 공식 버전보다 안정성은 떨어지지만 새 기능들이 출시되기 전에\n"
                 "먼저 사용해보실 수 있습니다. 버그와 문제가 있으면 보고해 주세요.",
        )
        layout.addWidget(row4)

        layout.addStretch()


# ── Page: 고급 설정 ──────────────────────────────────────────────

class AdvancedPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("prefPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(0)

        title = QLabel("고급 설정")
        title.setObjectName("prefPageTitle")
        layout.addWidget(title)
        layout.addWidget(_make_separator())

        # 동시 다운로드 수
        lbl_concurrent = QLabel("동시 다운로드 수")
        lbl_concurrent.setObjectName("prefLabel")
        layout.addSpacing(12)
        layout.addWidget(lbl_concurrent)
        layout.addSpacing(4)

        self.spin_concurrent = QSpinBox()
        self.spin_concurrent.setObjectName("prefSpinBox")
        self.spin_concurrent.setRange(1, 10)
        self.spin_concurrent.setValue(3)
        self.spin_concurrent.setFixedHeight(36)
        self.spin_concurrent.setFixedWidth(100)
        layout.addWidget(self.spin_concurrent)

        layout.addSpacing(8)
        layout.addWidget(_make_separator())

        # 다운로드 스레드 수
        lbl_threads = QLabel("다운로드 스레드 수")
        lbl_threads.setObjectName("prefLabel")
        layout.addSpacing(12)
        layout.addWidget(lbl_threads)
        layout.addSpacing(4)

        self.spin_threads = QSpinBox()
        self.spin_threads.setObjectName("prefSpinBox")
        self.spin_threads.setRange(1, 16)
        self.spin_threads.setValue(4)
        self.spin_threads.setFixedHeight(36)
        self.spin_threads.setFixedWidth(100)
        layout.addWidget(self.spin_threads)

        layout.addSpacing(8)
        layout.addWidget(_make_separator())

        # 기본 저장 경로
        lbl_path = QLabel("기본 저장 경로")
        lbl_path.setObjectName("prefLabel")
        layout.addSpacing(12)
        layout.addWidget(lbl_path)
        layout.addSpacing(4)

        path_row = QHBoxLayout()
        path_row.setContentsMargins(0, 0, 0, 0)
        path_row.setSpacing(8)

        self.edit_path = QLineEdit()
        self.edit_path.setObjectName("prefLineEdit")
        self.edit_path.setFixedHeight(36)
        self.edit_path.setReadOnly(True)
        path_row.addWidget(self.edit_path, stretch=1)

        btn_browse = QPushButton("탐색...")
        btn_browse.setObjectName("prefBrowseButton")
        btn_browse.setFixedHeight(36)
        btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_browse.clicked.connect(self._browse_path)
        path_row.addWidget(btn_browse)

        layout.addLayout(path_row)

        layout.addSpacing(8)
        layout.addWidget(_make_separator())

        row1, self.toggle_filename_numbering = _make_toggle_row(
            "파일명에 번호 추가 (재생목록)"
        )
        layout.addWidget(row1)

        layout.addStretch()

    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(
            self, "기본 저장 폴더 선택", self.edit_path.text()
        )
        if path:
            self.edit_path.setText(path)


# ── Page: 연결 ───────────────────────────────────────────────────

class ConnectionPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("prefPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(0)

        title = QLabel("연결")
        title.setObjectName("prefPageTitle")
        layout.addWidget(title)
        layout.addWidget(_make_separator())

        # 프록시 타입
        lbl_proxy = QLabel("프록시 유형")
        lbl_proxy.setObjectName("prefLabel")
        layout.addSpacing(12)
        layout.addWidget(lbl_proxy)
        layout.addSpacing(4)

        self.combo_proxy = QComboBox()
        self.combo_proxy.setObjectName("prefCombo")
        self.combo_proxy.addItems(["사용 안 함", "HTTP", "SOCKS5"])
        self.combo_proxy.setFixedHeight(36)
        layout.addWidget(self.combo_proxy)

        layout.addSpacing(8)
        layout.addWidget(_make_separator())

        # 프록시 주소
        lbl_addr = QLabel("프록시 주소")
        lbl_addr.setObjectName("prefLabel")
        layout.addSpacing(12)
        layout.addWidget(lbl_addr)
        layout.addSpacing(4)

        addr_row = QHBoxLayout()
        addr_row.setContentsMargins(0, 0, 0, 0)
        addr_row.setSpacing(8)

        self.edit_proxy_host = QLineEdit()
        self.edit_proxy_host.setObjectName("prefLineEdit")
        self.edit_proxy_host.setPlaceholderText("호스트")
        self.edit_proxy_host.setFixedHeight(36)
        addr_row.addWidget(self.edit_proxy_host, stretch=3)

        self.edit_proxy_port = QLineEdit()
        self.edit_proxy_port.setObjectName("prefLineEdit")
        self.edit_proxy_port.setPlaceholderText("포트")
        self.edit_proxy_port.setFixedHeight(36)
        self.edit_proxy_port.setFixedWidth(80)
        addr_row.addWidget(self.edit_proxy_port)

        layout.addLayout(addr_row)

        layout.addSpacing(8)
        layout.addWidget(_make_separator())

        # 속도 제한
        lbl_speed = QLabel("다운로드 속도 제한")
        lbl_speed.setObjectName("prefLabel")
        layout.addSpacing(12)
        layout.addWidget(lbl_speed)
        layout.addSpacing(4)

        speed_row = QHBoxLayout()
        speed_row.setContentsMargins(0, 0, 0, 0)
        speed_row.setSpacing(8)

        self.spin_speed = QSpinBox()
        self.spin_speed.setObjectName("prefSpinBox")
        self.spin_speed.setRange(0, 99999)
        self.spin_speed.setValue(0)
        self.spin_speed.setFixedHeight(36)
        self.spin_speed.setFixedWidth(100)
        self.spin_speed.setSpecialValueText("제한 없음")
        speed_row.addWidget(self.spin_speed)

        lbl_unit = QLabel("KB/s")
        lbl_unit.setObjectName("prefLabel")
        speed_row.addWidget(lbl_unit)
        speed_row.addStretch()

        layout.addLayout(speed_row)

        layout.addStretch()


# ── Page: 알림 ───────────────────────────────────────────────────

class NotificationPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("prefPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(0)

        title = QLabel("알림")
        title.setObjectName("prefPageTitle")
        layout.addWidget(title)
        layout.addWidget(_make_separator())

        row1, self.toggle_download_complete = _make_toggle_row(
            "다운로드 완료 알림", checked=True
        )
        layout.addWidget(row1)
        layout.addWidget(_make_separator())

        row2, self.toggle_download_error = _make_toggle_row(
            "다운로드 오류 알림", checked=True
        )
        layout.addWidget(row2)
        layout.addWidget(_make_separator())

        row3, self.toggle_sound = _make_toggle_row(
            "다운로드 완료 시 소리 재생"
        )
        layout.addWidget(row3)
        layout.addWidget(_make_separator())

        row4, self.toggle_tray = _make_toggle_row(
            "시스템 트레이 알림 표시", checked=True
        )
        layout.addWidget(row4)

        layout.addStretch()


# ── Page: 승인 ───────────────────────────────────────────────────

class AuthorizationPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("prefPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(0)

        title = QLabel("승인")
        title.setObjectName("prefPageTitle")
        layout.addWidget(title)
        layout.addWidget(_make_separator())

        # YouTube 계정
        layout.addSpacing(12)
        lbl_yt = QLabel("YouTube 계정")
        lbl_yt.setObjectName("prefLabel")
        layout.addWidget(lbl_yt)
        layout.addSpacing(8)

        lbl_yt_desc = QLabel(
            "YouTube 계정으로 로그인하여 개인 재생목록,\n"
            "좋아요 표시한 동영상, 나중에 볼 동영상에 접근하세요."
        )
        lbl_yt_desc.setObjectName("prefDesc")
        lbl_yt_desc.setWordWrap(True)
        layout.addWidget(lbl_yt_desc)
        layout.addSpacing(12)

        self.btn_youtube_login = QPushButton("YouTube 로그인")
        self.btn_youtube_login.setObjectName("prefActionButton")
        self.btn_youtube_login.setFixedHeight(36)
        self.btn_youtube_login.setFixedWidth(160)
        self.btn_youtube_login.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.btn_youtube_login)

        layout.addSpacing(8)
        layout.addWidget(_make_separator())

        # 쿠키 브라우저
        layout.addSpacing(12)
        lbl_cookie = QLabel("브라우저 쿠키")
        lbl_cookie.setObjectName("prefLabel")
        layout.addWidget(lbl_cookie)
        layout.addSpacing(8)

        lbl_cookie_desc = QLabel(
            "브라우저의 쿠키를 사용하여 연령 제한 콘텐츠 또는\n"
            "프리미엄 콘텐츠에 접근할 수 있습니다."
        )
        lbl_cookie_desc.setObjectName("prefDesc")
        lbl_cookie_desc.setWordWrap(True)
        layout.addWidget(lbl_cookie_desc)
        layout.addSpacing(8)

        self.combo_browser = QComboBox()
        self.combo_browser.setObjectName("prefCombo")
        self.combo_browser.addItems(["사용 안 함", "Chrome", "Firefox", "Edge", "Brave"])
        self.combo_browser.setFixedHeight(36)
        layout.addWidget(self.combo_browser)

        layout.addStretch()


# ── Main Preferences Dialog ──────────────────────────────────────

class PreferencesDialog(QDialog):
    """Settings dialog with sidebar navigation."""

    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("환경설정")
        self.setObjectName("prefDialog")
        self.setMinimumSize(680, 480)
        self.resize(720, 520)

        self._settings = SettingsManager()
        self._setup_ui()
        self._load_settings()
        self._connect_settings_signals()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange and not self.isActiveWindow():
            # 모달 다이얼로그(파일 탐색 등)가 열려있으면 닫지 않음
            if not QApplication.activeModalWidget():
                self.close()
        super().changeEvent(event)

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Left sidebar ────────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("prefSidebar")
        sidebar.setFixedWidth(180)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 12, 0, 12)
        sidebar_layout.setSpacing(2)

        self._sidebar_items = []
        menu_entries = [
            ("🔧", "일반"),
            ("⚙", "고급 설정"),
            ("🌐", "연결"),
            ("🔔", "알림"),
            ("🔑", "승인"),
        ]

        for icon, label in menu_entries:
            item = SidebarItem(icon, label)
            item.clicked.connect(lambda idx=len(self._sidebar_items): self._select_page(idx))
            sidebar_layout.addWidget(item)
            self._sidebar_items.append(item)

        sidebar_layout.addStretch()

        # 라이센스 (bottom)
        self._license_item = SidebarItem("✨", "라이센스")
        self._license_item.clicked.connect(
            lambda: self._select_page(len(self._sidebar_items))
        )
        sidebar_layout.addWidget(self._license_item)

        main_layout.addWidget(sidebar)

        # ── Right content area ──────────────────────────
        right = QWidget()
        right.setObjectName("prefRight")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Close button row
        close_row = QHBoxLayout()
        close_row.setContentsMargins(0, 8, 8, 0)
        close_row.addStretch()
        btn_close = QPushButton("✕")
        btn_close.setObjectName("prefCloseButton")
        btn_close.setFixedSize(32, 32)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.close)
        close_row.addWidget(btn_close)
        right_layout.addLayout(close_row)

        # Stacked pages
        self.stack = QStackedWidget()
        self.stack.setObjectName("prefStack")

        self.page_general = GeneralPage()
        self.page_advanced = AdvancedPage()
        self.page_connection = ConnectionPage()
        self.page_notification = NotificationPage()
        self.page_authorization = AuthorizationPage()
        self.page_license = self._build_license_page()

        self.stack.addWidget(self.page_general)
        self.stack.addWidget(self.page_advanced)
        self.stack.addWidget(self.page_connection)
        self.stack.addWidget(self.page_notification)
        self.stack.addWidget(self.page_authorization)
        self.stack.addWidget(self.page_license)

        right_layout.addWidget(self.stack, stretch=1)

        main_layout.addWidget(right, stretch=1)

        # Select first page
        self._select_page(0)

    def _build_license_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("prefPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(0)

        title = QLabel("라이센스")
        title.setObjectName("prefPageTitle")
        layout.addWidget(title)
        layout.addWidget(_make_separator())

        layout.addSpacing(16)
        lbl_status = QLabel("현재 라이센스: 무료 버전")
        lbl_status.setObjectName("prefLabel")
        layout.addWidget(lbl_status)

        layout.addSpacing(12)
        lbl_desc = QLabel(
            "프리미엄 라이센스를 활성화하면 동시 다운로드 제한 해제,\n"
            "재생목록 전체 다운로드 등의 기능을 사용할 수 있습니다."
        )
        lbl_desc.setObjectName("prefDesc")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        layout.addSpacing(16)

        key_row = QHBoxLayout()
        key_row.setContentsMargins(0, 0, 0, 0)
        key_row.setSpacing(8)

        self.edit_license_key = QLineEdit()
        self.edit_license_key.setObjectName("prefLineEdit")
        self.edit_license_key.setPlaceholderText("라이센스 키 입력")
        self.edit_license_key.setFixedHeight(36)
        key_row.addWidget(self.edit_license_key, stretch=1)

        btn_activate = QPushButton("활성화")
        btn_activate.setObjectName("prefActionButton")
        btn_activate.setFixedHeight(36)
        btn_activate.setCursor(Qt.CursorShape.PointingHandCursor)
        key_row.addWidget(btn_activate)

        layout.addLayout(key_row)

        layout.addStretch()
        return page

    def _select_page(self, index: int):
        # All sidebar items (top menu + license)
        all_items = self._sidebar_items + [self._license_item]
        for i, item in enumerate(all_items):
            item.set_selected(i == index)

        # License page is after all top items
        if index < len(self._sidebar_items):
            self.stack.setCurrentIndex(index)
        else:
            self.stack.setCurrentIndex(self.stack.count() - 1)

    # ── Settings persistence ─────────────────────────────

    def _load_settings(self):
        s = self._settings

        # General
        pg = self.page_general
        idx = pg.combo_lang.findText(s.language)
        if idx >= 0:
            pg.combo_lang.setCurrentIndex(idx)
        pg.toggle_background.setChecked(s.run_in_background)
        pg.toggle_autostart.setChecked(s.auto_start)
        pg.toggle_autoupdate.setChecked(s.auto_update)
        pg.toggle_beta.setChecked(s.beta_enabled)

        # Advanced
        pa = self.page_advanced
        pa.spin_concurrent.setValue(s.concurrent_downloads)
        pa.spin_threads.setValue(s.download_threads)
        pa.edit_path.setText(s.default_save_path)
        pa.toggle_filename_numbering.setChecked(s.filename_numbering)

        # Connection
        pc = self.page_connection
        idx = pc.combo_proxy.findText(s.proxy_type)
        if idx >= 0:
            pc.combo_proxy.setCurrentIndex(idx)
        pc.edit_proxy_host.setText(s.proxy_host)
        pc.edit_proxy_port.setText(s.proxy_port)
        pc.spin_speed.setValue(s.speed_limit)

        # Notification
        pn = self.page_notification
        pn.toggle_download_complete.setChecked(s.notify_download_complete)
        pn.toggle_download_error.setChecked(s.notify_download_error)
        pn.toggle_sound.setChecked(s.notify_sound)
        pn.toggle_tray.setChecked(s.notify_tray)

        # Authorization
        pauth = self.page_authorization
        idx = pauth.combo_browser.findText(s.cookie_browser)
        if idx >= 0:
            pauth.combo_browser.setCurrentIndex(idx)

    def _connect_settings_signals(self):
        pg = self.page_general
        pg.combo_lang.currentTextChanged.connect(self._save_general)
        pg.toggle_background.toggled.connect(self._save_general)
        pg.toggle_autostart.toggled.connect(self._save_general_autostart)
        pg.toggle_autoupdate.toggled.connect(self._save_general)
        pg.toggle_beta.toggled.connect(self._save_general)

        pa = self.page_advanced
        pa.spin_concurrent.valueChanged.connect(self._save_advanced)
        pa.spin_threads.valueChanged.connect(self._save_advanced)
        pa.edit_path.textChanged.connect(self._save_advanced)
        pa.toggle_filename_numbering.toggled.connect(self._save_advanced)

        pc = self.page_connection
        pc.combo_proxy.currentTextChanged.connect(self._save_connection)
        pc.edit_proxy_host.textChanged.connect(self._save_connection)
        pc.edit_proxy_port.textChanged.connect(self._save_connection)
        pc.spin_speed.valueChanged.connect(self._save_connection)

        pn = self.page_notification
        pn.toggle_download_complete.toggled.connect(self._save_notification)
        pn.toggle_download_error.toggled.connect(self._save_notification)
        pn.toggle_sound.toggled.connect(self._save_notification)
        pn.toggle_tray.toggled.connect(self._save_notification)

        pauth = self.page_authorization
        pauth.combo_browser.currentTextChanged.connect(self._save_auth)

    def _save_general(self, *_):
        s = self._settings
        pg = self.page_general
        s.language = pg.combo_lang.currentText()
        s.run_in_background = pg.toggle_background.isChecked()
        s.auto_update = pg.toggle_autoupdate.isChecked()
        s.beta_enabled = pg.toggle_beta.isChecked()
        s.sync()
        self.settings_changed.emit()

    def _save_general_autostart(self, checked: bool):
        self._settings.auto_start = checked
        self._apply_autostart(checked)
        self._settings.sync()
        self.settings_changed.emit()

    def _apply_autostart(self, enabled: bool):
        """운영체제별 자동 시작을 등록/해제한다."""
        from app.utils import autostart

        autostart.set_enabled(enabled, self._settings.get_auto_start_path())

    def _save_advanced(self, *_):
        s = self._settings
        pa = self.page_advanced
        s.concurrent_downloads = pa.spin_concurrent.value()
        s.download_threads = pa.spin_threads.value()
        s.default_save_path = pa.edit_path.text()
        s.filename_numbering = pa.toggle_filename_numbering.isChecked()
        s.sync()
        self.settings_changed.emit()

    def _save_connection(self, *_):
        s = self._settings
        pc = self.page_connection
        s.proxy_type = pc.combo_proxy.currentText()
        s.proxy_host = pc.edit_proxy_host.text()
        s.proxy_port = pc.edit_proxy_port.text()
        s.speed_limit = pc.spin_speed.value()
        s.sync()
        self.settings_changed.emit()

    def _save_notification(self, *_):
        s = self._settings
        pn = self.page_notification
        s.notify_download_complete = pn.toggle_download_complete.isChecked()
        s.notify_download_error = pn.toggle_download_error.isChecked()
        s.notify_sound = pn.toggle_sound.isChecked()
        s.notify_tray = pn.toggle_tray.isChecked()
        s.sync()
        self.settings_changed.emit()

    def _save_auth(self, *_):
        s = self._settings
        pauth = self.page_authorization
        s.cookie_browser = pauth.combo_browser.currentText()
        s.sync()
        self.settings_changed.emit()
