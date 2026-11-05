# -*- coding: utf-8 -*-
"""
ShortcutBroker - Moteur d'allocation intelligente et d'arbitrage de raccourcis clavier pour Anki.
Expose `mw.shortcut_broker` pour permettre aux add-ons tiers de :
1. Consulter en direct les touches occupées dans la session active de l'utilisateur.
2. Vérifier la disponibilité d'une combinaison (`is_free`).
3. Obtenir des alternatives viables sans collision (`suggest_alternative`).
4. Réclamer et enregistrer dynamiquement un raccourci avec support du Hot-Reload (`claim`).
5. Auto-résoudre proactivement les conflits avec notification unique post-détection.
"""

import os
import sys
import json
import re
from typing import Dict, List, Optional, Set, Tuple, Callable, Any
from aqt import mw, gui_hooks
from aqt.qt import QKeySequence, QTimer
from aqt.utils import tooltip

MODIFIER_ORDER = ["Ctrl", "Alt", "Shift", "Meta"]

def normalize_key_str(scut: str) -> str:
    """Normalise une chaîne de raccourci (ex: 'ctrl + shift + a' -> 'Ctrl+Shift+A')."""
    if not scut or not isinstance(scut, str):
        return ""
    s = scut.strip()
    if s.lower() in ("<nop>", "none", "null", "<default>", "false", "true", ""):
        return ""
    
    # Remplacements de touches spéciales Qt
    s = s.replace("Qt.Key_Return", "Return").replace("Qt.Key_Enter", "Enter")
    s = s.replace("Qt.Key_Space", "Space").replace("Qt.Key_Tab", "Tab")
    s = s.replace("Qt.Key_Escape", "Esc").replace("Qt.Key_Delete", "Del")
    s = s.replace("Control", "Ctrl").replace("Option", "Alt").replace("Command", "Meta")
    s = s.replace("Maj", "Shift")

    parts = [p.strip() for p in s.split("+") if p.strip()]
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
            base = p.upper()
    
    # Tri canonique des modificateurs
    sorted_mods = [m for m in MODIFIER_ORDER if m in mods]
    if base:
        return "+".join(sorted_mods + [base]) if sorted_mods else base
    return "+".join(sorted_mods)


class ShortcutClaim:
    """Représentation d'une action revendiquée par un add-on tiers ou enregistrée statiquement."""
    def __init__(self, action_id: str, label: str, scope: str, current_key: str,
                 default_key: str = "", fallbacks: Optional[List[str]] = None,
                 on_change: Optional[Callable[[str], None]] = None,
                 addon_id: str = "", addon_name: str = "", config_key: str = ""):
        self.action_id = action_id
        self.label = label
        self.scope = scope  # "main", "editor", "reviewer", "browser", "toolbar", "global"
        self.current_key = normalize_key_str(current_key)
        self.default_key = normalize_key_str(default_key or current_key)
        self.fallbacks = [normalize_key_str(f) for f in (fallbacks or []) if normalize_key_str(f)]
        self.on_change = on_change
        self.addon_id = addon_id
        self.addon_name = addon_name or addon_id
        self.config_key = config_key

    def to_dict(self) -> dict:
        return {
            "action_id": self.action_id,
            "label": self.label,
            "scope": self.scope,
            "current_key": self.current_key,
            "default_key": self.default_key,
            "fallbacks": self.fallbacks,
            "addon_id": self.addon_id,
            "addon_name": self.addon_name,
            "config_key": self.config_key
        }


