"""영상별로 사용 가능한 화질/포맷을 선택하는 다이얼로그."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
)

from app.models.video_info import VideoInfo
from app.utils.format_listing import list_formats
from app.utils.helpers import format_file_size
from app.utils.i18n import tr


class FormatDialog(QDialog):
    """VideoInfo.formats를 표로 보여주고 하나를 선택하게 한다."""

    def __init__(self, video_info: VideoInfo, download_type: str = "video",
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.format_title"))
        self.setObjectName("formatDialog")
        self.setMinimumSize(560, 440)
        self._download_type = download_type
        self._options = list_formats(video_info, download_type)
        self._selected_selector = ""
        self._selected_label = ""
        self._setup_ui(video_info)

    def _setup_ui(self, video_info: VideoInfo):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        lbl_title = QLabel(video_info.title or "제목 없음")
        lbl_title.setObjectName("prefPageTitle")
        lbl_title.setWordWrap(True)
        layout.addWidget(lbl_title)

        self.table = QTableWidget(0, 3, self)
        self.table.setObjectName("formatTable")
        self.table.setHorizontalHeaderLabels([
            tr("format.col_quality"),
            tr("format.col_info"),
            tr("format.col_size"),
        ])
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        for opt in self._options:
            row = self.table.rowCount()
            self.table.insertRow(row)
            label = opt.label
            if not opt.selector:
                label = (tr("format.auto") if self._download_type == "video"
                         else tr("format.auto_audio"))
            self.table.setItem(row, 0, QTableWidgetItem(label))
            self.table.setItem(row, 1, QTableWidgetItem(opt.detail))
            size_text = format_file_size(opt.filesize) if opt.filesize else "-"
            self.table.setItem(row, 2, QTableWidgetItem(size_text))

        if self.table.rowCount():
            self.table.selectRow(0)
        layout.addWidget(self.table, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton(tr("action.cancel"))
        btn_cancel.setCursor(self.cursor())
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_ok = QPushButton(tr("action.download"))
        btn_ok.setObjectName("prefActionButton")
        btn_ok.setCursor(self.cursor())
        btn_ok.clicked.connect(self._on_accept)
        btn_row.addWidget(btn_ok)

        layout.addLayout(btn_row)

    def _on_accept(self):
        row = self.table.currentRow()
        if 0 <= row < len(self._options):
            self._selected_selector = self._options[row].selector
            self._selected_label = self._options[row].label
        self.accept()

    def selected_selector(self) -> str:
        return self._selected_selector

    def selected_label(self) -> str:
        return self._selected_label
