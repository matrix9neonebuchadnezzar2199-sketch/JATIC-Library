"""Checkbox list for 51 download regions."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from jatic_library.constants import TARGETS_CACHE_PATH
from jatic_library.core.targets import Region, Target, load_overrides


class RegionSelector(QWidget):
    """Grouped checkboxes for region selection."""

    selection_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding,
        )
        self._targets = load_overrides(TARGETS_CACHE_PATH)
        self._boxes: dict[str, QCheckBox] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        select_all_btn = QPushButton("全選択")
        select_all_btn.clicked.connect(self.select_all)
        clear_btn = QPushButton("全解除")
        clear_btn.clicked.connect(self.clear_all)
        toolbar.addWidget(select_all_btn)
        toolbar.addWidget(clear_btn)
        toolbar.addStretch()
        outer.addLayout(toolbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        layout = QVBoxLayout(container)

        by_region: dict[Region, list[Target]] = {}
        for target in self._targets:
            by_region.setdefault(target.region, []).append(target)

        for region in Region:
            group = QGroupBox(region.value)
            group_layout = QVBoxLayout(group)
            row = QHBoxLayout()
            region_all = QPushButton("この地方を全選択")
            region_none = QPushButton("この地方を全解除")
            region_targets = by_region.get(region, [])
            region_all.clicked.connect(
                lambda _checked=False, r=region: self._select_region(r, True)
            )
            region_none.clicked.connect(
                lambda _checked=False, r=region: self._select_region(r, False)
            )
            row.addWidget(region_all)
            row.addWidget(region_none)
            row.addStretch()
            group_layout.addLayout(row)

            for target in region_targets:
                box = QCheckBox(target.display_name)
                box.setChecked(True)
                box.stateChanged.connect(lambda _state: self.selection_changed.emit())
                self._boxes[target.code] = box
                group_layout.addWidget(box)
            if region_targets:
                layout.addWidget(group)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll, stretch=1)

    def _select_region(self, region: Region, checked: bool) -> None:
        for target in self._targets:
            if target.region == region:
                self._boxes[target.code].setChecked(checked)
        self.selection_changed.emit()

    def select_all(self) -> None:
        for box in self._boxes.values():
            box.setChecked(True)
        self.selection_changed.emit()

    def clear_all(self) -> None:
        for box in self._boxes.values():
            box.setChecked(False)
        self.selection_changed.emit()

    def selected_codes(self) -> set[str]:
        """Return checked region codes."""
        return {code for code, box in self._boxes.items() if box.isChecked()}

    def set_selected_codes(self, codes: set[str]) -> None:
        """Update checks; empty *codes* means all regions selected."""
        if not codes:
            self.select_all()
            return
        for code, box in self._boxes.items():
            box.setChecked(code in codes)

    def selection_summary(self) -> str:
        """Human-readable selection count."""
        selected = len(self.selected_codes())
        total = len(self._boxes)
        if selected == total:
            return f"全 {total} 地域"
        return f"{selected} / {total} 地域"
