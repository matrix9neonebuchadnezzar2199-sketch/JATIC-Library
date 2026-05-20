"""Library tab with year-month-region tree."""

from __future__ import annotations

import os

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
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
    scan_library,
)
from jatic_library.core.repository import Repository
from jatic_library.settings.config import AppConfig
from jatic_library.ui.widgets.csv_preview import CsvPreviewWidget
from jatic_library.ui.widgets.file_detail_panel import FileDetailPanel

ROLE_NODE_KIND = Qt.ItemDataRole.UserRole
ROLE_FILE_ITEM = Qt.ItemDataRole.UserRole + 1

KIND_YEAR = "year"
KIND_MONTH = "month"
KIND_FILE = "file"


class LibraryTab(QWidget):
    """Browse downloaded publications in a three-level tree."""

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
        refresh_btn = QPushButton("再読込")
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(self._search)
        toolbar.addWidget(refresh_btn)
        left_layout.addLayout(toolbar)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["保管庫"])
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._open_context_menu)
        self._tree.currentItemChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self._tree)

        right_splitter = QSplitter(Qt.Orientation.Vertical)
        self._detail = FileDetailPanel()
        self._preview = CsvPreviewWidget()
        right_splitter.addWidget(self._detail)
        right_splitter.addWidget(self._preview)
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 2)

        splitter.addWidget(left)
        splitter.addWidget(right_splitter)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        root.addWidget(splitter)

    def update_config(self, config: AppConfig) -> None:
        """Replace config reference and refresh the tree."""
        self._config = config
        self.refresh()

    def refresh(self) -> None:
        """Rescan save_root and rebuild the tree."""
        save_root = self._config.download.save_root
        self._tree_data = scan_library(save_root, self._repo)
        self._rebuild_tree()
        self._apply_search_filter(self._search.text())

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
            file_node = QTreeWidgetItem([file_item.display_name])
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
            self._preview.clear()
            return
        kind = current.data(0, ROLE_NODE_KIND)
        if kind != KIND_FILE:
            self._detail.clear()
            self._preview.clear()
            return
        file_item = current.data(0, ROLE_FILE_ITEM)
        if not isinstance(file_item, LibraryFileItem):
            return
        self._detail.show_file(file_item)
        self._preview.load_zip(file_item.file_path)

    def _open_context_menu(self, position: QPoint) -> None:
        item = self._tree.itemAt(position)
        if item is None:
            return
        file_item = item.data(0, ROLE_FILE_ITEM)
        if not isinstance(file_item, LibraryFileItem):
            return

        menu = QMenu(self)
        open_action = QAction("エクスプローラーで開く", self)
        copy_action = QAction("パスをコピー", self)

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
        menu.addAction(open_action)
        menu.addAction(copy_action)
        menu.exec(self._tree.viewport().mapToGlobal(position))
