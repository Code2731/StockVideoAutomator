from typing import Dict
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QLineEdit, QMenu, QApplication
)
from PySide6.QtCore import Signal, Qt, QEvent, QTimer
from PySide6.QtGui import QAction

from app.utils.i18n import tr


class TabBar(QWidget):
    """Tab bar: 전체 / 동영상 / 오디오 / 재생 목록  +  search filter"""

    tab_changed = Signal(str)
    search_changed = Signal(str)  # emitted when filter text changes
    sort_changed = Signal(str, bool)  # key, ascending

    TABS = ["전체", "동영상", "오디오", "재생 목록"]
    _TAB_I18N = {
        "전체": "tab.all",
        "동영상": "tab.video",
        "오디오": "tab.audio",
        "재생 목록": "tab.playlist",
    }
    _SORT_I18N = {
        "added": "sort.added",
        "name": "sort.name",
        "size": "sort.size",
        "status": "sort.status",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_tab = "전체"
        self._buttons: Dict[str, QPushButton] = {}
        self._search_visible = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(0)
        self.setFixedHeight(50)

        for tab_name in self.TABS:
            btn = QPushButton(tr(self._TAB_I18N.get(tab_name, tab_name)))
            btn.setObjectName("tabButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(50)
            btn.setMinimumWidth(90)
            if tab_name == "전체":
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, name=tab_name: self._on_tab_click(name))
            layout.addWidget(btn)
            self._buttons[tab_name] = btn

        layout.addStretch()

        # Item count label
        self._count = 0
        self.lbl_count = QLabel(tr("tabbar.count", count=0))
        self.lbl_count.setObjectName("countLabel")
        layout.addWidget(self.lbl_count)

        # Search filter toggle button
        self.btn_search = QPushButton("🔍")
        self.btn_search.setObjectName("tabSearchButton")
        self.btn_search.setFixedSize(36, 36)
        self.btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_search.clicked.connect(self._toggle_search)
        layout.addWidget(self.btn_search)

        # Search input field
        self.search_input = QLineEdit()
        self.search_input.setObjectName("tabSearchInput")
        self.search_input.setPlaceholderText(tr("tabbar.search_placeholder"))
        self.search_input.setFixedHeight(32)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setVisible(False)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_input.installEventFilter(self)
        layout.addWidget(self.search_input)

        # Sort button
        self.btn_sort = QPushButton("↕")
        self.btn_sort.setObjectName("tabSortButton")
        self.btn_sort.setFixedSize(36, 36)
        self.btn_sort.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_sort_menu()
        layout.addWidget(self.btn_sort)

    def _on_tab_click(self, name: str):
        self._current_tab = name
        for tab_name, btn in self._buttons.items():
            btn.setChecked(tab_name == name)
        self.tab_changed.emit(name)

    def _toggle_search(self):
        self._search_visible = not self._search_visible
        self.search_input.setVisible(self._search_visible)
        self.lbl_count.setVisible(not self._search_visible)

        if self._search_visible:
            self.search_input.setFocus()
            self.btn_search.setToolTip(tr("tabbar.filter_hide"))
        else:
            self.search_input.clear()
            self.btn_search.setToolTip(tr("tabbar.filter_show"))

    def eventFilter(self, obj, event):
        if obj is self.search_input and event.type() == QEvent.Type.FocusOut:
            # Delay check so the new focus target is resolved
            QTimer.singleShot(0, self._check_close_search)
        return super().eventFilter(obj, event)

    def _check_close_search(self):
        """Close search bar if focus moved outside search-related widgets."""
        if not self._search_visible:
            return
        focused = QApplication.focusWidget()
        # Keep open if focus is still on the input or the toggle button
        if focused is self.search_input or focused is self.btn_search:
            return
        self._close_search()

    def _close_search(self):
        if not self._search_visible:
            return
        self._search_visible = False
        self.search_input.setVisible(False)
        self.lbl_count.setVisible(True)
        self.search_input.clear()
        self.btn_search.setToolTip(tr("tabbar.filter_show"))

    def _on_search_text_changed(self, text: str):
        self.search_changed.emit(text)

    def _build_sort_menu(self):
        self._sort_key = "added"
        self._sort_ascending = True

        menu = QMenu(self)
        menu.setObjectName("downloadTypeMenu")
        sort_options = [
            ("추가순", "added"),
            ("이름순", "name"),
            ("크기순", "size"),
            ("상태순", "status"),
        ]
        self._sort_actions = []
        for label, key in sort_options:
            act = QAction(tr(self._SORT_I18N.get(key, label)), self)
            act.setCheckable(True)
            act.setChecked(key == "added")
            act.triggered.connect(lambda checked, k=key: self._on_sort_selected(k))
            menu.addAction(act)
            self._sort_actions.append((act, key))

        menu.addSeparator()

        self.act_asc = QAction(tr("sort.asc"), self)
        self.act_asc.setCheckable(True)
        self.act_asc.setChecked(True)
        self.act_asc.triggered.connect(lambda: self._on_order_selected(True))
        menu.addAction(self.act_asc)

        self.act_desc = QAction(tr("sort.desc"), self)
        self.act_desc.setCheckable(True)
        self.act_desc.setChecked(False)
        self.act_desc.triggered.connect(lambda: self._on_order_selected(False))
        menu.addAction(self.act_desc)

        self.btn_sort.setMenu(menu)

    def _on_sort_selected(self, key: str):
        self._sort_key = key
        for act, k in self._sort_actions:
            act.setChecked(k == key)
        self.sort_changed.emit(self._sort_key, self._sort_ascending)

    def _on_order_selected(self, ascending: bool):
        self._sort_ascending = ascending
        self.act_asc.setChecked(ascending)
        self.act_desc.setChecked(not ascending)
        self.sort_changed.emit(self._sort_key, self._sort_ascending)

    def set_count(self, count: int):
        self._count = count
        self.lbl_count.setText(tr("tabbar.count", count=count))

    def retranslate(self):
        """언어 변경 시 탭/정렬 텍스트를 갱신한다."""
        for key, btn in self._buttons.items():
            btn.setText(tr(self._TAB_I18N.get(key, key)))
        self.set_count(self._count)
        self.search_input.setPlaceholderText(tr("tabbar.search_placeholder"))
        self.btn_search.setToolTip(
            tr("tabbar.filter_hide") if self._search_visible
            else tr("tabbar.filter_show")
        )
        for act, key in self._sort_actions:
            act.setText(tr(self._SORT_I18N.get(key, key)))
        self.act_asc.setText(tr("sort.asc"))
        self.act_desc.setText(tr("sort.desc"))

    @property
    def current_tab(self) -> str:
        return self._current_tab
