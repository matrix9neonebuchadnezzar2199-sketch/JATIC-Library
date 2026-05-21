"""Library tab with year-month-region tree."""

from __future__ import annotations

import os

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from jatic_library.core.library_scanner import (
    LibraryFileItem,
    LibraryMonthItem,
    LibraryYearItem,
    format_library_file_label,
    scan_library,
)
from jatic_library.core.library_storage import format_storage_usage_label
from jatic_library.core.repository import Repository
from jatic_library.settings.config import AppConfig
from jatic_library.ui.widgets.file_detail_panel import FileDetailPanel

ROLE_NODE_KIND = Qt.ItemDataRole.UserRole
ROLE_FILE_ITEM = Qt.ItemDataRole.UserRole + 1

KIND_YEAR = "year"
KIND_MONTH = "month"
KIND_FILE = "file"


class LibraryTab(QWidget):
    """Browse downloaded publications in a three-level tree."""

    redownload_requested = Signal(object)
    delete_requested = Signal(object)
    export_month_requested = Signal(str)
    sort_changed = Signal(str)

    def __init__(
        self,
        config: AppConfig,
        repo: Repository,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._repo = repo
        self._tree_data: list[LibraryYearItem] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        toolbar = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("地域名で検索…")
        self._search.textChanged.connect(self._apply_search_filter)
        self._sort = QComboBox()
        for label, key in (
            ("日付（新しい順）", "date_desc"),
            ("日付（古い順）", "date_asc"),
            ("地域名", "name"),
        ):
            self._sort.addItem(label, key)
        self._sort.currentIndexChanged.connect(self._on_sort_changed)
        refresh_btn = QPushButton("再読込")
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(self._search)
        toolbar.addWidget(self._sort)
        toolbar.addWidget(refresh_btn)
        left_layout.addLayout(toolbar)

        import_hint = QLabel(
            "以前ダウンロードした ZIP があれば、保存先（既定はアプリ直下の data）内に "
            "「YYYY_M」フォルダ（例: 2026_3 ＝データ月）を作成し、その中へ "
            "地域の ZIP を配置してから「再読込」すると保管庫に反映されます。"
            "ダウンロード完了時は ZIP を解凍し、選択地域の CSV を「統合.csv」に結合します。"
        )
        import_hint.setObjectName("sectionHint")
        import_hint.setWordWrap(True)
        left_layout.addWidget(import_hint)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(8, 8, 8, 8)
        self._header_title = QLabel("保管庫")
        self._header_title.setObjectName("libraryTreeHeaderTitle")
        self._header_usage = QLabel("")
        self._header_usage.setObjectName("libraryTreeHeaderUsage")
        self._header_usage.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_row.addWidget(self._header_title)
        header_row.addStretch(1)
        header_row.addWidget(self._header_usage)
        self._tree_header = QWidget()
        self._tree_header.setObjectName("libraryTreeHeader")
        self._tree_header.setLayout(header_row)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._open_context_menu)
        self._tree.currentItemChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self._tree_header)
        left_layout.addWidget(self._tree)

        self._detail = FileDetailPanel()

        splitter.addWidget(left)
        splitter.addWidget(self._detail)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter)

    def update_config(self, config: AppConfig) -> None:
        """Replace config reference and refresh the tree."""
        self._config = config
        self.refresh()

    def showEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        """Refresh storage label when the tab becomes visible."""
        super().showEvent(event)
        self._update_storage_header()

    def refresh(self) -> None:
        """Rescan save_root and rebuild the tree."""
        save_root = self._config.download.save_root
        sort_key = self._config.ui.library_default_sort
        self._tree_data = scan_library(save_root, self._repo, sort=sort_key)
        self._sync_sort_combo(sort_key)
        self._rebuild_tree()
        self._apply_search_filter(self._search.text())
        self._update_storage_header()

    def _update_storage_header(self) -> None:
        """Show library size vs disk capacity in the tree header band."""
        self._header_usage.setText(format_storage_usage_label(self._config.download.save_root))

    def _sync_sort_combo(self, sort_key: str) -> None:
        for index in range(self._sort.count()):
            if self._sort.itemData(index) == sort_key:
                self._sort.blockSignals(True)
                self._sort.setCurrentIndex(index)
                self._sort.blockSignals(False)
                break

    def _on_sort_changed(self) -> None:
        sort_key = self._sort.currentData()
        if not isinstance(sort_key, str):
            return
        self._config.ui.library_default_sort = sort_key
        self.sort_changed.emit(sort_key)
        self.refresh()

    def _rebuild_tree(self) -> None:
        self._tree.clear()
        for year_item in self._tree_data:
            year_node = QTreeWidgetItem([f"{year_item.year}年"])
            year_node.setData(0, ROLE_NODE_KIND, KIND_YEAR)
            year_node.setExpanded(True)
            for month_item in year_item.months:
                month_node = self._make_month_node(month_item)
                year_node.addChild(month_node)
            self._tree.addTopLevelItem(year_node)

    def _make_month_node(self, month: LibraryMonthItem) -> QTreeWidgetItem:
        status_suffix = ""
        if month.publication_status:
            status_suffix = f" [{month.publication_status}]"
        label = f"{month.year}年{month.month}月分 ({month.folder_name}){status_suffix}"
        month_node = QTreeWidgetItem([label])
        month_node.setData(0, ROLE_NODE_KIND, KIND_MONTH)
        month_node.setExpanded(True)
        for file_item in month.files:
            label = format_library_file_label(
                file_item.display_name,
                file_item.file_size,
                file_item.row_count,
            )
            file_node = QTreeWidgetItem([label])
            file_node.setData(0, ROLE_NODE_KIND, KIND_FILE)
            file_node.setData(0, ROLE_FILE_ITEM, file_item)
            month_node.addChild(file_node)
        return month_node

    def _apply_search_filter(self, text: str) -> None:
        needle = text.strip().casefold()

        def month_matches(month: LibraryMonthItem) -> bool:
            if not needle:
                return True
            return any(needle in file_item.display_name.casefold() for file_item in month.files)

        for index in range(self._tree.topLevelItemCount()):
            year_node = self._tree.topLevelItem(index)
            if year_node is None:
                continue
            year_visible = False
            for month_index in range(year_node.childCount()):
                month_node = year_node.child(month_index)
                if month_node is None:
                    continue
                month_item = self._month_from_node(month_node)
                visible = month_matches(month_item) if month_item else True
                month_node.setHidden(not visible)
                for file_index in range(month_node.childCount()):
                    file_node = month_node.child(file_index)
                    if file_node is None:
                        continue
                    file_item = file_node.data(0, ROLE_FILE_ITEM)
                    if isinstance(file_item, LibraryFileItem):
                        file_visible = not needle or needle in file_item.display_name.casefold()
                        file_node.setHidden(not file_visible or not visible)
                if visible and not month_node.isHidden():
                    year_visible = True
            year_node.setHidden(not year_visible and bool(needle))

    def _month_from_node(self, month_node: QTreeWidgetItem) -> LibraryMonthItem | None:
        label = month_node.text(0)
        for year_item in self._tree_data:
            for month_item in year_item.months:
                if month_item.folder_name in label:
                    return month_item
        return None

    def _on_selection_changed(
        self,
        current: QTreeWidgetItem | None,
        _previous: QTreeWidgetItem | None,
    ) -> None:
        if current is None:
            self._detail.clear()
            return
        kind = current.data(0, ROLE_NODE_KIND)
        if kind != KIND_FILE:
            self._detail.clear()
            return
        file_item = current.data(0, ROLE_FILE_ITEM)
        if not isinstance(file_item, LibraryFileItem):
            return
        scope_key = self._file_scope_key(file_item)
        tag_names = [row.name for row in self._repo.list_tags_for("file", scope_key)]
        self._detail.show_file(file_item, tags=tag_names)

    @staticmethod
    def _file_scope_key(file_item: LibraryFileItem) -> str:
        code = file_item.target_code or file_item.file_name
        return f"{file_item.publish_ym}/{code}"

    def _open_context_menu(self, position: QPoint) -> None:
        item = self._tree.itemAt(position)
        if item is None:
            return
        kind = item.data(0, ROLE_NODE_KIND)
        if kind == KIND_MONTH:
            self._month_context_menu(item, position)
            return
        file_item = item.data(0, ROLE_FILE_ITEM)
        if not isinstance(file_item, LibraryFileItem):
            return

        menu = QMenu(self)
        open_action = QAction("エクスプローラーで開く", self)
        copy_action = QAction("パスをコピー", self)
        redownload_action = QAction("再ダウンロード", self)
        delete_action = QAction("削除", self)
        tag_action = QAction("タグを管理…", self)
        is_merged = file_item.target_code == "merged"

        def open_in_explorer() -> None:
            folder = file_item.file_path.parent
            try:
                os.startfile(folder)  # noqa: S606 — Windows shell
            except OSError as exc:
                QMessageBox.warning(self, "保管庫", f"フォルダを開けませんでした:\n{exc}")

        def copy_path() -> None:
            clipboard = QApplication.clipboard()
            if clipboard is not None:
                clipboard.setText(str(file_item.file_path))

        open_action.triggered.connect(open_in_explorer)
        copy_action.triggered.connect(copy_path)
        if not is_merged:
            redownload_action.triggered.connect(lambda: self.redownload_requested.emit(file_item))
        delete_action.triggered.connect(lambda: self._confirm_delete(file_item))
        tag_action.triggered.connect(lambda: self._manage_tags(file_item))
        menu.addAction(open_action)
        menu.addAction(copy_action)
        menu.addSeparator()
        if not is_merged:
            menu.addAction(redownload_action)
        menu.addAction(delete_action)
        menu.addAction(tag_action)
        menu.exec(self._tree.viewport().mapToGlobal(position))

    def _month_context_menu(self, item: QTreeWidgetItem, position: QPoint) -> None:
        month_item = self._month_from_node(item)
        if month_item is None:
            return
        menu = QMenu(self)
        export_zip = QAction("月次 ZIP バンドルをエクスポート…", self)
        export_csv = QAction("統合 CSV をエクスポート…", self)

        def export_bundle() -> None:
            self.export_month_requested.emit(month_item.folder_name)

        export_zip.triggered.connect(export_bundle)
        export_csv.triggered.connect(export_bundle)
        menu.addAction(export_zip)
        menu.addAction(export_csv)
        menu.exec(self._tree.viewport().mapToGlobal(position))

    def _confirm_delete(self, file_item: LibraryFileItem) -> None:
        answer = QMessageBox.question(
            self,
            "削除確認",
            f"{file_item.display_name} を削除しますか？\n{file_item.file_path}",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(file_item)

    def _manage_tags(self, file_item: LibraryFileItem) -> None:
        scope_key = self._file_scope_key(file_item)
        existing = {row.id: row.name for row in self._repo.list_tags_for("file", scope_key)}
        all_tags = self._repo.list_tags()
        choices = [f"{row.name} ({row.id})" for row in all_tags]
        if not choices:
            name, ok = QInputDialog.getText(self, "タグ", "新しいタグ名:")
            if ok and name.strip():
                tag_id = self._repo.create_tag(name.strip())
                self._repo.assign_tag(tag_id, "file", scope_key)
                self._on_selection_changed(self._tree.currentItem(), None)
            return

        selected, ok = QInputDialog.getItem(
            self,
            "タグ",
            "付与するタグを選択（キャンセルで新規作成）:",
            choices,
            editable=False,
        )
        if ok and selected:
            tag_id = int(selected.rsplit("(", 1)[1].rstrip(")"))
            if tag_id in existing:
                self._repo.unassign_tag(tag_id, "file", scope_key)
            else:
                self._repo.assign_tag(tag_id, "file", scope_key)
            self._on_selection_changed(self._tree.currentItem(), None)
            return

        name, ok_new = QInputDialog.getText(self, "タグ", "新しいタグ名:")
        if ok_new and name.strip():
            tag_id = self._repo.create_tag(name.strip())
            self._repo.assign_tag(tag_id, "file", scope_key)
            self._on_selection_changed(self._tree.currentItem(), None)
