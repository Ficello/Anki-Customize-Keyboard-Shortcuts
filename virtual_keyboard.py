# -*- coding: utf-8 -*-
"""
Composant Clavier Virtuel Interactif inspire d'Adobe After Effects.
Affiche une vue complete et fidele du clavier avec rendu graphique personnalise (QPainter).
Permet la visualisation directe des raccourcis sur chaque touche, la bascule AZERTY / QWERTY,
l'adaptation en direct selon les touches de modification physiques ou cliquees (Ctrl, Alt, Maj),
et la selection interactive pour inspection.
"""

import sys
import ctypes
from aqt.qt import *
from aqt import mw

def detect_windows_keyboard_layout() -> str:
    """
    Detecte la disposition de clavier active sous Windows via l'API Win32.
    Renvoie 'AZERTY', 'QWERTY', 'QWERTZ', 'DVORAK' ou 'COLEMAK'.
    """
    if sys.platform != "win32":
        return "AZERTY"
    try:
        user32 = ctypes.windll.user32
        buf = ctypes.create_unicode_buffer(9)
        if user32.GetKeyboardLayoutNameW(buf):
            klid = buf.value.upper()
            if klid == "00010409":
                return "DVORAK"
            if klid.endswith("040C") or klid.endswith("080C"):
                return "AZERTY"
            if klid.endswith("0407") or klid.endswith("0807") or klid.endswith("100C") or klid.endswith("041B"):
                return "QWERTZ"
    except Exception:
        pass
    return "QWERTY"

LAYOUT_EFFECTIVE_KEYS = {
    "AZERTY": {
        "Q": "A", "W": "Z", "A": "Q", "SEMICOLON": "M",
        "Z": "W", "M": "COMMA"
    },
    "QWERTY": {},
    "QWERTZ": {
        "Y": "Z", "Z": "Y"
    },
    "DVORAK": {
        "Q": "APOSTROPHE", "W": "COMMA", "E": "PERIOD", "R": "P", "T": "Y", "Y": "F", "U": "G", "I": "C", "O": "R", "P": "L",
        "A": "A", "S": "O", "D": "E", "F": "U", "G": "I", "H": "D", "J": "H", "K": "T", "L": "N", "SEMICOLON": "S",
        "Z": "SEMICOLON", "X": "Q", "C": "J", "V": "K", "B": "X", "N": "B", "M": "M"
    },
    "COLEMAK": {
        "E": "F", "R": "P", "T": "G", "Y": "J", "U": "L", "I": "U", "O": "Y", "P": "SEMICOLON",
        "S": "R", "D": "S", "F": "T", "G": "D", "J": "N", "K": "E", "L": "I", "SEMICOLON": "O",
        "N": "K"
    }
}