class ShortcutBroker:
    """
    Arbitre centralisé des raccourcis Anki et add-ons tiers.
    Singleton accessible via `mw.shortcut_broker`.
    """
    _instance = None

    def __init__(self):
        self.claims: Dict[str, ShortcutClaim] = {}
        self._static_manifests_loaded = False
        self._resolution_log: List[Dict[str, str]] = []

    @classmethod
    def get_instance(cls) -> "ShortcutBroker":
        if cls._instance is None:
            cls._instance = ShortcutBroker()
        return cls._instance

    def _get_addon_config(self) -> dict:
        try:
            if mw and hasattr(mw, "addonManager") and mw.addonManager:
                cfg = mw.addonManager.getConfig("1762336370")
                if isinstance(cfg, dict):
                    return cfg
        except Exception:
            pass
        return {}

    def _save_addon_config(self, cfg: dict):
        try:
            if mw and hasattr(mw, "addonManager") and mw.addonManager:
                mw.addonManager.writeConfig("1762336370", cfg)
        except Exception:
            pass

    def get_occupied(self, scope: str = "all", include_global: bool = True) -> Dict[str, List[Dict[str, str]]]:
        """
        Retourne la carte exhaustive de toutes les touches actuellement occupées dans la session de l'utilisateur.
        Résultat sous la forme : { "Ctrl+Alt+C": [ {"owner": "Anki EDN", "action": "Copier NID", "scope": "browser"} ] }
        """
        occupied: Dict[str, List[Dict[str, str]]] = {}

        def _add(scut: str, owner: str, action: str, sc_scope: str):
            norm = normalize_key_str(scut)
            if not norm:
                return
            if norm not in occupied:
                occupied[norm] = []
            occupied[norm].append({
                "owner": owner,
                "action": action,
                "scope": sc_scope
            })

        # 1. Raccourcis natifs Anki configurés dans 1762336370
        cfg = self._get_addon_config()
        if cfg:
            for k, v in cfg.items():
                if isinstance(v, str) and not k.startswith("Ω") and k not in ("interface_language", "addon_shortcuts_overrides", "config_file_path"):
                    sc_scope = "toolbar"
                    if k.startswith("main "):
                        sc_scope = "main"
                    elif k.startswith("editor "):
                        sc_scope = "editor"
                    elif k.startswith("reviewer "):
                        sc_scope = "reviewer"
                    elif k.startswith("window_browser "):
                        sc_scope = "browser"

                    if scope in ("all", sc_scope) or (include_global and sc_scope in ("main", "toolbar")):
                        _add(v, "Anki Natif", k, sc_scope)

        # 2. Addons déclarés via claims
        for claim in self.claims.values():
            if not claim.current_key:
                continue
            if scope in ("all", claim.scope) or (include_global and claim.scope in ("main", "toolbar", "global")):
                _add(claim.current_key, claim.addon_name, claim.label, claim.scope)

        # 3. Addons tiers connus via le scanner
        try:
            from .addon_scanner import AddonScanner
            scanner = AddonScanner(current_addon_id="1762336370")
            overrides = cfg.get("addon_shortcuts_overrides", {})
            for item in scanner.get_all_addon_shortcuts():
                sk = item.edn_info.get("shortcut_key") if item.edn_info else None
                name_key = f"{item.addon_name}_{item.action_name}"
                id_key = f"{item.addon_id}_{item.action_name}"
                curr = (overrides.get(sk) if sk else None) or overrides.get(name_key) or overrides.get(id_key) or item.shortcut
                
                if scope in ("all", item.scope) or (include_global and item.scope in ("main", "toolbar", "global")):
                    _add(curr, item.addon_name, item.action_name, item.scope)
        except Exception:
            pass

        return occupied

    def is_free(self, shortcut: str, scope: str = "all", exclude_action_id: Optional[str] = None) -> bool:
        """Indique si un raccourci est parfaitement libre dans le contexte donné."""
        norm = normalize_key_str(shortcut)
        if not norm:
            return True
        occupied = self.get_occupied(scope=scope, include_global=True)
        if norm not in occupied:
            return True
        
        # Si la seule occupation est notre propre action_id, alors la touche est libre
        owners = occupied[norm]
        if exclude_action_id:
            owners = [o for o in owners if o.get("action") != exclude_action_id]
        return len(owners) == 0

    def suggest_alternative(self, preferred: List[str], scope: str = "main", exclude_action_id: Optional[str] = None) -> str:
        """
        Trouve le meilleur raccourci libre parmi une liste de candidats préférés,
        ou génère une combinaison ergonomique disponible (Alt+Key, Ctrl+Alt+Key, Ctrl+Shift+Key).
        """
        # 1. Tester les préférences explicites du développeur
        for cand in preferred:
            norm = normalize_key_str(cand)
            if norm and self.is_free(norm, scope=scope, exclude_action_id=exclude_action_id):
                return norm

        # 2. Si aucune n'est libre, dériver à partir de la première préférence
        first = preferred[0] if preferred else "F10"
        parts = [p.strip() for p in first.split("+") if p.strip()]
        base_key = parts[-1].upper() if parts else "F10"

        candidate_patterns = [
            f"Alt+{base_key}",
            f"Ctrl+Alt+{base_key}",
            f"Ctrl+Shift+{base_key}",
            f"Shift+Alt+{base_key}",
            f"Ctrl+Shift+Alt+{base_key}"
        ]

        for cand in candidate_patterns:
            norm = normalize_key_str(cand)
            if self.is_free(norm, scope=scope, exclude_action_id=exclude_action_id):
                return norm

        # Touches fonctions de secours
        for f_idx in range(2, 13):
            cand = f"F{f_idx}"
            if self.is_free(cand, scope=scope, exclude_action_id=exclude_action_id):
                return cand

        return ""

    def claim(self, action_id: str, label: str, scope: str, preferred: List[str],
              on_change: Optional[Callable[[str], None]] = None,
              addon_id: str = "", addon_name: str = "", config_key: str = "") -> str:
        """
        Enregistre une action par un add-on tiers.
        - Vérifie si l'utilisateur l'a déjà personnalisée (overrides ou edn_shared_config).
        - Si non, alloue le 1er choix libre ou une alternative automatique sans conflit.
        - Met en cache le claim et attache le callback `on_change` pour le Hot-Reload.
        """
        norm_prefs = [normalize_key_str(p) for p in preferred if normalize_key_str(p)]
        default_choice = norm_prefs[0] if norm_prefs else ""
        fallbacks = norm_prefs[1:] if len(norm_prefs) > 1 else []

        cfg = self._get_addon_config()
        overrides = cfg.get("addon_shortcuts_overrides", {})

        # Recherche d'un override utilisateur existant
        user_scut = None
        for test_key in (action_id, f"{addon_name}_{label}", f"{addon_id}_{label}"):
            if test_key in overrides:
                user_scut = overrides[test_key]
                break

        if user_scut is not None:
            effective_key = normalize_key_str(user_scut)
        else:
            # Allocation automatique de la première touche libre
            if self.is_free(default_choice, scope=scope, exclude_action_id=action_id):
                effective_key = default_choice
            else:
                effective_key = self.suggest_alternative(norm_prefs, scope=scope, exclude_action_id=action_id)
                # Tracer la résolution automatique
                if effective_key != default_choice:
                    self._resolution_log.append({
                        "addon": addon_name or addon_id,
                        "action": label,
                        "original": default_choice,
                        "resolved": effective_key,
                        "scope": scope
                    })

        claim_obj = ShortcutClaim(
            action_id=action_id,
            label=label,
            scope=scope,
            current_key=effective_key,
            default_key=default_choice,
            fallbacks=fallbacks,
            on_change=on_change,
            addon_id=addon_id,
            addon_name=addon_name,
            config_key=config_key
        )
        self.claims[action_id] = claim_obj

        # Sauvegarder dans overrides pour stabilité
        if user_scut is None and effective_key != default_choice:
            overrides[action_id] = effective_key
            if addon_name and label:
                overrides[f"{addon_name}_{label}"] = effective_key
            cfg["addon_shortcuts_overrides"] = overrides
            self._save_addon_config(cfg)

        return effective_key

    def notify_shortcut_changed(self, action_id: str, new_shortcut: str):
        """Déclenché lorsqu'un raccourci est modifié dans l'interface de 1762336370."""
        norm = normalize_key_str(new_shortcut)
        claim = self.claims.get(action_id)
        if claim:
            claim.current_key = norm
            if callable(claim.on_change):
                try:
                    claim.on_change(norm)
                except Exception as e:
                    print(f"[ShortcutBroker] Erreur dans on_change pour {action_id}: {e}")

        # Déclencher le hook Anki pour les écouteurs passifs
        try:
            gui_hooks.custom_shortcuts_did_change(action_id, norm)
        except Exception:
            pass

    def scan_static_shortcuts_json(self):
        """Scanne tous les fichiers 'shortcuts.json' dans addons21."""
        if self._static_manifests_loaded:
            return
        self._static_manifests_loaded = True

        try:
            addons_dir = mw.addonManager.addonsFolder() if (mw and mw.addonManager) else None
        except Exception:
            addons_dir = None
        if not addons_dir or not os.path.isdir(addons_dir):
            return

        for entry in os.listdir(addons_dir):
            if entry in ("1762336370", "__pycache__", ".git", ".agents", "agents"):
                continue
            addon_dir = os.path.join(addons_dir, entry)
            if not os.path.isdir(addon_dir):
                continue

            manifest_path = os.path.join(addon_dir, "shortcuts.json")
            if not os.path.isfile(manifest_path):
                continue

            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                addon_name = data.get("addon_name", entry)
                shortcuts_list = data.get("shortcuts", [])
                for item in shortcuts_list:
                    act_id = item.get("id") or f"{entry}_{item.get('label')}"
                    label = item.get("label", act_id)
                    scope = item.get("scope", "main")
                    default_key = item.get("default", "")
                    fallbacks = item.get("fallbacks", [])
                    config_key = item.get("config_key", "")

                    prefs = [default_key] + fallbacks
                    self.claim(
                        action_id=act_id,
                        label=label,
                        scope=scope,
                        preferred=prefs,
                        addon_id=entry,
                        addon_name=addon_name,
                        config_key=config_key
                    )
            except Exception as e:
                print(f"[ShortcutBroker] Erreur lecture {manifest_path}: {e}")

    def proactive_conflict_resolution(self):
        """
        Détecte et résout automatiquement les collisions entre extensions et Anki natif.
        Émet une notification unique (tooltip sobre) récapitulant les adaptations.
        """
        self.scan_static_shortcuts_json()

        cfg = self._get_addon_config()
        overrides = cfg.get("addon_shortcuts_overrides", {})
        if not isinstance(overrides, dict):
            overrides = {}

        # 1. Scanner tous les raccourcis d'extensions actuels
        try:
            from .addon_scanner import AddonScanner
            scanner = AddonScanner(current_addon_id="1762336370")
            addon_items = scanner.get_all_addon_shortcuts()
        except Exception:
            addon_items = []

        # Identifier les raccourcis natifs pour vérifier les collisions
        native_shortcuts: Dict[str, Set[str]] = {}
        for k, v in cfg.items():
            if isinstance(v, str) and not k.startswith("Ω") and k not in ("interface_language", "addon_shortcuts_overrides", "config_file_path"):
                norm = normalize_key_str(v)
                if not norm:
                    continue
                sc_scope = "toolbar"
                if k.startswith("main "):
                    sc_scope = "main"
                elif k.startswith("editor "):
                    sc_scope = "editor"
                elif k.startswith("reviewer "):
                    sc_scope = "reviewer"
                elif k.startswith("window_browser "):
                    sc_scope = "browser"
                
                if norm not in native_shortcuts:
                    native_shortcuts[norm] = set()
                native_shortcuts[norm].add(sc_scope)

        adapted_count = 0
        adapted_details = []

        seen_keys: Dict[Tuple[str, str], str] = {} # (norm_key, scope) -> item identifier

        for item in addon_items:
            # Clé sémantique stable
            sk = item.edn_info.get("shortcut_key") if item.edn_info else None
            name_key = f"{item.addon_name}_{item.action_name}"
            id_key = f"{item.addon_id}_{item.action_name}"

            # Si l'utilisateur l'a déjà explicitement personnalisé, on ne touche à rien
            if (sk and sk in overrides) or (name_key in overrides) or (id_key in overrides):
                continue

            current_norm = normalize_key_str(item.shortcut)
            if not current_norm:
                continue

            # Vérifier collision avec Anki natif dans le même scope (ou global)
            has_conflict = False
            conflict_reason = ""
            if current_norm in native_shortcuts:
                scopes = native_shortcuts[current_norm]
                if item.scope in scopes or "main" in scopes or "toolbar" in scopes:
                    has_conflict = True
                    conflict_reason = "Anki natif"

            # Vérifier collision avec un autre add-on dans le même scope
            pair_key = (current_norm, item.scope)
            if pair_key in seen_keys:
                has_conflict = True
                conflict_reason = seen_keys[pair_key]
            else:
                seen_keys[pair_key] = item.addon_name

            if has_conflict:
                # Proposer une alternative
                alternative = self.suggest_alternative([current_norm], scope=item.scope)
                if alternative and alternative != current_norm:
                    # Enregistrer dans overrides
                    if sk:
                        overrides[sk] = alternative
                    overrides[name_key] = alternative
                    overrides[id_key] = alternative

                    # Si item a une QAction ou QShortcut vivante, l'appliquer en direct
                    if item.qaction and hasattr(item.qaction, "setShortcut"):
                        try:
                            item.qaction.setShortcut(QKeySequence(alternative))
                        except Exception:
                            pass
                    if item.qshortcut and hasattr(item.qshortcut, "setKey"):
                        try:
                            item.qshortcut.setKey(QKeySequence(alternative))
                        except Exception:
                            pass

                    # Si EDN, persister dans edn_shared_config.json
                    if sk and hasattr(scanner, "save_edn_shortcut"):
                        try:
                            scanner.save_edn_shortcut(sk, alternative)
                        except Exception:
                            pass

                    # Si l'addon a un config_key dans config.json
                    if item.config_key and item.addon_id and mw and hasattr(mw, "addonManager") and mw.addonManager:
                        try:
                            third_cfg = mw.addonManager.getConfig(item.addon_id)
                            if isinstance(third_cfg, dict) and item.config_key in third_cfg:
                                third_cfg[item.config_key] = alternative
                                mw.addonManager.writeConfig(item.addon_id, third_cfg)
                        except Exception:
                            pass

                    adapted_count += 1
                    adapted_details.append(f"{item.addon_name} : '{item.action_name}' adapté sur {alternative} (au lieu de {current_norm} utilisé par {conflict_reason})")
                    seen_keys[(alternative, item.scope)] = item.addon_name

        if adapted_count > 0:
            cfg["addon_shortcuts_overrides"] = overrides
            self._save_addon_config(cfg)
            # Notification unique post-détection (sobre, sans emoji)
            msg = f"Raccourcis clavier : {adapted_count} conflit(s) d'extension(s) résolu(s) automatiquement.\n"
            msg += "\n".join(adapted_details[:3])
            if len(adapted_details) > 3:
                msg += f"\n...et {len(adapted_details) - 3} autre(s)."
            
            QTimer.singleShot(1500, lambda: tooltip(msg, period=6000))
        elif len(self._resolution_log) > 0:
            # Notification pour les claims auto-résolus
            msg = f"Raccourcis clavier : {len(self._resolution_log)} action(s) d'extension(s) adaptée(s) sans collision."
            QTimer.singleShot(1500, lambda: tooltip(msg, period=4000))
            self._resolution_log.clear()


# Initialisation et injection globale sur mw
def init_shortcut_broker():
    broker = ShortcutBroker.get_instance()
    if mw:
        mw.shortcut_broker = broker
    # Scanner les shortcuts.json et résoudre proactivement les conflits
    QTimer.singleShot(300, broker.proactive_conflict_resolution)


# Hook d'initialisation Anki
gui_hooks.profile_did_open.append(init_shortcut_broker)
