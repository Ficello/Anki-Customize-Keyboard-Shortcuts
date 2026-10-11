# -*- coding: utf-8 -*-
"""
Module de detection et d'extraction avancee des raccourcis des autres add-ons Anki.
- Recherche avancee dans tous les conteneurs Qt (mw, Browser, Editor, Reviewer, etc.)
- Connecteurs specifiques pour l'ecosysteme EDN (mw._edn_registered_modules, edn_shared_config.json, shared_menu)
- Connecteurs specifiques pour anki_import_diff (gui_hooks, BrowserDiffPanel, etc.)
- Resolution des vrais noms lisibles des extensions via meta.json
- Detection precise de la portee (main, editor, reviewer, browser, toolbar)
- Conservation des references d'objets Qt et cles de configuration pour modification reelle
"""

import os
import json
import re
import sys
from aqt import mw
from aqt.qt import *

SHORTCUT_REGEX = re.compile(
    r"^(?:(?:Ctrl|Alt|Shift|Maj|Meta)\+)*(?:[A-Za-z0-9]|F[1-9]|F1[0-2]|Space|Return|Enter|Tab|Backspace|Delete|Insert|Home|End|PageUp|PageDown|Left|Right|Up|Down|Esc|Escape|[+\-=\[\]\\;',./`])$",
    re.IGNORECASE
)

EXCLUDED_ADDON_IDS = {
    "1762336370",
    "24411424",
    ".agents",
    "agents",
    "__pycache__"
}

ANKI_CORE_PREFIXES = ("main ", "editor ", "reviewer ", "window_browser ", "m_toolbox ")

class AddonShortcutItem:
    def __init__(self, addon_id, addon_name, action_name, shortcut, source="config", scope="main", 
                 qaction=None, qshortcut=None, config_key=None, edn_info=None):
        self.addon_id = str(addon_id)
        self.addon_name = addon_name
        self.action_name = action_name
        self.shortcut = shortcut
        self.source = source  # "config", "live", "edn", "hook", "static", "code"
        self.scope = scope    # "main", "editor", "reviewer", "browser", "toolbar"
        self.qaction = qaction
        self.qshortcut = qshortcut
        self.config_key = config_key
        self.edn_info = edn_info

    def to_dict(self):
        return {
            "addon_id": self.addon_id,
            "addon_name": self.addon_name,
            "action_name": self.action_name,
            "shortcut": self.shortcut,
            "source": self.source,
            "scope": self.scope
        }