LAYOUT_LABELS = {
    "AZERTY": {
        "GRAVE": "²",
        "1": "& 1", "2": "é 2", "3": "\" 3", "4": "' 4", "5": "( 5",
        "6": "- 6", "7": "è 7", "8": "_ 8", "9": "ç 9", "0": "à 0",
        "MINUS": ") °", "EQUAL": "= +",
        "Q": "A", "W": "Z", "E": "E", "R": "R", "T": "T", "Y": "Y", "U": "U", "I": "I", "O": "O", "P": "P",
        "BRACKET_L": "^ ¨", "BRACKET_R": "$ £", "BACKSLASH": "* µ",
        "A": "Q", "S": "S", "D": "D", "F": "F", "G": "G", "H": "H", "J": "J", "K": "K", "L": "L", "SEMICOLON": "M",
        "APOSTROPHE": "ù %",
        "Z": "W", "X": "X", "C": "C", "V": "V", "B": "B", "N": "N", "M": ", ?",
        "COMMA": "; .", "PERIOD": ": /", "SLASH": "! §"
    },
    "QWERTY": {
        "GRAVE": "~ `", "1": "1", "2": "2", "3": "3", "4": "4", "5": "5",
        "6": "6", "7": "7", "8": "8", "9": "9", "0": "0", "MINUS": "- _", "EQUAL": "= +",
        "Q": "Q", "W": "W", "E": "E", "R": "R", "T": "T", "Y": "Y", "U": "U", "I": "I", "O": "O", "P": "P",
        "BRACKET_L": "[ {", "BRACKET_R": "] }", "BACKSLASH": "\\ |",
        "A": "A", "S": "S", "D": "D", "F": "F", "G": "G", "H": "H", "J": "J", "K": "K", "L": "L", "SEMICOLON": "; :",
        "APOSTROPHE": "' \"",
        "Z": "Z", "X": "X", "C": "C", "V": "V", "B": "B", "N": "N", "M": "M",
        "COMMA": ", <", "PERIOD": ". >", "SLASH": "/ ?"
    },
    "QWERTZ": {
        "GRAVE": "^ °", "1": "1", "2": "2", "3": "3", "4": "4", "5": "5",
        "6": "6", "7": "7", "8": "8", "9": "9", "0": "0", "MINUS": "ß ?", "EQUAL": "´ `",
        "Q": "Q", "W": "W", "E": "E", "R": "R", "T": "T", "Y": "Z", "U": "U", "I": "I", "O": "O", "P": "P",
        "BRACKET_L": "Ü", "BRACKET_R": "+ *", "BACKSLASH": "# '",
        "A": "A", "S": "S", "D": "D", "F": "F", "G": "G", "H": "H", "J": "J", "K": "K", "L": "L", "SEMICOLON": "Ö",
        "APOSTROPHE": "Ä",
        "Z": "Y", "X": "X", "C": "C", "V": "V", "B": "B", "N": "N", "M": "M",
        "COMMA": ", ;", "PERIOD": ". :", "SLASH": "- _"
    },
    "DVORAK": {
        "Q": "' \"", "W": ", <", "E": ". >", "R": "P", "T": "Y", "Y": "F", "U": "G", "I": "C", "O": "R", "P": "L",
        "BRACKET_L": "/ ?", "BRACKET_R": "= +",
        "A": "A", "S": "O", "D": "E", "F": "U", "G": "I", "H": "D", "J": "H", "K": "T", "L": "N", "SEMICOLON": "S",
        "APOSTROPHE": "- _",
        "Z": "; :", "X": "Q", "C": "J", "V": "K", "B": "X", "N": "B", "M": "M"
    },
    "COLEMAK": {
        "E": "F", "R": "P", "T": "G", "Y": "J", "U": "L", "I": "U", "O": "Y", "P": "; :",
        "A": "A", "R": "S", "S": "R", "D": "S", "F": "T", "T": "G", "G": "D", "J": "N", "K": "E", "L": "I", "SEMICOLON": "O",
        "N": "K"
    }
}

# Palettes de couleurs sobres et elegantes (sans emojis)
THEME_DARK = {
    "bg": QColor("#1e1e24"),
    "key_bg": QColor("#2b2b36"),
    "key_bg_hover": QColor("#3a3a4a"),
    "key_bg_selected": QColor("#46465c"),
    "border": QColor("#3f3f50"),
    "border_selected": QColor("#63b3ed"),
    "text_key": QColor("#e2e8f0"),
    "text_key_dim": QColor("#a0aec0"),
    "text_action": QColor("#ffffff"),
    "anki_tint": QColor("#3182ce"),       # Bleu sobre pour les actions Anki
    "addon_tint": QColor("#2b6cb0"),      # Sarcelle / Turquoise pour autres addons
    "custom_tint": QColor("#d69e2e"),     # Ambre pour les raccourcis modifies
    "modifier_active": QColor("#805ad5"), # Violet sobre pour modificateur actif
    "legend_text": QColor("#cbd5e0")
}

THEME_LIGHT = {
    "bg": QColor("#f7fafc"),
    "key_bg": QColor("#edf2f7"),
    "key_bg_hover": QColor("#e2e8f0"),
    "key_bg_selected": QColor("#cbd5e0"),
    "border": QColor("#cbd5e0"),
    "border_selected": QColor("#2b6cb0"),
    "text_key": QColor("#2d3748"),
    "text_key_dim": QColor("#718096"),
    "text_action": QColor("#1a202c"),
    "anki_tint": QColor("#90cdf4"),
    "addon_tint": QColor("#81e6d9"),
    "custom_tint": QColor("#fbd38d"),
    "modifier_active": QColor("#d6bcfa"),
    "legend_text": QColor("#4a5568")
}

