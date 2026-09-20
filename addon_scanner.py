# -*- coding: utf-8 -*-
"""
Module de detection et d'extraction avancee des raccourcis des autres add-ons Anki.
- Recherche avancee dans tous les conteneurs Qt (mw, Browser, Editor, Reviewer, etc.)
- Connecteurs specifiques pour l'ecosysteme EDN (mw._edn_registered_modules, AnkiEDNMenu)
- Connecteurs specifiques pour anki_import_diff (gui_hooks, BrowserDiffPanel, etc.)
- Resolution des vrais noms lisibles des extensions via meta.json
- Detection precise de la portee (main, editor, reviewer, browser, toolbar)
- Conservation des references d'objets Qt et cles de configuration pour modification reelle
"""

import os
import json
import re
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
        self.source = source  # "config", "live", "edn", "hook", "static"
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

            # Nettoyage et embellissement du nom si besoin
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
        import re as _re
        if _re.match(r'^F([1-9]|1[0-2])$', val, _re.IGNORECASE):
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
        """Scanne specifiquement les raccourcis de l'ecosysteme Anki EDN."""
        results = []
        # Recuperation du registre partage EDN
        edn_reg = getattr(mw, "_edn_registered_modules", None) if mw else None
        if not edn_reg:
            try:
                from Anki_EDN_Lier_les_cartes.edn_menu import shared_menu
                edn_reg = shared_menu._get_registry()
            except Exception:
                pass

        if isinstance(edn_reg, dict):
            for module_id, mod_info in edn_reg.items():
                mod_name = mod_info.get("name", module_id.replace("_", " ").title())
                friendly_addon = f"Anki EDN ({mod_name})" if "edn" not in mod_name.lower() else f"Anki {mod_name}"

                for act_data in mod_info.get("actions", []):
                    label = act_data.get("label", "Action EDN")
                    scut = act_data.get("shortcut")
                    qact = act_data.get("action")
                    if qact and hasattr(qact, "shortcut"):
                        live_scut = qact.shortcut().toString()
                        if live_scut:
                            scut = live_scut

                    norm = self.normalize_shortcut(scut)
                    if norm:
                        results.append(AddonShortcutItem(
                            addon_id=f"edn_{module_id}",
                            addon_name=friendly_addon,
                            action_name=label,
                            shortcut=norm,
                            source="edn",
                            scope="main",
                            qaction=qact,
                            edn_info={
                                "module_id": module_id,
                                "label": label,
                                "action": qact,
                                "shortcut_key": act_data.get("shortcut_key") or f"{module_id}_{label}"
                            }
                        ))

        # Scan statique en secours si aucun module dynamique n'a ete trouve
        if not results:
            addons_dir = self.get_addons_folder()
            if os.path.isdir(addons_dir):
                for entry in os.listdir(addons_dir):
                    if entry in EXCLUDED_ADDON_IDS or entry.startswith("."):
                        continue
                    addon_path = os.path.join(addons_dir, entry)
                    if not os.path.isdir(addon_path):
                        continue
                    for root, _, files in os.walk(addon_path):
                        for f_name in files:
                            if f_name.endswith(".py"):
                                py_file = os.path.join(root, f_name)
                                try:
                                    with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                                        content = f.read()
                                    if "register_action" in content:
                                        blocks = re.findall(r"register_action\s*\((?:[^)(]+|\((?:[^)(]+|\([^)(]*\))*\))*\)", content)
                                        for b in blocks:
                                            sc_match = re.search(r'shortcut\s*=\s*["\']([^"\']+)["\']', b)
                                            if sc_match:
                                                scut = sc_match.group(1)
                                                norm = self.normalize_shortcut(scut)
                                                if norm:
                                                    mod_m = re.search(r'module_id\s*=\s*["\']([^"\']+)["\']', b)
                                                    mod_id = mod_m.group(1) if mod_m else entry
                                                    lbl_m = re.search(r'label\s*=\s*["\']([^"\']+)["\']', b)
                                                    lbl = lbl_m.group(1) if lbl_m else "Action EDN"
                                                    friendly = self.get_friendly_addon_name(entry)
                                                    results.append(AddonShortcutItem(
                                                        addon_id=f"edn_{mod_id}",
                                                        addon_name=friendly,
                                                        action_name=lbl,
                                                        shortcut=norm,
                                                        source="edn",
                                                        scope="main",
                                                        edn_info={
                                                            "module_id": mod_id,
                                                            "label": lbl,
                                                            "shortcut_key": f"{mod_id}_{lbl}"
                                                        }
                                                    ))
                                except Exception:
                                    pass

        return results

    def scan_diff_and_hook_shortcuts(self):
        """Scanne les raccourcis injectes par anki_import_diff et les hooks GUI."""
        results = []

        # Verification des hooks d'editeur
        try:
            from aqt import gui_hooks
            if hasattr(gui_hooks, "editor_did_init_shortcuts"):
                hooks = getattr(gui_hooks.editor_did_init_shortcuts, "_hooks", [])
                for h in hooks:
                    mod_name = getattr(h, "__module__", "")
                    if "diff" in mod_name.lower():
                        results.append(AddonShortcutItem(
                            addon_id="anki_import_diff",
                            addon_name="Anki Import Diff Review",
                            action_name="Accepter la note modifiée",
                            shortcut="F2",
                            source="hook",
                            scope="editor"
                        ))
                        results.append(AddonShortcutItem(
                            addon_id="anki_import_diff",
                            addon_name="Anki Import Diff Review",
                            action_name="Rejeter la note modifiée",
                            shortcut="F3",
                            source="hook",
                            scope="editor"
                        ))
                        break
        except Exception:
            pass

        # Raccourcis statiques connus de anki_import_diff (Browser & Dialog)
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
            ]
            for scut, act_name, scope in diff_shortcuts:
                results.append(AddonShortcutItem(
                    addon_id="anki_import_diff",
                    addon_name="Anki Import Diff Review",
                    action_name=act_name,
                    shortcut=scut,
                    source="static",
                    scope=scope
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
                        if "editor" in k_lower:
                            scope = "editor"
                        elif "browser" in k_lower:
                            scope = "browser"
                        elif "reviewer" in k_lower or "review" in k_lower:
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
        """Tente d'identifier precisement le nom de l'addon a l'origine d'une QAction."""
        parent_widget = action.parentWidget()
        if isinstance(parent_widget, QMenu):
            title = parent_widget.title().replace("&", "").strip()
            if title == "Anki EDN" or parent_widget.objectName() == "AnkiEDNMenu":
                return "Anki EDN"
            if title and title not in ("Outils", "Fichier", "Édition", "Affichage", "Aide", "Tools", "File", "Edit", "View", "Help"):
                return title

        p = action.parent()
        if p:
            p_name = p.__class__.__name__
            if "EDN" in p_name:
                return "Anki EDN"
            if "Diff" in p_name:
                return "Anki Import Diff Review"

        act_text = action.text().lower()
        if "edn" in act_text:
            return "Anki EDN"
        if "diff" in act_text:
            return "Anki Import Diff Review"

        for entry, meta in self._addon_meta.items():
            name = meta.get("name", "")
            if entry.lower() in act_text or (name and name.lower() in act_text):
                return name

        return "Module complémentaire"

    def _collect_actions_from_widget(self, widget, scope, seen_pairs, results):
        """Scan recursif des QAction et QShortcut dans un widget et ses enfants."""
        for action in widget.findChildren(QAction):
            scut = action.shortcut().toString()
            norm = self.normalize_shortcut(scut)
            if not norm:
                continue
            text = action.text().replace("&", "").strip()
            if not text:
                text = action.objectName() or "Action sans titre"

            addon_name = self._resolve_addon_name_for_action(action)

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

        for qs in widget.findChildren(QShortcut):
            scut = qs.key().toString()
            norm = self.normalize_shortcut(scut)
            if not norm:
                continue
            name = qs.objectName() or f"Raccourci {norm}"

            addon_name = "Module complementaire"
            if "diff" in name.lower():
                addon_name = "Anki Import Diff Review"
            elif "edn" in name.lower():
                addon_name = "Anki EDN"

            pair = (norm.lower(), f"{addon_name}_{name}".lower())
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            results.append(AddonShortcutItem(
                addon_id="live_qt",
                addon_name=addon_name,
                action_name=name,
                shortcut=norm,
                source="live",
                scope=scope,
                qshortcut=qs
            ))

    def scan_live_actions(self, known_shortcuts):
        """Scanne les QAction et QShortcut instancies dans toutes les fenetres actives d'Anki."""
        results = []
        app = QApplication.instance()
        if not app:
            return results

        seen_pairs = set((item.shortcut.lower(), item.action_name.lower()) for item in known_shortcuts)

        # Exclure les raccourcis Anki natifs connus pour eviter les doublons
        anki_native_shortcuts = set()
        try:
            if mw and hasattr(mw, "addonManager") and mw.addonManager:
                cfg = mw.addonManager.getConfig("1762336370") or {}
                for k, v in cfg.items():
                    if isinstance(v, str) and not k.startswith("Omega") and not k.startswith("\u03a9"):
                        norm = self.normalize_shortcut(v)
                        if norm:
                            anki_native_shortcuts.add(norm.lower())
        except Exception:
            pass

        top_widgets = app.topLevelWidgets()
        for widget in top_widgets:
            w_cls = widget.__class__.__name__.lower()
            scope = "main"
            if "browser" in w_cls:
                scope = "browser"
            elif "editor" in w_cls or "addcards" in w_cls or "editcurrent" in w_cls:
                scope = "editor"
            elif "reviewer" in w_cls:
                scope = "reviewer"

            self._collect_actions_from_widget(widget, scope, seen_pairs, results)

        # Scan additionnel : menus de la barre de menus Anki principale
        try:
            if mw and hasattr(mw, "menuBar") and mw.menuBar():
                menu_bar = mw.menuBar()
                for action in menu_bar.actions():
                    menu = action.menu()
                    if menu:
                        self._scan_menu_recursively(menu, seen_pairs, results, anki_native_shortcuts)
        except Exception:
            pass

        return results

    def _scan_menu_recursively(self, menu, seen_pairs, results, anki_native_shortcuts):
        """Scanne recursivement un QMenu et ses sous-menus pour extraire les raccourcis d'addons."""
        parent_title = menu.title().replace("&", "").strip()
        # Ignorer les menus Anki natifs dont on connait les raccourcis
        anki_native_menus = {"Fichier", "Edition", "Affichage", "Aide", "Outils",
                             "File", "Edit", "View", "Help", "Tools"}

        for action in menu.actions():
            if action.isSeparator():
                continue

            sub_menu = action.menu()
            if sub_menu:
                self._scan_menu_recursively(sub_menu, seen_pairs, results, anki_native_shortcuts)
                continue

            scut = action.shortcut().toString()
            norm = self.normalize_shortcut(scut)
            if not norm:
                continue

            # Ne pas re-lister les raccourcis Anki natifs
            if norm.lower() in anki_native_shortcuts:
                continue

            text = action.text().replace("&", "").strip()
            if not text:
                continue

            addon_name = self._resolve_addon_name_for_action(action)
            # Si le menu parent est un menu Anki natif et que l'addon est inconnu,
            # c'est probablement un item Anki injecte par un addon
            if parent_title in anki_native_menus and addon_name == "Module complementaire":
                addon_name = parent_title

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


    def get_all_addon_shortcuts(self):
        """Point d'entree unifie : extrait, harmonise et fusionne tous les raccourcis d'extensions."""
        edn_items = self.scan_edn_shortcuts()
        diff_items = self.scan_diff_and_hook_shortcuts()
        config_items = self.scan_addon_configs()
        
        all_so_far = edn_items + diff_items + config_items
        live_items = self.scan_live_actions(all_so_far)
        all_items = all_so_far + live_items

        unique = []
        seen = set()
        for item in all_items:
            key = (item.addon_name.lower(), item.action_name.lower(), item.shortcut.lower(), item.scope)
            if key not in seen:
                seen.add(key)
                unique.append(item)

        return unique