class AddonScanner:
    def __init__(self, current_addon_id="1762336370"):
        self.current_addon_id = current_addon_id
        self._addon_meta = {}
        self._load_addon_metadata()

    def get_addons_folder(self):
        """Localise le repertoire addons21 d'Anki."""
        try:
            if mw and hasattr(mw, "addonManager") and hasattr(mw.addonManager, "addonsFolder"):
                return mw.addonManager.addonsFolder()
        except Exception:
            pass
        return os.path.expandvars(r"%APPDATA%\Anki2\addons21")

    def get_edn_shared_config(self):
        """Recupere la configuration partagee EDN (edn_shared_config.json) du profil actif."""
        try:
            if mw and hasattr(mw, "pm") and mw.pm and hasattr(mw.pm, "name") and mw.pm.name:
                p = os.path.join(mw.pm.profileFolder(), "edn_shared_config.json")
                if os.path.isfile(p):
                    with open(p, "r", encoding="utf-8") as f:
                        return json.load(f), p
        except Exception:
            pass

        # Recherche de secours dans les profils Anki2
        appdata = os.path.expandvars(r"%APPDATA%\Anki2")
        if os.path.isdir(appdata):
            for entry in os.listdir(appdata):
                p = os.path.join(appdata, entry, "edn_shared_config.json")
                if os.path.isfile(p):
                    try:
                        with open(p, "r", encoding="utf-8") as f:
                            return json.load(f), p
                    except Exception:
                        pass
        return {}, None

    def save_edn_shortcut(self, shortcut_key, shortcut_value):
        """Sauvegarde un raccourci EDN a la fois en memoire et dans edn_shared_config.json."""
        # 1. Mise a jour via shared_menu si present en memoire
        for mod_name, mod in list(sys.modules.items()):
            if "shared_menu" in mod_name and hasattr(mod, "set_shortcut"):
                try:
                    mod.set_shortcut(shortcut_key, shortcut_value)
                    break
                except Exception:
                    pass

        # 2. Persistance directe dans le fichier edn_shared_config.json du profil
        _, cfg_path = self.get_edn_shared_config()
        if not cfg_path and mw and hasattr(mw, "pm") and mw.pm and getattr(mw.pm, "name", None):
            cfg_path = os.path.join(mw.pm.profileFolder(), "edn_shared_config.json")

        if cfg_path:
            try:
                cfg = {}
                if os.path.isfile(cfg_path):
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                if not isinstance(cfg, dict):
                    cfg = {}
                if "shortcuts" not in cfg or not isinstance(cfg["shortcuts"], dict):
                    cfg["shortcuts"] = {}
                cfg["shortcuts"][shortcut_key] = shortcut_value
                with open(cfg_path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

        # 3. Mise a jour immediate des raccourcis actifs sur les fenetres du browser
        try:
            from aqt import dialogs
            from aqt.qt import QKeySequence
            browser_dlg = dialogs._dialogs.get("Browser")
            if browser_dlg and isinstance(browser_dlg, tuple):
                browser = browser_dlg[1]
                if browser:
                    attr_map = {
                        "linked_cards_copy": ("_edn_sc_copy", "_edn_sc_copy_editor"),
                        "linked_cards_search": ("_edn_sc_search", "_edn_sc_search_editor"),
                        "linked_cards_liens": ("_edn_sc_liens", "_edn_sc_liens_editor")
                    }
                    if shortcut_key in attr_map:
                        seq = QKeySequence(shortcut_value if shortcut_value != "<nop>" else "")
                        for attr in attr_map[shortcut_key]:
                            sc = getattr(browser, attr, None)
                            if sc and hasattr(sc, "setKey"):
                                sc.setKey(seq)
        except Exception:
            pass

    def _load_addon_metadata(self):
        """Charge les metadonnees et noms lisibles de tous les addons installes."""
        self._addon_meta.clear()
        addons_dir = self.get_addons_folder()
        if not os.path.isdir(addons_dir):
            return

        for entry in os.listdir(addons_dir):
            if entry in EXCLUDED_ADDON_IDS or entry.startswith("."):
                continue
            addon_path = os.path.join(addons_dir, entry)
            if not os.path.isdir(addon_path):
                continue

            meta_path = os.path.join(addon_path, "meta.json")
            name = entry
            is_disabled = False
            if os.path.isfile(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        name = meta.get("name") or entry
                        is_disabled = meta.get("disabled", False)
                except Exception:
                    pass

            if name == entry:
                clean_name = entry.replace("_", " ").replace("-", " ")
                if "edn" in clean_name.lower():
                    clean_name = clean_name.replace("Anki EDN", "Anki EDN").replace("edn", "EDN")
                name = clean_name.title()

            self._addon_meta[entry] = {
                "name": name,
                "disabled": is_disabled,
                "path": addon_path
            }

    def get_friendly_addon_name(self, addon_id):
        meta = self._addon_meta.get(str(addon_id))
        if meta and meta.get("name"):
            return meta["name"]
        clean = str(addon_id).replace("_", " ").replace("-", " ")
        if "edn" in clean.lower():
            clean = clean.replace("edn", "EDN")
        return clean.title()

    def normalize_shortcut(self, scut):
        if not scut or not isinstance(scut, str):
            return ""
        s = scut.strip()
        if s.lower() in ("<nop>", "none", "", "null", "<default>"):
            return ""
        s = s.replace("Qt.Key_Return", "Return").replace("Qt.Key_Enter", "Enter")
        s = s.replace("Qt.Key_Space", "Space").replace("Qt.Key_Tab", "Tab")
        s = s.replace("Qt.Key_Escape", "Esc").replace("Qt.Key_Delete", "Del")
        s = s.replace("Control", "Ctrl")
        return s

    def is_plausible_shortcut(self, key_name, value):
        if not isinstance(value, str):
            return False
        val = value.strip()
        if not val or val.lower() in ("<nop>", "none", "false", "true", "<default>"):
            return False

        kn = key_name.lower()
        has_scut_name = any(word in kn for word in (
            "shortcut", "hotkey", "scut", "accel", "key", "raccourci", "touche", "keybind"
        ))

        if len(val) > 25:
            return False

        # Raccourci compose (Ctrl+X, Alt+F4, etc.)
        if "+" in val:
            return True

        # Touches fonctions
        if re.match(r'^F([1-9]|1[0-2])$', val, re.IGNORECASE):
            return True

        # Touche speciale connue
        special = {"space", "return", "enter", "tab", "backspace", "delete", "del",
                   "insert", "ins", "home", "end", "pageup", "pagedown", "pgup", "pgdn",
                   "up", "down", "left", "right", "escape", "esc"}
        if val.lower() in special:
            return True

        # Caractere alphanum seul avec cle dont le nom suggere un raccourci
        if has_scut_name and len(val) == 1 and (val.isalpha() or val.isdigit()):
            return True

        return False

    def scan_edn_shortcuts(self):
        """Scanne exhaustivement les raccourcis de l'ecosysteme Anki EDN (dynamique, config et statique)."""
        results = []
        edn_cfg, _ = self.get_edn_shared_config()
        edn_saved_scuts = edn_cfg.get("shortcuts", {}) if isinstance(edn_cfg, dict) else {}

        # 1. Recuperation via registre dynamique (mw._edn_registered_modules)
        edn_reg = getattr(mw, "_edn_registered_modules", None) if mw else None
        if not edn_reg:
            for mod_name, mod in list(sys.modules.items()):
                if "shared_menu" in mod_name and hasattr(mod, "_get_registry"):
                    try:
                        edn_reg = mod._get_registry()
                        break
                    except Exception:
                        pass

        handled_keys = set()

        if isinstance(edn_reg, dict):
            for module_id, mod_info in edn_reg.items():
                mod_name = mod_info.get("name", module_id.replace("_", " ").title())
                friendly_addon = f"Anki EDN ({mod_name})" if "edn" not in mod_name.lower() else f"Anki {mod_name}"

                for act_data in mod_info.get("actions", []):
                    label = act_data.get("label", "Action EDN")
                    shortcut_key = act_data.get("shortcut_key") or f"{module_id}_{label}"
                    handled_keys.add(shortcut_key)

                    scut = edn_saved_scuts.get(shortcut_key, act_data.get("shortcut"))
                    qact = act_data.get("action")
                    if qact and hasattr(qact, "shortcut"):
                        try:
                            live_scut = qact.shortcut().toString()
                            if live_scut:
                                scut = live_scut
                        except Exception:
                            pass

                    norm = self.normalize_shortcut(scut)
                    if not norm:
                        continue

                    scope = "main"
                    sk_lower = f"{module_id}_{shortcut_key}_{label}".lower()
                    if any(w in sk_lower for w in ("search", "copy", "lien", "gui", "browser")):
                        scope = "browser"
                    elif any(w in sk_lower for w in ("open", "preview", "navigate", "back", "suivant", "apercu", "retour", "reviewer")):
                        scope = "reviewer"

                    results.append(AddonShortcutItem(
                        addon_id=f"edn_{module_id}",
                        addon_name=friendly_addon,
                        action_name=label,
                        shortcut=norm,
                        source="edn",
                        scope=scope,
                        qaction=qact,
                        edn_info={
                            "module_id": module_id,
                            "label": label,
                            "action": qact,
                            "shortcut_key": shortcut_key
                        }
                    ))

        # 2. Addons EDN connus installes dans addons21
        addons_dir = self.get_addons_folder()
        known_edn = [
            {
                "folder": "Anki_EDN_Lier_les_cartes",
                "module_id": "linked_cards",
                "addon_name": "Anki EDN (Lier les cartes)",
                "actions": [
                    {"label": "Rechercher des liens (GUI)", "shortcut_key": "linked_cards_search", "default": "Ctrl+Alt+L", "scope": "browser"},
                    {"label": "Copier NID", "shortcut_key": "linked_cards_copy", "default": "Ctrl+Alt+C", "scope": "browser"},
                    {"label": "Afficher / masquer volet Liens", "shortcut_key": "linked_cards_liens", "default": "Ctrl+Alt+B", "scope": "browser"},
                    {"label": "Suivant (carte liée)", "shortcut_key": "linked_cards_kbd_open", "default": "n", "scope": "reviewer"},
                    {"label": "Aperçu de la carte liée", "shortcut_key": "linked_cards_kbd_preview", "default": "p", "scope": "reviewer"},
                    {"label": "Aperçu étendu de la carte liée", "shortcut_key": "linked_cards_kbd_navigate", "default": "r", "scope": "reviewer"},
                    {"label": "Retour à la carte précédente", "shortcut_key": "linked_cards_kbd_back", "default": "z", "scope": "reviewer"},
                ]
            },
            {
                "folder": "Anki_EDN_Stats",
                "module_id": "edn_progress",
                "addon_name": "Anki EDN (Stats)",
                "actions": [
                    {"label": "Statistiques EDN", "shortcut_key": "edn_progress_stat", "default": "Ctrl+U", "scope": "main"}
                ]
            },
            {
                "folder": "Anki_EDN_Media_References",
                "module_id": "anki_edn_media_refs",
                "addon_name": "Anki EDN (Références Médias)",
                "actions": [
                    {"label": "Ouvrir dossier média", "shortcut_key": "edn_media_refs_browser", "default": "Ctrl+Shift+E", "scope": "browser"}
                ]
            }
        ]

        for mod_def in known_edn:
            folder_path = os.path.join(addons_dir, mod_def["folder"])
            if not os.path.isdir(folder_path):
                continue
            meta = self._addon_meta.get(mod_def["folder"])
            if meta and meta.get("disabled"):
                continue

            for act in mod_def["actions"]:
                sk = act["shortcut_key"]
                if sk in handled_keys:
                    continue
                handled_keys.add(sk)

                current_scut = edn_saved_scuts.get(sk, act["default"])
                norm = self.normalize_shortcut(current_scut)
                if norm:
                    results.append(AddonShortcutItem(
                        addon_id=f"edn_{mod_def['module_id']}",
                        addon_name=mod_def["addon_name"],
                        action_name=act["label"],
                        shortcut=norm,
                        source="edn",
                        scope=act["scope"],
                        edn_info={
                            "module_id": mod_def["module_id"],
                            "label": act["label"],
                            "shortcut_key": sk
                        }
                    ))

        return results

    def scan_diff_and_hook_shortcuts(self):
        """Scanne les raccourcis injectes par anki_import_diff et les hooks GUI."""
        results = []
        addons_dir = self.get_addons_folder()
        diff_dir = os.path.join(addons_dir, "anki_import_diff")
        if os.path.isdir(diff_dir):
            diff_shortcuts = [
                ("F2", "Accepter tous les champs", "browser"),
                ("Alt+A", "Accepter tous les champs (Alt+A)", "browser"),
                ("F3", "Rejeter tous les champs", "browser"),
                ("Alt+R", "Rejeter tous les champs (Alt+R)", "browser"),
                ("Alt+H", "Basculer vers l'onglet Historique", "browser"),
                ("Alt+C", "Copier les anciens champs de la note", "browser"),
                ("F2", "Accepter la note modifiée", "editor"),
                ("F3", "Rejeter la note modifiée", "editor"),
            ]
            for scut, act_name, scope in diff_shortcuts:
                results.append(AddonShortcutItem(
                    addon_id="anki_import_diff",
                    addon_name="Anki Import Diff Review",
                    action_name=act_name,
                    shortcut=scut,
                    source="hook" if scope == "editor" else "static",
                    scope=scope
                ))
        return results

    def scan_code_shortcuts(self):
        """Scanne les raccourcis definis directement dans le code Python d'addons sans config.json."""
        results = []
        addons_dir = self.get_addons_folder()
        
        # FocusForce
        ff_dir = os.path.join(addons_dir, "1356589749")
        if os.path.isdir(ff_dir):
            meta = self._addon_meta.get("1356589749")
            if not meta or not meta.get("disabled"):
                results.append(AddonShortcutItem(
                    addon_id="1356589749",
                    addon_name=self.get_friendly_addon_name("1356589749"),
                    action_name="Activer / Désactiver FocusForce",
                    shortcut="Ctrl+Shift+L",
                    source="code",
                    scope="main"
                ))

        # Find and Replace in Templates
        fr_dir = os.path.join(addons_dir, "992153575")
        if os.path.isdir(fr_dir):
            meta = self._addon_meta.get("992153575")
            if not meta or not meta.get("disabled"):
                results.append(AddonShortcutItem(
                    addon_id="992153575",
                    addon_name=self.get_friendly_addon_name("992153575"),
                    action_name="Rechercher et remplacer dans les modèles",
                    shortcut="Ctrl+Alt+T",
                    source="code",
                    scope="browser"
                ))

        return results

    def scan_addon_configs(self):
        """Analyse les fichiers config.json et meta.json des addons installes."""
        results = []
        addons_dir = self.get_addons_folder()
        if not os.path.isdir(addons_dir):
            return results

        for entry, meta in self._addon_meta.items():
            if meta.get("disabled"):
                continue

            addon_path = meta.get("path")
            config_path = os.path.join(addon_path, "config.json")
            if not os.path.isfile(config_path):
                continue

            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self._extract_shortcuts_from_dict(entry, meta["name"], cfg, results)
            except Exception:
                pass

        return results

    def _extract_shortcuts_from_dict(self, addon_id, addon_name, data, results, prefix=""):
        if not isinstance(data, dict):
            return
        for k, v in data.items():
            full_key = f"{prefix} {k}".strip() if prefix else k
            if isinstance(v, dict):
                self._extract_shortcuts_from_dict(addon_id, addon_name, v, results, full_key)
            elif isinstance(v, str):
                if self.is_plausible_shortcut(full_key, v):
                    norm = self.normalize_shortcut(v)
                    if norm:
                        scope = "main"
                        k_lower = full_key.lower()
                        if "editor" in k_lower or addon_id == "183246496":
                            scope = "editor"
                        elif "browser" in k_lower:
                            scope = "browser"
                        elif "reviewer" in k_lower or "review" in k_lower or addon_id == "1046608507":
                            scope = "reviewer"
                        elif "tool" in k_lower or "menu" in k_lower:
                            scope = "toolbar"

                        results.append(AddonShortcutItem(
                            addon_id=addon_id,
                            addon_name=addon_name,
                            action_name=full_key.replace("_", " ").title(),
                            shortcut=norm,
                            source="config",
                            scope=scope,
                            config_key=k
                        ))

    def _resolve_addon_name_for_action(self, action):
        """Tente d'identifier precisement le nom de l'addon a l'origine d'une QAction de maniere securisee (Qt5 et Qt6)."""
        try:
            parent = getattr(action, "parentWidget", None)
            if callable(parent):
                try:
                    parent = parent()
                except Exception:
                    parent = None
            if not parent and hasattr(action, "parent"):
                try:
                    parent = action.parent()
                except Exception:
                    parent = None

            if isinstance(parent, QMenu):
                title = parent.title().replace("&", "").strip()
                if title == "Anki EDN" or parent.objectName() == "AnkiEDNMenu":
                    return "Anki EDN"
                if title and title not in ("Outils", "Fichier", "Édition", "Affichage", "Aide", "Tools", "File", "Edit", "View", "Help"):
                    return title

            if hasattr(action, "associatedObjects"):
                try:
                    for obj in action.associatedObjects():
                        if isinstance(obj, QMenu):
                            t = obj.title().replace("&", "").strip()
                            if t == "Anki EDN" or obj.objectName() == "AnkiEDNMenu":
                                return "Anki EDN"
                            if t and t not in ("Outils", "Fichier", "Édition", "Affichage", "Aide", "Tools", "File", "Edit", "View", "Help"):
                                return t
                except Exception:
                    pass

            if parent:
                p_name = parent.__class__.__name__
                if "EDN" in p_name:
                    return "Anki EDN"
                if "Diff" in p_name:
                    return "Anki Import Diff Review"

            act_text = ""
            try:
                act_text = action.text().lower()
            except Exception:
                pass

            if "edn" in act_text:
                return "Anki EDN"
            if "diff" in act_text:
                return "Anki Import Diff Review"

            for entry, meta in self._addon_meta.items():
                name = meta.get("name", "")
                if entry.lower() in act_text or (name and name.lower() in act_text):
                    return name

            return "Module complémentaire"
        except Exception:
            return "Module complémentaire"

    def _resolve_addon_name_for_qshortcut(self, qs, obj_name=""):
        """Tente d'identifier le nom de l'addon a l'origine d'un QShortcut."""
        name_lower = obj_name.lower()
        # Correspondances rapides sur le nom de l'objet
        if "diff" in name_lower:
            return "Anki Import Diff Review"
        if "edn" in name_lower:
            return "Anki EDN"

        # Remonter la chaîne de parents widgets pour trouver un titre de fenêtre
        try:
            parent = qs.parent() if hasattr(qs, "parent") else None
            depth = 0
            while parent is not None and depth < 8:
                depth += 1
                cls_name = parent.__class__.__name__
                if "EDN" in cls_name or "edn" in cls_name.lower():
                    return "Anki EDN"
                if "Diff" in cls_name or "diff" in cls_name.lower():
                    return "Anki Import Diff Review"
                # Fenêtre avec un titre exploitable
                if hasattr(parent, "windowTitle"):
                    try:
                        title = parent.windowTitle().strip()
                        if title and title not in ("Anki", "", "Main Window"):
                            # Chercher dans les métadonnées d'addons
                            title_lower = title.lower()
                            for entry, meta in self._addon_meta.items():
                                m_name = meta.get("name", "")
                                if m_name and (m_name.lower() in title_lower or title_lower in m_name.lower()):
                                    return m_name
                            return title
                    except Exception:
                        pass
                # QMenu avec un titre d'addon
                if isinstance(parent, QMenu):
                    try:
                        t = parent.title().replace("&", "").strip()
                        if t and t not in ("Outils", "Fichier", "Édition", "Affichage", "Aide",
                                           "Tools", "File", "Edit", "View", "Help"):
                            return t
                    except Exception:
                        pass
                try:
                    parent = parent.parent()
                except Exception:
                    break
        except Exception:
            pass

        # Correspondance sur le nom de l'objet dans les métadonnées
        for entry, meta in self._addon_meta.items():
            m_name = meta.get("name", "")
            if m_name and (entry.lower() in name_lower or (m_name and m_name.lower() in name_lower)):
                return m_name

        return "Module complémentaire"

    def _collect_actions_from_widget(self, widget, scope, seen_pairs, results):
        """Scan securise des QAction instanciees appartenant a un addon tiers identifie."""
        try:
            actions = widget.findChildren(QAction)
        except Exception:
            actions = []

        _forbidden_names = {
            "module complémentaire", "fichier", "file", "outils", "tools",
            "affichage", "view", "aide", "help", "édition", "edit",
            "utilisateur 1 - anki", "anki", "main window", "action sans titre"
        }

        for action in actions:
            try:
                scut = action.shortcut().toString()
                norm = self.normalize_shortcut(scut)
                if not norm:
                    continue
                text = action.text().replace("&", "").strip()
                if not text:
                    text = action.objectName() or ""
                if not text:
                    continue

                addon_name = self._resolve_addon_name_for_action(action)
                if not addon_name or addon_name.lower() in _forbidden_names or addon_name.lower().endswith(" - anki"):
                    continue

                pair = (norm.lower(), f"{addon_name}_{text}".lower())
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)

                results.append(AddonShortcutItem(
                    addon_id="live_qt",
                    addon_name=addon_name,
                    action_name=text,
                    shortcut=norm,
                    source="live",
                    scope=scope,
                    qaction=action
                ))
            except Exception:
                continue

    def scan_live_actions(self, known_shortcuts):
        """Scanne les QAction et QShortcut instancies dans toutes les fenetres actives d'Anki."""
        results = []
        try:
            app = QApplication.instance()
            if not app:
                return results

            seen_pairs = set((item.shortcut.lower(), item.action_name.lower()) for item in known_shortcuts)

            top_widgets = app.topLevelWidgets()
            for widget in top_widgets:
                try:
                    w_cls = widget.__class__.__name__.lower()
                    scope = "main"
                    if "browser" in w_cls:
                        scope = "browser"
                    elif "editor" in w_cls or "addcards" in w_cls or "editcurrent" in w_cls:
                        scope = "editor"
                    elif "reviewer" in w_cls:
                        scope = "reviewer"

                    self._collect_actions_from_widget(widget, scope, seen_pairs, results)
                except Exception:
                    continue

            # Scan additionnel : menus de la barre de menus Anki principale
            try:
                if mw and hasattr(mw, "menuBar") and mw.menuBar():
                    menu_bar = mw.menuBar()
                    for action in menu_bar.actions():
                        menu = action.menu()
                        if menu:
                            self._scan_menu_recursively(menu, seen_pairs, results)
            except Exception:
                pass
        except Exception:
            pass

        return results

    def _scan_menu_recursively(self, menu, seen_pairs, results):
        """Scanne recursivement un QMenu et ses sous-menus pour extraire les raccourcis d'addons."""
        try:
            parent_title = menu.title().replace("&", "").strip()
        except Exception:
            parent_title = ""

        anki_native_menus = {"Fichier", "Edition", "Affichage", "Aide", "Outils",
                             "File", "Edit", "View", "Help", "Tools"}

        try:
            actions = menu.actions()
        except Exception:
            return

        for action in actions:
            try:
                if action.isSeparator():
                    continue

                sub_menu = action.menu()
                if sub_menu:
                    self._scan_menu_recursively(sub_menu, seen_pairs, results)
                    continue

                scut = action.shortcut().toString()
                norm = self.normalize_shortcut(scut)
                if not norm:
                    continue

                text = action.text().replace("&", "").strip()
                if not text:
                    continue

                addon_name = self._resolve_addon_name_for_action(action)
                # Si l'action appartient a un menu natif Anki et qu'aucun addon tiers n'est formellement identifie, l'ignorer
                if not addon_name or addon_name in anki_native_menus or addon_name == "Module complémentaire":
                    continue
                if parent_title in anki_native_menus and (addon_name in anki_native_menus or addon_name == parent_title):
                    continue
                if addon_name.lower().endswith(" - anki"):
                    continue

                pair = (norm.lower(), f"{addon_name}_{text}".lower())
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)

                results.append(AddonShortcutItem(
                    addon_id="live_qt",
                    addon_name=addon_name,
                    action_name=text,
                    shortcut=norm,
                    source="live",
                    scope="main",
                    qaction=action
                ))
            except Exception:
                continue

    def get_all_addon_shortcuts(self):
        """Point d'entree unifie : extrait, harmonise et fusionne tous les raccourcis d'extensions."""
        try:
            edn_items = self.scan_edn_shortcuts()
        except Exception as e:
            print(f"[AddonScanner] Erreur scan_edn_shortcuts: {e}")
            edn_items = []

        try:
            diff_items = self.scan_diff_and_hook_shortcuts()
        except Exception as e:
            print(f"[AddonScanner] Erreur scan_diff_and_hook_shortcuts: {e}")
            diff_items = []

        try:
            code_items = self.scan_code_shortcuts()
        except Exception as e:
            print(f"[AddonScanner] Erreur scan_code_shortcuts: {e}")
            code_items = []

        try:
            config_items = self.scan_addon_configs()
        except Exception as e:
            print(f"[AddonScanner] Erreur scan_addon_configs: {e}")
            config_items = []

        all_so_far = edn_items + diff_items + code_items + config_items

        try:
            live_items = self.scan_live_actions(all_so_far)
        except Exception as e:
            print(f"[AddonScanner] Erreur scan_live_actions: {e}")
            live_items = []

        all_items = all_so_far + live_items

        unique = []
        seen = set()
        for item in all_items:
            key = (item.addon_name.lower(), item.action_name.lower(), item.shortcut.lower(), item.scope)
            if key not in seen:
                seen.add(key)
                unique.append(item)

        return unique