class KeyDef:
    """Definition structurelle d'une touche du clavier virtuel."""
    def __init__(self, key_id, label_qwerty, label_azerty=None, width_units=1.0, is_modifier=False, mod_type=None, is_spacer=False):
        self.key_id = key_id                      # Ex: 'A', '1', 'F1', 'Return', 'Space', 'Ctrl_L'
        self.label_qwerty = label_qwerty          # Label principal en QWERTY
        self.label_azerty = label_azerty or label_qwerty  # Label en AZERTY
        self.width_units = width_units            # Largeur relative (1.0 = touche standard)
        self.is_modifier = is_modifier            # True pour Ctrl, Alt, Shift...
        self.mod_type = mod_type                  # 'Ctrl', 'Alt', 'Shift'
        self.is_spacer = is_spacer                # Espacement vide

class VirtualKeyboardWidget(QWidget):
    key_clicked = pyqtSignal(str, str)     # (key_id, display_label)
    key_hovered = pyqtSignal(str, str)     # (key_id, current_action)
    modifiers_changed = pyqtSignal(set)    # set des modificateurs actifs {'Ctrl', 'Alt', 'Shift'}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        self.layout_mode = "AUTO"  # "AUTO", "AZERTY", "QWERTY", "QWERTZ", "DVORAK", "COLEMAK"
        self.active_modifiers = set() # {'Ctrl', 'Alt', 'Shift'}
        self.show_anki = True
        self.show_addons = True
        
        # Mappings de raccourcis : { (modifier_str, key_id): ActionInfo }
        self.shortcut_map = {} 
        self.all_keys_with_actions = set() # ensemble des key_id ayant au moins une action

        self.selected_key_id = None
        self.hovered_key_id = None
        self.key_rects = {} # key_id -> QRectF

        self.setMinimumSize(880, 290)
        self._build_keyboard_structure()

    def _is_dark_mode(self):
        try:
            from aqt.theme import theme_manager
            return theme_manager.night_mode
        except Exception:
            return True

    def get_theme(self):
        return THEME_DARK if self._is_dark_mode() else THEME_LIGHT

    def set_layout_mode(self, mode):
        if self.layout_mode != mode:
            self.layout_mode = mode
            self.update()

    def set_source_filters(self, show_anki=True, show_addons=True):
        self.show_anki = show_anki
        self.show_addons = show_addons
        self.update()

    def deselect_key(self):
        if self.selected_key_id is not None:
            self.selected_key_id = None
            self.key_clicked.emit("", "")
            self.update()

    def _get_effective_layout(self):
        if self.layout_mode == "AUTO":
            return detect_windows_keyboard_layout()
        return self.layout_mode

    def set_shortcut_data(self, shortcut_dict):
        """
        shortcut_dict structure :
        {
            "main add": {"shortcut": "A", "label": "Ajouter", "source": "anki", "scope": "main"},
            "editor bold": {"shortcut": "Ctrl+B", "label": "Gras", "source": "anki", "scope": "editor"},
            ...
        }
        """
        self.shortcut_map.clear()
        self.all_keys_with_actions.clear()

        for action_id, info in shortcut_dict.items():
            scut = info.get("shortcut", "").strip()
            if not scut or scut.lower() in ("<nop>", "none", "<default>"):
                continue

            # Parsing du raccourci
            mods, base_key = self._parse_shortcut_string(scut)
            if base_key:
                mod_key = "+".join(sorted(mods))
                dict_key = (mod_key, base_key.upper())
                self.shortcut_map[dict_key] = {
                    "action_id": action_id,
                    "label": info.get("label", action_id),
                    "source": info.get("source", "anki"),
                    "scope": info.get("scope", "main"),
                    "full_shortcut": scut
                }
                self.all_keys_with_actions.add(base_key.upper())

        self.update()

    def _parse_shortcut_string(self, scut):
        """Separe les modificateurs et la touche de base."""
        parts = [p.strip() for p in scut.split("+") if p.strip()]
        mods = []
        base = ""
        for p in parts:
            pl = p.lower()
            if pl in ("ctrl", "control"):
                mods.append("Ctrl")
            elif pl in ("alt", "option"):
                mods.append("Alt")
            elif pl in ("shift", "maj"):
                mods.append("Shift")
            elif pl in ("meta", "win", "cmd"):
                mods.append("Meta")
            else:
                base = p

        # Normalisation de la touche de base
        base_norm = self._normalize_key_name(base)
        return mods, base_norm

    def _normalize_key_name(self, name):
        if not name:
            return ""
        n = name.upper()
        mapping = {
            "RETURN": "RETURN",
            "ENTER": "ENTER",
            "SPACE": "SPACE",
            "BACKSPACE": "BACKSPACE",
            "DELETE": "DEL",
            "DEL": "DEL",
            "TAB": "TAB",
            "ESC": "ESC",
            "ESCAPE": "ESC",
            "UP": "UP",
            "DOWN": "DOWN",
            "LEFT": "LEFT",
            "RIGHT": "RIGHT",
            "PAGEUP": "PGUP",
            "PAGEDOWN": "PGDN",
            "HOME": "HOME",
            "END": "END",
            "INS": "INS",
            "INSERT": "INS",
            "*": "*",
            "-": "-",
            "+": "+",
            "=": "=",
            "!": "!",
            ":": ":",
            "/": "/"
        }
        return mapping.get(n, n)

    def _build_keyboard_structure(self):
        """Construit les 6 rangees du clavier complet ISO/ANSI avec pave num."""
        self.rows = []

        # Rangee 0 : F-Keys
        row0 = [
            KeyDef("ESC", "Esc", "Échap", 1.0),
            KeyDef("GAP_F1", "", "", 0.75, is_spacer=True),
            KeyDef("F1", "F1", "F1", 1.0),
            KeyDef("F2", "F2", "F2", 1.0),
            KeyDef("F3", "F3", "F3", 1.0),
            KeyDef("F4", "F4", "F4", 1.0),
            KeyDef("GAP_F2", "", "", 0.5, is_spacer=True),
            KeyDef("F5", "F5", "F5", 1.0),
            KeyDef("F6", "F6", "F6", 1.0),
            KeyDef("F7", "F7", "F7", 1.0),
            KeyDef("F8", "F8", "F8", 1.0),
            KeyDef("GAP_F3", "", "", 0.5, is_spacer=True),
            KeyDef("F9", "F9", "F9", 1.0),
            KeyDef("F10", "F10", "F10", 1.0),
            KeyDef("F11", "F11", "F11", 1.0),
            KeyDef("F12", "F12", "F12", 1.0),
            KeyDef("GAP_F4", "", "", 0.5, is_spacer=True),
            KeyDef("PRINTSCREEN", "PrtSc", "Impr", 1.0),
            KeyDef("SCROLLLOCK", "ScrLk", "Arrêt", 1.0),
            KeyDef("PAUSE", "Pause", "Attn", 1.0),
            KeyDef("GAP_F5", "", "", 0.5, is_spacer=True),
            KeyDef("NUM_LOCK", "Num", "VerrNum", 1.0),
            KeyDef("NUM_DIV", "/", "/", 1.0),
            KeyDef("NUM_MUL", "*", "*", 1.0),
            KeyDef("NUM_SUB", "-", "-", 1.0),
        ]

        # Rangee 1 : Chiffres
        row1 = [
            KeyDef("GRAVE", "~ `", "²", 1.0),
            KeyDef("1", "1", "& 1", 1.0),
            KeyDef("2", "2", "é 2", 1.0),
            KeyDef("3", "3", "\" 3", 1.0),
            KeyDef("4", "4", "' 4", 1.0),
            KeyDef("5", "5", "( 5", 1.0),
            KeyDef("6", "6", "- 6", 1.0),
            KeyDef("7", "7", "è 7", 1.0),
            KeyDef("8", "8", "_ 8", 1.0),
            KeyDef("9", "9", "ç 9", 1.0),
            KeyDef("0", "0", "à 0", 1.0),
            KeyDef("MINUS", "- _", ") °", 1.0),
            KeyDef("EQUAL", "= +", "= +", 1.0),
            KeyDef("BACKSPACE", "Backspace", "Effacer", 2.0),
            KeyDef("GAP_R1", "", "", 0.5, is_spacer=True),
            KeyDef("INS", "Ins", "Inser", 1.0),
            KeyDef("HOME", "Home", "Début", 1.0),
            KeyDef("PGUP", "PgUp", "PgPréc", 1.0),
            KeyDef("GAP_R1_NUM", "", "", 0.5, is_spacer=True),
            KeyDef("NUM_7", "7", "7", 1.0),
            KeyDef("NUM_8", "8", "8", 1.0),
            KeyDef("NUM_9", "9", "9", 1.0),
            KeyDef("NUM_ADD", "+", "+", 1.0),
        ]

        # Rangee 2 : Lettres sup (QWERTY Q-P / AZERTY A-P)
        row2 = [
            KeyDef("TAB", "Tab", "Tab", 1.5),
            KeyDef("Q", "Q", "A", 1.0),
            KeyDef("W", "W", "Z", 1.0),
            KeyDef("E", "E", "E", 1.0),
            KeyDef("R", "R", "R", 1.0),
            KeyDef("T", "T", "T", 1.0),
            KeyDef("Y", "Y", "Y", 1.0),
            KeyDef("U", "U", "U", 1.0),
            KeyDef("I", "I", "I", 1.0),
            KeyDef("O", "O", "O", 1.0),
            KeyDef("P", "P", "P", 1.0),
            KeyDef("BRACKET_L", "[ {", "^ ¨", 1.0),
            KeyDef("BRACKET_R", "] }", "$ £", 1.0),
            KeyDef("BACKSLASH", "\\ |", "* µ", 1.5),
            KeyDef("GAP_R2", "", "", 0.5, is_spacer=True),
            KeyDef("DEL", "Del", "Suppr", 1.0),
            KeyDef("END", "End", "Fin", 1.0),
            KeyDef("PGDN", "PgDn", "PgSuiv", 1.0),
            KeyDef("GAP_R2_NUM", "", "", 0.5, is_spacer=True),
            KeyDef("NUM_4", "4", "4", 1.0),
            KeyDef("NUM_5", "5", "5", 1.0),
            KeyDef("NUM_6", "6", "6", 1.0),
            KeyDef("GAP_NUM_ADD", "", "", 1.0, is_spacer=True), # Occupe par NUM_ADD sur 2 lignes visuellement
        ]

        # Rangee 3 : Lettres milieu (A-L / Q-M)
        row3 = [
            KeyDef("CAPS", "Caps", "VerrMaj", 1.8),
            KeyDef("A", "A", "Q", 1.0),
            KeyDef("S", "S", "S", 1.0),
            KeyDef("D", "D", "D", 1.0),
            KeyDef("F", "F", "F", 1.0),
            KeyDef("G", "G", "G", 1.0),
            KeyDef("H", "H", "H", 1.0),
            KeyDef("J", "J", "J", 1.0),
            KeyDef("K", "K", "K", 1.0),
            KeyDef("L", "L", "L", 1.0),
            KeyDef("SEMICOLON", "; :", "M", 1.0),
            KeyDef("APOSTROPHE", "' \"", "ù %", 1.0),
            KeyDef("RETURN", "Enter", "Entrée", 2.2),
            KeyDef("GAP_R3", "", "", 3.5, is_spacer=True),
            KeyDef("GAP_R3_NUM", "", "", 0.5, is_spacer=True),
            KeyDef("NUM_1", "1", "1", 1.0),
            KeyDef("NUM_2", "2", "2", 1.0),
            KeyDef("NUM_3", "3", "3", 1.0),
            KeyDef("NUM_ENTER", "Enter", "Entrée", 1.0),
        ]

        # Rangee 4 : Lettres bas (Z-M / W-!)
        row4 = [
            KeyDef("SHIFT_L", "Shift", "Maj", 2.2, is_modifier=True, mod_type="Shift"),
            KeyDef("LESS_THAN", "< >", "< >", 0.9),
            KeyDef("Z", "Z", "W", 1.0),
            KeyDef("X", "X", "X", 1.0),
            KeyDef("C", "C", "C", 1.0),
            KeyDef("V", "V", "V", 1.0),
            KeyDef("B", "B", "B", 1.0),
            KeyDef("N", "N", "N", 1.0),
            KeyDef("M", "M", ", ?", 1.0),
            KeyDef("COMMA", ", <", "; .", 1.0),
            KeyDef("PERIOD", ". >", ": /", 1.0),
            KeyDef("SLASH", "/ ?", "! §", 1.0),
            KeyDef("SHIFT_R", "Shift", "Maj", 2.4, is_modifier=True, mod_type="Shift"),
            KeyDef("GAP_R4", "", "", 1.5, is_spacer=True),
            KeyDef("UP", "▲", "▲", 1.0),
            KeyDef("GAP_R4_NAV", "", "", 1.0, is_spacer=True),
            KeyDef("GAP_R4_NUM", "", "", 0.5, is_spacer=True),
            KeyDef("NUM_0", "0", "0", 2.0),
            KeyDef("NUM_DECIMAL", ".", ".", 1.0),
            KeyDef("GAP_NUM_ENTER", "", "", 1.0, is_spacer=True),
        ]

        # Rangee 5 : Modificateurs et Espace
        row5 = [
            KeyDef("CTRL_L", "Ctrl", "Ctrl", 1.4, is_modifier=True, mod_type="Ctrl"),
            KeyDef("WIN_L", "Win", "Win", 1.25),
            KeyDef("ALT_L", "Alt", "Alt", 1.4, is_modifier=True, mod_type="Alt"),
            KeyDef("SPACE", "Space", "Espace", 6.2),
            KeyDef("ALT_R", "AltGr", "AltGr", 1.4, is_modifier=True, mod_type="Alt"),
            KeyDef("WIN_R", "Win", "Win", 1.25),
            KeyDef("MENU", "Menu", "Menu", 1.2),
            KeyDef("CTRL_R", "Ctrl", "Ctrl", 1.4, is_modifier=True, mod_type="Ctrl"),
            KeyDef("GAP_R5", "", "", 0.5, is_spacer=True),
            KeyDef("LEFT", "◀", "◀", 1.0),
            KeyDef("DOWN", "▼", "▼", 1.0),
            KeyDef("RIGHT", "▶", "▶", 1.0),
            KeyDef("GAP_R5_NUM", "", "", 0.5, is_spacer=True),
            KeyDef("GAP_NUM_PAD_BOTTOM", "", "", 4.0, is_spacer=True),
        ]

        self.rows = [row0, row1, row2, row3, row4, row5]

    def _get_key_effective_id(self, key_def):
        """Retourne l'identifiant de la touche en tenant compte de la disposition."""
        eff_mode = self._get_effective_layout()
        mapping = LAYOUT_EFFECTIVE_KEYS.get(eff_mode, {})
        return mapping.get(key_def.key_id, key_def.key_id)

    def _get_key_display_label(self, key_def):
        eff_mode = self._get_effective_layout()
        layout_dict = LAYOUT_LABELS.get(eff_mode, {})
        if key_def.key_id in layout_dict:
            return layout_dict[key_def.key_id]
        if eff_mode == "AZERTY":
            return key_def.label_azerty
        return key_def.label_qwerty

    def toggle_modifier(self, mod_name):
        if mod_name in self.active_modifiers:
            self.active_modifiers.remove(mod_name)
        else:
            self.active_modifiers.add(mod_name)
        self.modifiers_changed.emit(self.active_modifiers)
        self.update()

    def set_active_modifiers(self, mods):
        self.active_modifiers = set(mods)
        self.modifiers_changed.emit(self.active_modifiers)
        self.update()

    def keyPressEvent(self, event):
        key = event.key()
        updated = False
        if key in (Qt.Key.Key_Control,):
            self.active_modifiers.add("Ctrl")
            updated = True
        elif key in (Qt.Key.Key_Alt,):
            self.active_modifiers.add("Alt")
            updated = True
        elif key in (Qt.Key.Key_Shift,):
            self.active_modifiers.add("Shift")
            updated = True

        if updated:
            self.modifiers_changed.emit(self.active_modifiers)
            self.update()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        key = event.key()
        updated = False
        if key in (Qt.Key.Key_Control,):
            self.active_modifiers.discard("Ctrl")
            updated = True
        elif key in (Qt.Key.Key_Alt,):
            self.active_modifiers.discard("Alt")
            updated = True
        elif key in (Qt.Key.Key_Shift,):
            self.active_modifiers.discard("Shift")
            updated = True

        if updated:
            self.modifiers_changed.emit(self.active_modifiers)
            self.update()
        super().keyReleaseEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position() if hasattr(event, "position") else event.pos()
        hovered = None
        for key_id, rect in self.key_rects.items():
            if rect.contains(pos):
                hovered = key_id
                break
        
        if hovered != self.hovered_key_id:
            self.hovered_key_id = hovered
            action_label = self._get_action_for_key(hovered) if hovered else ""
            self.key_hovered.emit(hovered or "", action_label)
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        if self.hovered_key_id:
            self.hovered_key_id = None
            self.key_hovered.emit("", "")
            self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position() if hasattr(event, "position") else event.pos()
            for key_id, rect in self.key_rects.items():
                if rect.contains(pos):
                    # Verifier si c'est un modificateur
                    for row in self.rows:
                        for kdef in row:
                            if kdef.key_id == key_id and kdef.is_modifier and kdef.mod_type:
                                self.toggle_modifier(kdef.mod_type)
                                return
                    
                    # Si on clique a nouveau sur la meme touche -> Deselection !
                    if self.selected_key_id == key_id:
                        self.selected_key_id = None
                        self.key_clicked.emit("", "")
                        self.update()
                        return

                    self.selected_key_id = key_id
                    display_lbl = ""
                    for row in self.rows:
                        for kdef in row:
                            if kdef.key_id == key_id:
                                display_lbl = self._get_key_display_label(kdef)
                                break
                    self.key_clicked.emit(key_id, display_lbl)
                    self.update()
                    return

            # Clic dans le vide ou un espace vide -> Deselection
            if self.selected_key_id is not None:
                self.selected_key_id = None
                self.key_clicked.emit("", "")
                self.update()
        super().mousePressEvent(event)

    def _get_action_for_key(self, key_id):
        """Recherche l'action associee a la touche pour l'etat actuel des modificateurs."""
        eff_id = key_id.upper()
        mod_key = "+".join(sorted(self.active_modifiers))
        info = self.shortcut_map.get((mod_key, eff_id))
        if info:
            return info.get("label", "")
        return ""

    def _has_any_action(self, key_id):
        """Indique si la touche possede une action (sous n'importe quel modificateur)."""
        eff_id = key_id.upper()
        return eff_id in self.all_keys_with_actions

    def _get_action_info(self, key_id):
        """Retourne les details de l'action sous les modificateurs courants."""
        eff_id = key_id.upper()
        mod_key = "+".join(sorted(self.active_modifiers))
        return self.shortcut_map.get((mod_key, eff_id))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        theme = self.get_theme()
        w = self.width()
        h = self.height()

        # Fond principal du clavier
        painter.fillRect(0, 0, w, h, theme["bg"])

        # Calcul des dimensions des touches
        total_units_per_row = 23.5  # Largeur totale cumulee d'une ligne
        padding = 8
        gap = 3

        avail_w = w - (2 * padding)
        avail_h = h - (2 * padding)

        unit_w = (avail_w - (total_units_per_row * gap)) / total_units_per_row
        row_h = (avail_h - (len(self.rows) * gap)) / len(self.rows)

        self.key_rects.clear()

        y = padding
        for row_idx, row in enumerate(self.rows):
            x = padding
            for key_def in row:
                kw = (key_def.width_units * unit_w) + ((key_def.width_units - 1.0) * gap)
                rect = QRectF(x, y, kw, row_h)

                if not key_def.is_spacer:
                    self.key_rects[key_def.key_id] = rect
                    self._paint_key(painter, key_def, rect, theme)

                x += kw + gap
            y += row_h + gap

    def _paint_key(self, painter, key_def, rect, theme):
        key_id = key_def.key_id
        eff_id = self._get_key_effective_id(key_def)
        is_hovered = (key_id == self.hovered_key_id)
        is_selected = (key_id == self.selected_key_id)
        
        # Verification si modificateur actif
        is_mod_active = False
        if key_def.is_modifier and key_def.mod_type:
            is_mod_active = (key_def.mod_type in self.active_modifiers)

        # Action associee
        action_info = self._get_action_info(eff_id)
        if action_info:
            src = action_info.get("source", "anki")
            if (src == "anki" and not self.show_anki) or (src == "addon" and not self.show_addons):
                action_info = None

        has_current_action = (action_info is not None)
        has_any_action = self._has_any_action(eff_id)
        if not self.show_anki and not self.show_addons:
            has_any_action = False

        # 1. Couleur de fond de base
        if is_mod_active:
            bg_color = theme["modifier_active"]
        elif has_current_action:
            src = action_info.get("source", "anki")
            bg_color = theme["addon_tint"] if src == "addon" else theme["anki_tint"]
        elif is_selected:
            bg_color = theme["key_bg_selected"]
        elif is_hovered:
            bg_color = theme["key_bg_hover"]
        else:
            bg_color = theme["key_bg"]

        # Dessin du rectangle avec coins arrondis
        painter.save()
        radius = 3.5

        # Fond
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect, radius, radius)

        # Style After Effects : triangle diagonal si la touche a d'autres actions sous d'autres modificateurs
        if has_any_action and not has_current_action:
            triangle_path = QPainterPath()
            triangle_path.moveTo(rect.right() - 8, rect.top())
            triangle_path.lineTo(rect.right(), rect.top())
            triangle_path.lineTo(rect.right(), rect.top() + 8)
            triangle_path.closeSubpath()
            painter.fillPath(triangle_path, QBrush(theme["anki_tint"]))

        # Bordure
        if is_selected:
            pen = QPen(theme["border_selected"], 2.0)
        elif is_hovered:
            pen = QPen(theme["text_key_dim"], 1.2)
        else:
            pen = QPen(theme["border"], 1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, radius, radius)

        # 2. Rendu textuel : Nom de la touche
        display_label = self._get_key_display_label(key_def)
        
        font_key = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font_key)
        painter.setPen(theme["text_key"] if not is_mod_active else QColor("#ffffff"))

        # Positionnement de l'etiquette de la touche
        if has_current_action:
            # Touche active : etiquette en bas a gauche, action en haut
            key_rect = QRectF(rect.left() + 4, rect.bottom() - 14, rect.width() - 8, 12)
            painter.drawText(key_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, display_label)

            # Libelle de l'action au-dessus
            font_act = QFont("Segoe UI", 7, QFont.Weight.Normal)
            painter.setFont(font_act)
            painter.setPen(theme["text_action"] if not is_mod_active else QColor("#ffffff"))

            act_label = action_info.get("label", "")
            # Elagage avec ellipse si necessaire
            metrics = QFontMetrics(font_act)
            elided_label = metrics.elidedText(act_label, Qt.TextElideMode.ElideRight, int(rect.width() - 8))

            act_rect = QRectF(rect.left() + 4, rect.top() + 3, rect.width() - 8, rect.height() - 16)
            painter.drawText(act_rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, elided_label)
        else:
            # Touche standard
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, display_label)

        painter.restore()
