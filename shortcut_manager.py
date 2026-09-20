# -*- coding: utf-8 -*-
"""
Gestionnaire et Visualiseur de Raccourcis Clavier pour Anki (Fork ameliore).
Interface inspiree d'Adobe After Effects avec clavier virtuel interactif,
synchronisation bidirectionnelle, detection avancee des raccourcis d'autres addons (EDN, Diff, etc.),
detection native de la disposition Windows, filtres interactifs, deselection et edition complete.
"""

import os
import json
import copy
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo, showWarning, saveGeom, restoreGeom

try:
    from . import custom_shortcuts
    from . import cs_functions as functions
    from .i18n import I18n, get_anki_language
    from .virtual_keyboard import VirtualKeyboardWidget, detect_windows_keyboard_layout
    from .addon_scanner import AddonScanner
except (ImportError, ValueError):
    import custom_shortcuts
    import cs_functions as functions
    from i18n import I18n, get_anki_language
    from virtual_keyboard import VirtualKeyboardWidget, detect_windows_keyboard_layout
    from addon_scanner import AddonScanner

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "default_config.json")
USER_CONFIG_PATH = None

DISABLED_SHORTCUTS = [
    "editor insert latex",
    "editor insert latex equation",
    "editor insert latex math environment",
    "editor insert mathjax inline",
    "editor insert mathjax block",
    "editor insert mathjax chemistry"
]

MODIFIER_COMBINATIONS = [
    ("mod_none", ""),
    ("mod_ctrl", "Ctrl"),
    ("mod_alt", "Alt"),
    ("mod_shift", "Shift"),
    ("mod_ctrl_shift", "Ctrl+Shift"),
    ("mod_ctrl_alt", "Ctrl+Alt"),
    ("mod_alt_shift", "Alt+Shift"),
    ("mod_ctrl_alt_shift", "Ctrl+Alt+Shift")
]

