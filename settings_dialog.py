# -*- coding: utf-8 -*-
"""
Settings dialog for Image Editor Enhanced.
Complies with ECN Anki guidelines (no emojis, dark/light tooltip protection, clean styling).
"""

from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QComboBox,
    QSpinBox, QPushButton, QGroupBox, QFormLayout, Qt, QWidget
)
from aqt.utils import tooltip, restoreGeom, saveGeom
from .utils import get_addon_config, write_addon_config
from .i18n import tr


def is_dark_mode() -> bool:
    try:
        from aqt.theme import theme_manager
        return theme_manager.night_mode
    except Exception:
        pass
    try:
        from aqt import colors
        return mw.pm.night_mode() if hasattr(mw.pm, "night_mode") else False
    except Exception:
        return False


def get_tooltip_qss() -> str:
    dark = is_dark_mode()
    bg = "#0f172a" if dark else "#ffffff"
    text = "#f8fafc" if dark else "#000000"
    border = "#334155" if dark else "#cbd5e1"
    return f"""
    QToolTip, CustomLabel, QLabel[customTooltip="true"] {{
        background-color: {bg};
        color: {text};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 12px;
    }}
    """


class ImageEditorConfigDialog(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent or mw)
        self.setWindowTitle(tr("settings_window_title"))
        self.setMinimumWidth(460)
        self.setStyleSheet(get_tooltip_qss())
        self.config = get_addon_config()
        self.setup_ui()
        restoreGeom(self, "addon_image_editor_config")

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(18, 18, 18, 18)

        # Group: Recadrage & Remplacement
        grp_behavior = QGroupBox(tr("settings_grp_behavior"))
        form_behavior = QFormLayout(grp_behavior)
        form_behavior.setSpacing(10)

        self.chk_replace_all = QCheckBox(tr("settings_chk_replace_all_desc"))
        self.chk_replace_all.setChecked(bool(self.config.get("replace_all", False)))
        form_behavior.addRow(QLabel(tr("settings_replace_label")), self.chk_replace_all)

        self.combo_ratio = QComboBox()
        self.ratio_options = [
            ("free", tr("ratio_free")),
            ("1:1", "1:1 (Carré)"),
            ("4:3", "4:3"),
            ("16:9", "16:9"),
            ("3:2", "3:2"),
        ]
        for key, label in self.ratio_options:
            self.combo_ratio.addItem(label, key)
        cur_ratio = self.config.get("default_ratio", "free")
        idx_ratio = next((i for i, (k, _) in enumerate(self.ratio_options) if k == cur_ratio), 0)
        self.combo_ratio.setCurrentIndex(idx_ratio)
        form_behavior.addRow(QLabel(tr("settings_ratio_label")), self.combo_ratio)

        layout.addWidget(grp_behavior)

        # Group: Image & Qualité
        grp_image = QGroupBox(tr("settings_grp_image"))
        form_image = QFormLayout(grp_image)
        form_image.setSpacing(10)

        self.spin_quality = QSpinBox()
        self.spin_quality.setRange(50, 100)
        self.spin_quality.setSingleStep(5)
        self.spin_quality.setSuffix(" %")
        self.spin_quality.setValue(int(self.config.get("export_quality", 95)))
        form_image.addRow(QLabel(tr("settings_quality_label")), self.spin_quality)

        self.combo_filter = QComboBox()
        self.filter_options = [
            ("none", tr("filter_none")),
            ("invert", tr("filter_invert")),
            ("high_contrast", tr("filter_contrast")),
            ("grayscale", tr("filter_grayscale")),
        ]
        for key, label in self.filter_options:
            self.combo_filter.addItem(label, key)
        cur_filter = self.config.get("default_filter", "none")
        idx_filter = next((i for i, (k, _) in enumerate(self.filter_options) if k == cur_filter), 0)
        self.combo_filter.setCurrentIndex(idx_filter)
        form_image.addRow(QLabel(tr("settings_filter_label")), self.combo_filter)

        layout.addWidget(grp_image)

        # Info raccourci clavier
        lbl_shortcut_info = QLabel(tr("settings_shortcut_info"))
        lbl_shortcut_info.setWordWrap(True)
        lbl_shortcut_info.setStyleSheet("color: #888899; font-size: 11px;")
        layout.addWidget(lbl_shortcut_info)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)

        btn_cancel = QPushButton(tr("btn_cancel_plain"))
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton(tr("btn_save_plain"))
        btn_save.setDefault(True)
        btn_save.clicked.connect(self.save_and_close)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def save_and_close(self):
        self.config["replace_all"] = self.chk_replace_all.isChecked()
        self.config["default_ratio"] = self.combo_ratio.currentData()
        self.config["export_quality"] = self.spin_quality.value()
        self.config["default_filter"] = self.combo_filter.currentData()
        write_addon_config(self.config)
        saveGeom(self, "addon_image_editor_config")
        tooltip(tr("settings_saved"), parent=self.parent())
        self.accept()

    def reject(self):
        saveGeom(self, "addon_image_editor_config")
        super().reject()


def open_settings_dialog():
    diag = ImageEditorConfigDialog()
    diag.exec()