class KeySequenceCaptureDialog(QDialog):
    """Dialogue modal de capture de raccourci clavier au vol."""
    def __init__(self, parent, action_label, current_scut, i18n):
        super().__init__(parent)
        self.i18n = i18n
        self.captured_shortcut = current_scut or ""
        self.setWindowTitle(self.i18n.t("dialog_edit_title", "Modifier le raccourci"))
        self.setFixedSize(450, 220)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        title_lbl = QLabel(f"<b>{action_label}</b>")
        title_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        title_lbl.setStyleSheet("font-size: 13px;")
        layout.addWidget(title_lbl)

        instr_lbl = QLabel(self.i18n.t("dialog_edit_instruction", "Appuyez sur la combinaison de touches souhaitée :"))
        instr_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(instr_lbl)

        self.display_lbl = QLabel(self.captured_shortcut if self.captured_shortcut and self.captured_shortcut != "<nop>" else "-")
        self.display_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display_lbl.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 12px;
                border: 2px dashed #3182ce;
                border-radius: 6px;
                background-color: rgba(49, 130, 206, 0.08);
            }
        """)
        self.display_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.display_lbl)

        btn_box = QHBoxLayout()
        self.btn_clear = QPushButton(self.i18n.t("dialog_edit_clear", "Effacer (Désactiver)"))
        self.btn_clear.clicked.connect(self.on_clear)
        self.btn_ok = QPushButton(self.i18n.t("btn_ok", "OK"))
        self.btn_ok.setDefault(True)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = QPushButton(self.i18n.t("btn_cancel", "Annuler"))
        self.btn_cancel.clicked.connect(self.reject)

        btn_box.addWidget(self.btn_clear)
        btn_box.addStretch()
        btn_box.addWidget(self.btn_cancel)
        btn_box.addWidget(self.btn_ok)
        layout.addLayout(btn_box)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return super().keyPressEvent(event)
        if key == Qt.Key.Key_Escape:
            self.reject()
            return

        mods = event.modifiers()
        parts = []
        if mods & Qt.KeyboardModifier.ControlModifier:
            parts.append("Ctrl")
        if mods & Qt.KeyboardModifier.AltModifier:
            parts.append("Alt")
        if mods & Qt.KeyboardModifier.ShiftModifier:
            parts.append("Shift")
        if mods & Qt.KeyboardModifier.MetaModifier:
            parts.append("Win")

        key_name = ""
        if Qt.Key.Key_F1 <= key <= Qt.Key.Key_F12:
            key_name = f"F{key - Qt.Key.Key_F1 + 1}"
        elif key == Qt.Key.Key_Return:
            key_name = "Return"
        elif key == Qt.Key.Key_Enter:
            key_name = "Enter"
        elif key == Qt.Key.Key_Space:
            key_name = "Space"
        elif key == Qt.Key.Key_Tab:
            key_name = "Tab"
        elif key == Qt.Key.Key_Backspace:
            key_name = "Backspace"
        elif key == Qt.Key.Key_Delete:
            key_name = "Del"
        elif key == Qt.Key.Key_Insert:
            key_name = "Ins"
        elif key == Qt.Key.Key_Home:
            key_name = "Home"
        elif key == Qt.Key.Key_End:
            key_name = "End"
        elif key == Qt.Key.Key_PageUp:
            key_name = "PgUp"
        elif key == Qt.Key.Key_PageDown:
            key_name = "PgDn"
        elif key == Qt.Key.Key_Up:
            key_name = "Up"
        elif key == Qt.Key.Key_Down:
            key_name = "Down"
        elif key == Qt.Key.Key_Left:
            key_name = "Left"
        elif key == Qt.Key.Key_Right:
            key_name = "Right"
        else:
            text = event.text().upper()
            if text and text.isalnum():
                key_name = text
            else:
                key_name = QKeySequence(key).toString()

        if key_name:
            full_seq = "+".join(parts + [key_name])
            self.captured_shortcut = full_seq
            self.display_lbl.setText(full_seq)

    def on_clear(self):
        self.captured_shortcut = "<nop>"
        self.display_lbl.setText("<nop>")


class ShortcutManagerDialog(QDialog):
    def __init__(self, parent=None, initial_context=None):
        super().__init__(parent)
        self.parent = parent
        self.initial_context = initial_context
        
        # Configuration
        try:
            self.config = mw.addonManager.getConfig(__name__) if (mw and hasattr(mw, "addonManager") and mw.addonManager) else None
        except Exception:
            self.config = None
            
        if not self.config:
            try:
                _cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
                with open(_cfg_path, "r", encoding="utf-8") as _f:
                    self.config = json.load(_f)
            except Exception:
                self.config = {}
        
        # Internationalisation
        cfg_lang = self.config.get("interface_language", "auto")
        self.i18n = I18n(cfg_lang)
        self.current_lang = self.i18n.lang
        
        # Scanner d'addons tiers
        self.addon_scanner = AddonScanner(current_addon_id="1762336370")
        self.addon_shortcuts = []
        
        # Structure interne des raccourcis en cours d'edition
        self.shortcuts_data = {}
        
        self.selected_key_id = None
        self.selected_key_label = ""
        self.show_anki = True
        self.show_addons = True
        
        self.setWindowTitle(self.i18n.t("window_title"))
        self.setMinimumSize(1100, 740)
        
        try:
            restoreGeom(self, "shortcutManagerVisual")
        except Exception:
            pass
        
        self.setup_ui()
        self.load_all_shortcuts()
        self.apply_initial_context()
        self.refresh_display()
        
        # Theme change listener
        try:
            from aqt.theme import theme_manager
            theme_manager.night_mode_changed.connect(self.on_theme_changed)
        except Exception:
            pass

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # -----------------------------------------------------------------
        # 1. Barre superieure : Disposition clavier + Portees en checkboxes
        # -----------------------------------------------------------------
        top_bar = QHBoxLayout()
        top_bar.setSpacing(16)

        # Disposition Clavier (Auto Windows, AZERTY, QWERTY, QWERTZ, Dvorak, Colemak)
        layout_box = QHBoxLayout()
        self.layout_label = QLabel(self.i18n.t("layout_label"))
        self.layout_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.layout_combo = QComboBox()

        detected_layout = detect_windows_keyboard_layout()
        auto_label = f"{self.i18n.t('layout_auto', 'Disposition Windows')} ({detected_layout})"
        self.layout_combo.addItem(auto_label, "AUTO")
        self.layout_combo.addItem(self.i18n.t("layout_azerty"), "AZERTY")
        self.layout_combo.addItem(self.i18n.t("layout_qwerty"), "QWERTY")
        self.layout_combo.addItem(self.i18n.t("layout_qwertz"), "QWERTZ")
        self.layout_combo.addItem(self.i18n.t("layout_dvorak"), "DVORAK")
        self.layout_combo.addItem(self.i18n.t("layout_colemak"), "COLEMAK")

        # Selection native par defaut sur AUTO
        self.layout_combo.setCurrentIndex(0)
        self.layout_combo.currentIndexChanged.connect(self.on_layout_changed)
        layout_box.addWidget(self.layout_label)
        layout_box.addWidget(self.layout_combo)
        top_bar.addLayout(layout_box)

        top_bar.addStretch()

        # Portees : checkboxes horizontales exclusives (comportement radio)
        scope_bar = QHBoxLayout()
        scope_bar.setSpacing(2)

        SCOPE_DEFS = [
            ("all",      self.i18n.t("scope_all",      "Tout")),
            ("main",     self.i18n.t("scope_main",     "Menu")),
            ("editor",   self.i18n.t("scope_editor",   "Editeur")),
            ("reviewer", self.i18n.t("scope_reviewer", "Reviseur")),
            ("browser",  self.i18n.t("scope_browser",  "Navigateur")),
            ("toolbar",  self.i18n.t("scope_toolbar",  "Barre")),
            ("addons",   self.i18n.t("scope_addons",   "Extensions")),
        ]

        self._scope_buttons = {}
        _btn_style = """
            QPushButton {
                font-size: 11px;
                padding: 3px 9px;
                border: 1px solid #cbd5e0;
                border-radius: 3px;
                background: transparent;
            }
            QPushButton:checked {
                background-color: #3182ce;
                color: #ffffff;
                border-color: #2b6cb0;
            }
            QPushButton:hover:!checked {
                background-color: #e2e8f0;
            }
        """
        for scope_id, scope_label in SCOPE_DEFS:
            btn = QPushButton(scope_label)
            btn.setCheckable(True)
            btn.setStyleSheet(_btn_style)
            btn.setProperty("scope_id", scope_id)
            btn.clicked.connect(self._on_scope_button_clicked)
            self._scope_buttons[scope_id] = btn
            scope_bar.addWidget(btn)

        # Selection initiale : "all"
        self._current_scope = "all"
        self._scope_buttons["all"].setChecked(True)

        top_bar.addLayout(scope_bar)
        main_layout.addLayout(top_bar)


        # -----------------------------------------------------------------
        # 2. Zone centrale : Clavier Virtuel Interactif
        # -----------------------------------------------------------------
        self.virtual_keyboard = VirtualKeyboardWidget(self)
        self.virtual_keyboard.set_layout_mode(self.layout_combo.currentData())
        self.virtual_keyboard.key_clicked.connect(self.on_virtual_key_clicked)
        self.virtual_keyboard.key_hovered.connect(self.on_virtual_key_hovered)
        self.virtual_keyboard.modifiers_changed.connect(self.on_virtual_modifiers_changed)
        main_layout.addWidget(self.virtual_keyboard, stretch=2)

        # Barre de filtres interactifs et legende visuelle
        mod_bar = QHBoxLayout()
        mod_bar.setContentsMargins(6, 0, 6, 0)
        mod_bar.setSpacing(18)

        # Filtres interactifs decocables (remplacent la legende statique et les boutons doublons)
        self.chk_filter_anki = QCheckBox(self.i18n.t("filter_anki", "Raccourcis Anki actifs"))
        self.chk_filter_anki.setChecked(True)
        self.chk_filter_anki.setStyleSheet("""
            QCheckBox { font-size: 11px; font-weight: bold; color: #3182ce; }
            QCheckBox::indicator { width: 13px; height: 13px; border-radius: 2px; }
            QCheckBox::indicator:checked { background-color: #3182ce; border: 1px solid #2b6cb0; }
            QCheckBox::indicator:unchecked { background-color: transparent; border: 1px solid #a0aec0; }
        """)
        self.chk_filter_anki.stateChanged.connect(self.on_filter_changed)

        self.chk_filter_addons = QCheckBox(self.i18n.t("filter_addons", "Raccourcis d'autres extensions"))
        self.chk_filter_addons.setChecked(True)
        self.chk_filter_addons.setStyleSheet("""
            QCheckBox { font-size: 11px; font-weight: bold; color: #2b6cb0; }
            QCheckBox::indicator { width: 13px; height: 13px; border-radius: 2px; }
            QCheckBox::indicator:checked { background-color: #2b6cb0; border: 1px solid #1a4971; }
            QCheckBox::indicator:unchecked { background-color: transparent; border: 1px solid #a0aec0; }
        """)
        self.chk_filter_addons.stateChanged.connect(self.on_filter_changed)

        leg_mod_box = self._create_legend_badge(QColor("#805ad5"), self.i18n.t("legend_modifier"))

        mod_bar.addWidget(self.chk_filter_anki)
        mod_bar.addWidget(self.chk_filter_addons)
        mod_bar.addWidget(leg_mod_box)

        mod_bar.addStretch()

        # Etiquette de statut/survol
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #718096; font-style: italic;")
        self.status_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        mod_bar.addWidget(self.status_label)

        main_layout.addLayout(mod_bar)

        # -----------------------------------------------------------------
        # 3. Zone inferieure (Splitter) : Liste des commandes & Inspecteur
        # -----------------------------------------------------------------
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panneau Gauche : Recherche et Tableau des commandes
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        # Champ de recherche et bouton de modification rapide
        search_box = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.i18n.t("search_placeholder"))
        self.search_input.textChanged.connect(self.filter_commands_table)
        self.search_input.setClearButtonEnabled(True)
        search_box.addWidget(self.search_input)

        self.btn_edit_cmd = QPushButton(self.i18n.t("btn_edit_shortcut", "Modifier..."))
        self.btn_edit_cmd.setToolTip("Double-cliquez sur une ligne ou cliquez ici pour modifier son raccourci")
        self.btn_edit_cmd.clicked.connect(lambda: self.on_edit_shortcut_dialog())
        search_box.addWidget(self.btn_edit_cmd)

        left_layout.addLayout(search_box)

        # Tableau des commandes
        self.commands_table = QTableWidget()
        self.commands_table.setColumnCount(3)
        self.commands_table.setHorizontalHeaderLabels([
            self.i18n.t("col_action"),
            self.i18n.t("col_shortcut"),
            self.i18n.t("col_category")
        ])
        self.commands_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.commands_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.commands_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.commands_table.verticalHeader().setVisible(False)
        self.commands_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.commands_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.commands_table.itemSelectionChanged.connect(self.on_command_table_selected)
        self.commands_table.itemDoubleClicked.connect(lambda: self.on_edit_shortcut_dialog())
        self.commands_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.commands_table.customContextMenuRequested.connect(self.on_table_context_menu)
        left_layout.addWidget(self.commands_table)

        splitter.addWidget(left_panel)

        # Panneau Droit : Inspecteur de touche ("Touche : [X]" ou "Aucune touche sélectionnée")
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 0, 0, 0)
        right_layout.setSpacing(6)

        self.inspector_header = QLabel(self.i18n.t("no_key_selected", "Aucune touche selectionnee"))
        self.inspector_header.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.inspector_header.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        right_layout.addWidget(self.inspector_header)


        # Tableau des 8 combinaisons de modificateurs pour la touche selectionnee
        self.inspector_table = QTableWidget()
        self.inspector_table.setColumnCount(2)
        self.inspector_table.setHorizontalHeaderLabels([
            self.i18n.t("col_modifier"),
            self.i18n.t("col_command")
        ])
        self.inspector_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.inspector_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.inspector_table.verticalHeader().setVisible(False)
        self.inspector_table.setRowCount(len(MODIFIER_COMBINATIONS))
        self.inspector_table.itemDoubleClicked.connect(self.on_inspector_row_double_clicked)
        self.inspector_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.inspector_table.customContextMenuRequested.connect(self.on_inspector_context_menu)
        right_layout.addWidget(self.inspector_table)

        # Boutons rapides d'action pour l'inspecteur
        inspector_btn_box = QHBoxLayout()
        self.btn_clear_key = QPushButton(self.i18n.t("btn_clear_shortcut"))
        self.btn_clear_key.clicked.connect(self.on_clear_selected_key_combination)
        self.btn_clear_key.setEnabled(False)

        self.btn_reset_key = QPushButton(self.i18n.t("btn_reset_shortcut"))
        self.btn_reset_key.clicked.connect(self.on_reset_selected_key_combination)
        self.btn_reset_key.setEnabled(False)

        inspector_btn_box.addWidget(self.btn_clear_key)
        inspector_btn_box.addWidget(self.btn_reset_key)
        right_layout.addLayout(inspector_btn_box)

        splitter.addWidget(right_panel)
        splitter.setSizes([620, 440])
        main_layout.addWidget(splitter, stretch=3)

        # -----------------------------------------------------------------
        # 4. Barre inferieure : Chemin config, Rétablissement, Annuler, Appliquer, OK
        # -----------------------------------------------------------------
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        self.btn_browse_path = QPushButton(self.i18n.t("btn_browse"))
        self.btn_browse_path.clicked.connect(self.select_config_path)
        self.path_info_label = QLabel(USER_CONFIG_PATH or "")
        self.path_info_label.setStyleSheet("color: #718096; font-size: 11px;")
        self.path_info_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bottom_bar.addWidget(self.btn_browse_path)
        bottom_bar.addWidget(self.path_info_label)

        bottom_bar.addStretch()

        self.btn_restore_all = QPushButton(self.i18n.t("btn_restore_all"))
        self.btn_restore_all.clicked.connect(self.restore_all_defaults)
        bottom_bar.addWidget(self.btn_restore_all)

        self.btn_apply = QPushButton(self.i18n.t("btn_apply"))
        self.btn_apply.clicked.connect(self.apply_changes)
        bottom_bar.addWidget(self.btn_apply)

        self.btn_cancel = QPushButton(self.i18n.t("btn_cancel"))
        self.btn_cancel.clicked.connect(self.reject)
        bottom_bar.addWidget(self.btn_cancel)

        self.btn_ok = QPushButton(self.i18n.t("btn_ok"))
        self.btn_ok.setDefault(True)
        self.btn_ok.clicked.connect(self.accept_changes)
        bottom_bar.addWidget(self.btn_ok)

        main_layout.addLayout(bottom_bar)

    def _create_legend_badge(self, color, text):
        badge = QWidget()
        l = QHBoxLayout(badge)
        l.setContentsMargins(0, 0, 8, 0)
        l.setSpacing(6)

        color_sq = QLabel()
        color_sq.setFixedSize(12, 12)
        color_sq.setStyleSheet(f"background-color: {color.name()}; border-radius: 2px;")

        txt_lbl = QLabel(text)
        txt_lbl.setStyleSheet("font-size: 11px;")
        txt_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        l.addWidget(color_sq)
        l.addWidget(txt_lbl)
        return badge

    def on_deselect_key(self):
        """Désélectionne la touche courante."""
        self.selected_key_id = None
        self.selected_key_label = ""
        self.virtual_keyboard.deselect_key()
        self.inspector_header.setText(self.i18n.t("no_key_selected"))
        self.btn_clear_key.setEnabled(False)
        self.btn_reset_key.setEnabled(False)
        self.update_key_inspector()

    def on_filter_changed(self):
        """Met a jour les filtres de source pour le tableau et le clavier."""
        show_anki = self.chk_filter_anki.isChecked()
        show_addons = self.chk_filter_addons.isChecked()
        self.virtual_keyboard.set_source_filters(show_anki, show_addons)
        self.refresh_display()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.selected_key_id is not None:
                self.on_deselect_key()
                return
        super().keyPressEvent(event)

    def apply_initial_context(self):
        """Selectionne automatiquement le contexte correspondant a la page active d'Anki."""
        ctx = self.initial_context
        if not ctx:
            try:
                if hasattr(mw, "state") and mw.state == "review":
                    ctx = "reviewer"
                elif QApplication.activeWindow() and "browser" in QApplication.activeWindow().__class__.__name__.lower():
                    ctx = "browser"
                elif QApplication.activeWindow() and "editor" in QApplication.activeWindow().__class__.__name__.lower():
                    ctx = "editor"
                else:
                    ctx = "all"
            except Exception:
                ctx = "all"

        self._set_scope(ctx)


    def load_all_shortcuts(self):
        """Charge l'ensemble des raccourcis Anki et ceux des autres addons avec persistance."""
        self.shortcuts_data.clear()

        default_config = {}
        if os.path.exists(DEFAULT_CONFIG_PATH):
            try:
                with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
                    default_config = json.load(f)
            except Exception:
                pass

        # 1. Raccourcis Anki natifs
        for k, v in self.config.items():
            if isinstance(v, (dict, list)) or k.startswith("Ω") or k in ("interface_language", "addon_shortcuts_overrides"):
                continue
            
            scope = "toolbar"
            if k.startswith("main "):
                scope = "main"
            elif k.startswith("editor "):
                scope = "editor"
            elif k.startswith("reviewer "):
                scope = "reviewer"
            elif k.startswith("window_browser "):
                scope = "browser"

            label = self.i18n.get_action_name(k)
            def_val = default_config.get(k, "")
            is_dis = (k in DISABLED_SHORTCUTS)

            self.shortcuts_data[k] = {
                "shortcut": v,
                "label": label,
                "source": "anki",
                "scope": scope,
                "default_shortcut": def_val,
                "is_disabled": is_dis,
                "original_key": k
            }

        # 2. Raccourcis des autres extensions (EDN, Diff, config, live Qt)
        try:
            overrides = self.config.get("addon_shortcuts_overrides", {})
            self.addon_shortcuts = self.addon_scanner.get_all_addon_shortcuts()

            for idx, item in enumerate(self.addon_shortcuts):
                k = f"addon_{item.addon_id}_{idx}"
                name_key = f"{item.addon_name}_{item.action_name}"
                current_scut = overrides.get(k, overrides.get(name_key, item.shortcut))

                self.shortcuts_data[k] = {
                    "shortcut": current_scut,
                    "label": f"[{item.addon_name}] {item.action_name}",
                    "source": "addon",
                    "scope": item.scope,
                    "default_shortcut": item.shortcut,
                    "is_disabled": False,
                    "addon_id": item.addon_id,
                    "addon_name": item.addon_name,
                    "action_name": item.action_name,
                    "qaction": item.qaction,
                    "qshortcut": item.qshortcut,
                    "config_key": item.config_key,
                    "edn_info": item.edn_info,
                    "original_key": k
                }
        except Exception:
            pass

    def refresh_display(self):
        """Met a jour le clavier virtuel, le tableau des commandes et l'inspecteur."""
        current_scope = self._current_scope
        show_anki = self.chk_filter_anki.isChecked()
        show_addons = self.chk_filter_addons.isChecked()
        
        kb_data = {}
        for action_id, item in self.shortcuts_data.items():
            if item["source"] == "anki" and not show_anki:
                continue
            if item["source"] == "addon" and not show_addons:
                continue
            if current_scope != "all" and item["scope"] != current_scope:
                continue
            kb_data[action_id] = {
                "shortcut": item["shortcut"],
                "label": item["label"],
                "source": item["source"],
                "scope": item["scope"]
            }

        self.virtual_keyboard.set_shortcut_data(kb_data)
        self.populate_commands_table()
        self.update_key_inspector()

    def populate_commands_table(self):
        """Remplit le tableau des commandes selon la portee, les filtres de sources et la recherche."""
        current_scope = self._current_scope
        search_query = self.search_input.text().lower()
        show_anki = getattr(self, "chk_filter_anki", None) is None or self.chk_filter_anki.isChecked()
        show_addons = getattr(self, "chk_filter_addons", None) is None or self.chk_filter_addons.isChecked()

        self.commands_table.setRowCount(0)
        row_idx = 0

        for action_id, item in sorted(self.shortcuts_data.items(), key=lambda x: x[1]["label"]):
            if item["source"] == "anki" and not show_anki:
                continue
            if item["source"] == "addon" and not show_addons:
                continue
            if current_scope != "all" and item["scope"] != current_scope:
                continue

            label = item["label"]
            scut = item["shortcut"]
            
            # Categorie precise
            scope_trans = self.i18n.t(f"scope_{item['scope']}", item['scope'])
            if item["source"] == "addon":
                cat_name = f"{item['addon_name']} ({scope_trans})"
            else:
                cat_name = scope_trans

            # Filtre de recherche
            if search_query:
                if search_query not in label.lower() and search_query not in scut.lower() and search_query not in cat_name.lower():
                    continue

            self.commands_table.insertRow(row_idx)

            # Colonne Commande
            col_action_item = QTableWidgetItem(label)
            col_action_item.setData(Qt.ItemDataRole.UserRole, action_id)
            self.commands_table.setItem(row_idx, 0, col_action_item)

            # Colonne Raccourci
            col_scut_item = QTableWidgetItem(scut if scut != "<nop>" else "")
            if item.get("is_disabled"):
                col_scut_item.setFlags(col_scut_item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.commands_table.setItem(row_idx, 1, col_scut_item)

            # Colonne Categorie
            col_cat_item = QTableWidgetItem(cat_name)
            self.commands_table.setItem(row_idx, 2, col_cat_item)

            row_idx += 1

    def filter_commands_table(self):
        self.populate_commands_table()

    def on_command_table_selected(self):
        """Lorsqu'une ligne est selectionnee dans le tableau, synchroniser le clavier virtuel."""
        selected_items = self.commands_table.selectedItems()
        if not selected_items:
            return
        row = selected_items[0].row()
        action_id = self.commands_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        item = self.shortcuts_data.get(action_id)
        if not item:
            return

        scut = item.get("shortcut", "")
        if scut and scut != "<nop>":
            mods, base_key = self.virtual_keyboard._parse_shortcut_string(scut)
            self.virtual_keyboard.set_active_modifiers(mods)
            if base_key:
                self.selected_key_id = base_key
                self.selected_key_label = base_key
                self.inspector_header.setText(f"{self.i18n.t('key_inspector_title')} {base_key}")
                self.btn_clear_key.setEnabled(True)
                self.btn_reset_key.setEnabled(True)
                self.update_key_inspector()

    def on_virtual_key_clicked(self, key_id, display_label):
        """Clic sur une touche du clavier virtuel : mise a jour ou deselection."""
        if not key_id:
            self.on_deselect_key()
            return

        self.selected_key_id = key_id
        self.selected_key_label = display_label or key_id
        self.inspector_header.setText(f"{self.i18n.t('key_inspector_title')} {self.selected_key_label}")
        self.btn_clear_key.setEnabled(True)
        self.btn_reset_key.setEnabled(True)
        self.update_key_inspector()

    def on_virtual_key_hovered(self, key_id, action_label):
        if key_id and action_label:
            self.status_label.setText(f"{key_id} : {action_label}")
        elif key_id:
            self.status_label.setText(f"{key_id}")
        else:
            self.status_label.setText("")

    def on_virtual_modifiers_changed(self, active_mods):
        self.update_key_inspector()

    def update_key_inspector(self):
        """Met a jour les combinaisons de modificateurs pour la touche selectionnee."""
        key_id = self.selected_key_id
        if not key_id:
            for row_idx, (trans_key, _) in enumerate(MODIFIER_COMBINATIONS):
                self.inspector_table.setItem(row_idx, 0, QTableWidgetItem(self.i18n.t(trans_key)))
                empty_item = QTableWidgetItem("-")
                empty_item.setData(Qt.ItemDataRole.UserRole, None)
                self.inspector_table.setItem(row_idx, 1, empty_item)
            return

        eff_id = key_id.upper()
        current_scope = self._current_scope
        show_anki = self.chk_filter_anki.isChecked()
        show_addons = self.chk_filter_addons.isChecked()

        for row_idx, (trans_key, mod_prefix) in enumerate(MODIFIER_COMBINATIONS):
            mod_label = self.i18n.t(trans_key)
            self.inspector_table.setItem(row_idx, 0, QTableWidgetItem(mod_label))

            matched_action = None
            matched_action_id = None
            for action_id, item in self.shortcuts_data.items():
                if item["source"] == "anki" and not show_anki:
                    continue
                if item["source"] == "addon" and not show_addons:
                    continue
                if current_scope != "all" and item["scope"] != current_scope:
                    continue
                
                _, item_base = self.virtual_keyboard._parse_shortcut_string(item["shortcut"])
                item_mods, _ = self.virtual_keyboard._parse_shortcut_string(item["shortcut"])
                item_full = "+".join(sorted(item_mods) + [item_base.upper()])
                test_full = "+".join(sorted(mod_prefix.split("+") if mod_prefix else []) + [eff_id])

                if item_full == test_full:
                    matched_action = item
                    matched_action_id = action_id
                    break

            if matched_action:
                act_text = f"{matched_action['label']} ({matched_action['shortcut']})"
                item_widget = QTableWidgetItem(act_text)
                item_widget.setData(Qt.ItemDataRole.UserRole, matched_action_id)
                self.inspector_table.setItem(row_idx, 1, item_widget)
            else:
                empty_item = QTableWidgetItem("-")
                empty_item.setData(Qt.ItemDataRole.UserRole, None)
                self.inspector_table.setItem(row_idx, 1, empty_item)

    def on_edit_shortcut_dialog(self, action_id=None):
        """Ouvre la boite de dialogue de saisie directe d'un nouveau raccourci."""
        if not action_id:
            selected_items = self.commands_table.selectedItems()
            if not selected_items:
                return
            row = selected_items[0].row()
            action_id = self.commands_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        item = self.shortcuts_data.get(action_id)
        if not item or item.get("is_disabled"):
            return

        dlg = KeySequenceCaptureDialog(self, item["label"], item["shortcut"], self.i18n)
        if dlg.exec():
            new_scut = dlg.captured_shortcut
            item["shortcut"] = new_scut
            self.refresh_display()

    def on_table_context_menu(self, pos):
        """Menu contextuel sur le tableau des commandes (Editer, Copier)."""
        item = self.commands_table.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        act_edit = menu.addAction(self.i18n.t("btn_edit_shortcut", "Modifier..."))
        menu.addSeparator()
        act_copy = menu.addAction(self.i18n.t("copy_cell", "Copier la valeur"))
        act_copy_row = menu.addAction(self.i18n.t("copy_row", "Copier la ligne"))
        
        chosen = menu.exec(self.commands_table.viewport().mapToGlobal(pos))
        if chosen == act_edit:
            self.on_edit_shortcut_dialog()
        elif chosen == act_copy:
            QApplication.clipboard().setText(item.text())
        elif chosen == act_copy_row:
            row = item.row()
            row_text = " | ".join(self.commands_table.item(row, col).text() for col in range(self.commands_table.columnCount()))
            QApplication.clipboard().setText(row_text)

    def on_inspector_context_menu(self, pos):
        """Menu contextuel sur l'inspecteur."""
        item = self.inspector_table.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        act_copy = menu.addAction(self.i18n.t("copy_cell", "Copier la valeur"))
        chosen = menu.exec(self.inspector_table.viewport().mapToGlobal(pos))
        if chosen == act_copy:
            QApplication.clipboard().setText(item.text())

    def on_inspector_row_double_clicked(self, table_item):
        """Double-clic sur une combinaison dans l'inspecteur."""
        action_id = table_item.data(Qt.ItemDataRole.UserRole)
        if action_id:
            self.on_edit_shortcut_dialog(action_id)
        else:
            # Assigner la commande actuellement selectionnee dans le tableau a cette combinaison
            selected_items = self.commands_table.selectedItems()
            if selected_items and self.selected_key_id:
                row = selected_items[0].row()
                cmd_id = self.commands_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                cmd_item = self.shortcuts_data.get(cmd_id)
                if cmd_item and not cmd_item.get("is_disabled"):
                    current_row = self.inspector_table.currentRow()
                    _, mod_prefix = MODIFIER_COMBINATIONS[current_row]
                    eff_id = self.selected_key_id.upper()
                    new_scut = f"{mod_prefix}+{eff_id}".strip("+") if mod_prefix else eff_id
                    cmd_item["shortcut"] = new_scut
                    self.refresh_display()

    def on_clear_selected_key_combination(self):
        """Desactive le raccourci correspondant a la combinaison selectionnee."""
        current_row = self.inspector_table.currentRow()
        if current_row < 0:
            return
        action_item = self.inspector_table.item(current_row, 1)
        action_id = action_item.data(Qt.ItemDataRole.UserRole)
        if action_id and action_id in self.shortcuts_data:
            if not self.shortcuts_data[action_id].get("is_disabled"):
                self.shortcuts_data[action_id]["shortcut"] = "<nop>"
                self.refresh_display()

    def on_reset_selected_key_combination(self):
        """Retablit le raccourci par defaut pour la combinaison selectionnee."""
        current_row = self.inspector_table.currentRow()
        if current_row < 0:
            return
        action_item = self.inspector_table.item(current_row, 1)
        action_id = action_item.data(Qt.ItemDataRole.UserRole)
        if action_id and action_id in self.shortcuts_data:
            def_scut = self.shortcuts_data[action_id].get("default_shortcut", "<nop>")
            self.shortcuts_data[action_id]["shortcut"] = def_scut
            self.refresh_display()

    def _set_scope(self, scope_id):
        """Active la portee donnee et met a jour les boutons."""
        if scope_id not in self._scope_buttons:
            scope_id = "all"
        self._current_scope = scope_id
        for sid, btn in self._scope_buttons.items():
            btn.setChecked(sid == scope_id)
        self.refresh_display()

    def _on_scope_button_clicked(self):
        """Slot des boutons de portee - comportement exclusif."""
        sender = self.sender()
        if sender:
            scope_id = sender.property("scope_id")
            # Si on re-clique sur le bouton deja actif, on reste dessus
            if scope_id:
                self._set_scope(scope_id)

    def on_scope_changed(self):
        """Compatibilite - ne plus utilisee directement."""
        self.refresh_display()

    def on_layout_changed(self):
        mode = self.layout_combo.currentData()
        self.virtual_keyboard.set_layout_mode(mode)

    def restore_all_defaults(self):
        """Retablit l'ensemble des raccourcis a leur valeur par defaut."""
        for action_id, item in self.shortcuts_data.items():
            item["shortcut"] = item.get("default_shortcut", "<nop>")
        self.refresh_display()

    def apply_changes(self):
        """Sauvegarde les modifications dans Anki et applique les raccourcis aux extensions."""
        try:
            saveGeom(self, "shortcutManagerVisual")
        except Exception:
            pass
        
        overrides = self.config.get("addon_shortcuts_overrides", {})
        if not isinstance(overrides, dict):
            overrides = {}

        # Application et persistance
        for action_id, item in self.shortcuts_data.items():
            scut = item["shortcut"]
            if item.get("source") == "anki" and not item.get("is_disabled"):
                orig_key = item.get("original_key", action_id)
                self.config[orig_key] = scut
            elif item.get("source") == "addon":
                orig_key = item.get("original_key", action_id)
                name_key = f"{item.get('addon_name')}_{item.get('action_name')}"
                
                overrides[orig_key] = scut
                overrides[name_key] = scut

                # 1. Mise a jour immediate des objets Qt vivants
                qact = item.get("qaction")
                if qact and hasattr(qact, "setShortcut"):
                    try:
                        qact.setShortcut(QKeySequence(scut if scut != "<nop>" else ""))
                    except Exception:
                        pass
                
                qs = item.get("qshortcut")
                if qs and hasattr(qs, "setKey"):
                    try:
                        qs.setKey(QKeySequence(scut if scut != "<nop>" else ""))
                    except Exception:
                        pass

                # 2. Mise a jour pour l'ecosysteme EDN
                edn = item.get("edn_info")
                if edn and isinstance(edn, dict):
                    try:
                        from Anki_EDN_Lier_les_cartes.edn_menu import shared_menu
                        sk = edn.get("shortcut_key")
                        if sk:
                            shared_menu.set_shortcut(sk, scut)
                    except Exception:
                        pass

                # 3. Mise a jour de la configuration de l'addon tiers
                addon_id = item.get("addon_id")
                cfg_key = item.get("config_key")
                if addon_id and cfg_key and mw and hasattr(mw, "addonManager") and mw.addonManager:
                    try:
                        third_cfg = mw.addonManager.getConfig(addon_id)
                        if isinstance(third_cfg, dict) and cfg_key in third_cfg:
                            third_cfg[cfg_key] = scut
                            mw.addonManager.writeConfig(addon_id, third_cfg)
                    except Exception:
                        pass

        self.config["addon_shortcuts_overrides"] = overrides
        # La langue est lue depuis config.json (interface_language), pas modifiee ici

        # Ecriture de la configuration du customizer
        if mw and hasattr(mw, "addonManager") and mw.addonManager:
            mw.addonManager.writeConfig(__name__, self.config)
        else:
            try:
                _cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
                with open(_cfg_path, "w", encoding="utf-8") as _f:
                    json.dump(self.config, _f, ensure_ascii=False, indent=4)
            except Exception:
                pass

        if USER_CONFIG_PATH and os.path.exists(os.path.dirname(USER_CONFIG_PATH)):
            try:
                with open(USER_CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=4)
            except Exception:
                pass

        showInfo(self.i18n.t("changes_saved"))

    def accept_changes(self):
        self.apply_changes()
        self.accept()

    def select_config_path(self):
        global USER_CONFIG_PATH
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.i18n.t("config_path_label"),
            os.path.expanduser("~"),
            "JSON Files (*.json)"
        )
        if file_path:
            USER_CONFIG_PATH = file_path
            self.path_info_label.setText(file_path)
            self.config["config_file_path"] = file_path
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=4)
                showInfo(self.i18n.t("save_success"))
            except Exception as e:
                showInfo(f"{self.i18n.t('save_error')} : {str(e)}")

    def on_theme_changed(self):
        self.virtual_keyboard.update()


def init_config_path():
    global USER_CONFIG_PATH
    config = mw.addonManager.getConfig(__name__)
    if config and "config_file_path" in config:
        path = config["config_file_path"]
        if os.path.exists(os.path.dirname(path)):
            USER_CONFIG_PATH = path

def open_shortcut_manager(context=None):
    """Point d'entree pour ouvrir le gestionnaire de raccourcis."""
    init_config_path()
    dialog = ShortcutManagerDialog(mw, initial_context=context)
    try:
        dialog.exec()
    except AttributeError:
        dialog.exec_()