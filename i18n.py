# -*- coding: utf-8 -*-
"""
Module d'internationalisation pour le gestionnaire et visualiseur de raccourcis.
Detecte automatiquement la langue native d'Anki et fournit les traductions
completes pour le francais, l'anglais et le chinois.
"""

from aqt import mw

def get_anki_language():
    """Detecte la langue courante configuree dans Anki."""
    try:
        from anki.lang import current_lang
        lang = current_lang()
        if lang:
            return lang
    except Exception:
        pass
    
    try:
        if mw and hasattr(mw, "pm") and mw.pm and hasattr(mw.pm, "meta"):
            lang = mw.pm.meta.get("defaultLang")
            if lang:
                return lang
    except Exception:
        pass
        
    return "fr_FR"

def resolve_language(configured_lang):
    """Resout la langue effective a utiliser (gere le mode 'auto')."""
    if not configured_lang or configured_lang == "auto":
        anki_lang = get_anki_language()
        if anki_lang.startswith("fr"):
            return "fr_FR"
        elif anki_lang.startswith("zh"):
            return "zh_CN"
        else:
            return "en_US"
    if configured_lang in TRANSLATIONS:
        return configured_lang
    if configured_lang.startswith("fr"):
        return "fr_FR"
    elif configured_lang.startswith("zh"):
        return "zh_CN"
    return "en_US"

TRANSLATIONS = {
    "fr_FR": {
        # Titres et navigation
        "window_title": "Raccourcis clavier",
        "preset_label": "Préréglage :",
        "default_preset": "Raccourcis par défaut",
        "commands_scope_label": "Commandes :",
        "layout_label": "Disposition du clavier :",
        "layout_auto": "Disposition Windows (auto)",
        "layout_azerty": "AZERTY (FR)",
        "layout_qwerty": "QWERTY (US)",
        "layout_qwertz": "QWERTZ (DE/CH)",
        "layout_dvorak": "Dvorak",
        "layout_colemak": "Colemak",
        "language_label": "Langue :",
        "lang_auto": "Langue d'Anki (auto)",
        "lang_fr": "Français",
        "lang_en": "English",
        "lang_zh": "Chinois",
        
        # Contextes
        "scope_all": "Toutes les commandes",
        "scope_main": "Écran principal",
        "scope_editor": "Éditeur de cartes",
        "scope_reviewer": "Réviseur",
        "scope_browser": "Navigateur",
        "scope_toolbar": "Outils et Menus",
        "scope_addons": "Autres Add-ons",
        
        # Clavier et inspecteur
        "key_inspector_title": "Touche :",
        "no_key_selected": "Aucune touche sélectionnée",
        "no_key_hint": "Cliquez sur une touche du clavier pour inspecter ou modifier ses combinaisons.",
        "btn_deselect_key": "Désélectionner",
        "btn_edit_shortcut": "Modifier...",
        "col_modifier": "Modificateurs",
        "col_command": "Commande",
        "mod_none": "Aucun",
        "mod_ctrl": "Ctrl",
        "mod_alt": "Alt",
        "mod_shift": "Maj",
        "mod_ctrl_shift": "Ctrl+Maj",
        "mod_ctrl_alt": "Ctrl+Alt",
        "mod_alt_shift": "Alt+Maj",
        "mod_ctrl_alt_shift": "Ctrl+Alt+Maj",
        
        # Légende & Filtres interactifs
        "legend_anki": "Raccourcis Anki actifs",
        "legend_addon": "Raccourcis d'autres Add-ons",
        "filter_anki": "Raccourcis Anki actifs",
        "filter_addons": "Raccourcis d'autres Add-ons",
        "legend_custom": "Raccourcis personnalisés",
        "legend_modifier": "Touche de modification enfoncée",
        "legend_conflict": "Conflit détecté",
        
        # Boîte de dialogue de saisie
        "dialog_edit_title": "Modifier le raccourci",
        "dialog_edit_instruction": "Appuyez sur la combinaison de touches souhaitée :",
        "dialog_edit_current": "Raccourci actuel :",
        "dialog_edit_clear": "Effacer (Désactiver)",
        "copy_cell": "Copier la valeur",
        "copy_row": "Copier la ligne",
        
        # Liste des commandes et recherche
        "search_placeholder": "Rechercher une commande ou un raccourci...",
        "col_action": "Commande",
        "col_shortcut": "Raccourci",
        "col_category": "Catégorie / Contexte",
        "col_source": "Source",
        
        # Boutons
        "btn_clear_shortcut": "Effacer",
        "btn_reset_shortcut": "Réinitialiser",
        "btn_disable_tab": "Désactiver la catégorie",
        "btn_disable_all": "Désactiver tout",
        "btn_restore_tab": "Rétablir la catégorie",
        "btn_restore_all": "Rétablir par défaut",
        "btn_apply": "Appliquer",
        "btn_cancel": "Annuler",
        "btn_ok": "OK",
        "btn_browse": "Parcourir",
        "btn_reset_path": "Réinitialiser chemin",
        
        # Messages
        "nop_hint": "<nop> pour désactiver",
        "changes_saved": "Paramètres enregistrés. Redémarrez Anki si nécessaire pour appliquer certains changements.",
        "config_path_label": "Fichier de configuration :",
        "config_path_note": "Un chemin personnalisé permet de synchroniser vos raccourcis entre plusieurs appareils.",
        "save_success": "Configuration enregistrée avec succès.",
        "save_error": "Erreur lors de l'enregistrement de la configuration.",
        "other_addons_count": "raccourcis détectés depuis d'autres add-ons",
        "conflict_warning": "Attention : ce raccourci est déjà attribué à une autre commande dans ce même contexte.",
        
        # Libellés des actions
        "readable_names": {
            # Écran principal
            "main debug": "Console de débogage",
            "main deckbrowser": "Arborescence des paquets",
            "main study": "Commencer l'étude",
            "main add": "Ajouter des cartes",
            "main browse": "Ouvrir le navigateur",
            "main stats": "Afficher les statistiques",
            "main sync": "Synchroniser la collection",
            
            # Éditeur
            "editor card layout": "Disposition des cartes",
            "editor bold": "Gras",
            "editor italic": "Italique",
            "editor underline": "Souligné",
            "editor superscript": "Exposant",
            "editor subscript": "Indice",
            "editor remove format": "Effacer le formatage",
            "editor foreground": "Couleur du texte",
            "editor change col": "Couleur de surlignage",
            "editor change deck": "Changer de paquet",
            "editor cloze": "Texte à trou (Cloze)",
            "editor cloze alt": "Texte à trou (même numéro)",
            "editor cloze forced increment": "Texte à trou (incrémenter)",
            "editor cloze no increment": "Texte à trou (sans incrémenter)",
            "editor add media": "Insérer un média / image",
            "editor record sound": "Enregistrer un son",
            "editor insert latex": "Insérer du LaTeX",
            "editor insert latex equation": "Insérer équation LaTeX",
            "editor insert latex math environment": "Insérer environnement maths LaTeX",
            "editor insert mathjax inline": "Insérer formule MathJax en ligne",
            "editor insert mathjax block": "Insérer bloc formule MathJax",
            "editor insert mathjax chemistry": "Insérer formule chimie MathJax",
            "editor html edit": "Modifier le code HTML source",
            "editor focus tags": "Accéder au champ étiquettes (Tags)",
            "editor confirm add card": "Valider et ajouter la carte",
            "editor add card close window": "Ajouter et fermer la fenêtre",
            "editor change note type": "Changer le type de note",
            "editor toggle sticky current": "Figer le champ actif",
            "editor toggle sticky all": "Figer tous les champs",
            "editor block indent": "Augmenter le retrait",
            "editor block outdent": "Diminuer le retrait",
            "editor list insert ordered": "Insérer liste numérotée",
            "editor list insert unordered": "Insérer liste à puces",
            
            # Réviseur
            "reviewer edit current": "Modifier la note courante",
            "reviewer flip card 1": "Afficher la réponse (Espace)",
            "reviewer flip card 2": "Afficher la réponse (Entrée)",
            "reviewer flip card 3": "Afficher la réponse (Entrée Pavé)",
            "reviewer replay audio 1": "Rejouer l'audio 1",
            "reviewer replay audio 2": "Rejouer l'audio 2",
            "reviewer set flag 1": "Marqueur rouge",
            "reviewer set flag 2": "Marqueur orange",
            "reviewer set flag 3": "Marqueur vert",
            "reviewer set flag 4": "Marqueur bleu",
            "reviewer set flag 5": "Marqueur rose",
            "reviewer set flag 6": "Marqueur turquoise",
            "reviewer set flag 7": "Marqueur violet",
            "reviewer set flag 0": "Supprimer le marqueur",
            "reviewer mark card": "Épingler la carte (Marque *)",
            "reviewer bury note": "Enfouir la note",
            "reviewer bury card": "Enfouir la carte",
            "reviewer suspend note": "Suspendre la note",
            "reviewer suspend card": "Suspendre la carte",
            "reviewer delete note": "Supprimer la note",
            "reviewer play recorded voice": "Écouter l'enregistrement vocal",
            "reviewer record voice": "Enregistrer la voix",
            "reviewer set due date": "Définir la date d'échéance",
            "reviewer options menu": "Menu des options",
            "reviewer choice 1": "Bouton 1 : À revoir",
            "reviewer choice 2": "Bouton 2 : Difficile",
            "reviewer choice 3": "Bouton 3 : Correct",
            "reviewer choice 4": "Bouton 4 : Facile",
            "reviewer pause audio": "Pause / Reprendre audio",
            "reviewer seek backward": "Recul audio",
            "reviewer seek forward": "Avance audio",
            "reviewer card info": "Informations sur la carte",
            "reviewer previous card info": "Infos sur la carte précédente",
            "reviewer more options": "Menu Plus d'options",
            
            # Navigateur
            "window_browser preview": "Aperçu de la carte",
            "window_browser reschedule": "Reprogrammer la carte",
            "window_browser select all": "Tout sélectionner",
            "window_browser undo": "Annuler la dernière action",
            "window_browser invert selection": "Inverser la sélection",
            "window_browser find": "Rechercher",
            "window_browser goto note": "Aller à la note",
            "window_browser goto next note": "Note suivante",
            "window_browser goto previous note": "Note précédente",
            "window_browser guide": "Guide d'utilisation",
            "window_browser change note type": "Changer le type de note",
            "window_browser find and replace": "Rechercher et remplacer",
            "window_browser filter": "Filtrer la vue",
            "window_browser goto card list": "Accéder à la liste des cartes",
            "window_browser reposition": "Repositionner",
            "window_browser first card": "Première carte",
            "window_browser last card": "Dernière carte",
            "window_browser close": "Fermer le navigateur",
            "window_browser info": "Informations de la carte",
            "window_browser add tag": "Ajouter une étiquette",
            "window_browser remove tag": "Supprimer une étiquette",
            "window_browser suspend": "Suspendre / Activer",
            "window_browser delete": "Supprimer la sélection",
            "window_browser add note": "Créer une nouvelle note",
            "window_browser change deck": "Déplacer vers un paquet",
            "window_browser flag_red": "Marqueur rouge",
            "window_browser flag_orange": "Marqueur orange",
            "window_browser flag_green": "Marqueur vert",
            "window_browser flag_blue": "Marqueur bleu",
            "window_browser goto sidebar": "Accéder au panneau latéral",
            "window_browser toggle mark": "Basculer la marque (*)",
            "window_browser clear unused tags": "Nettoyer les étiquettes orphelines",
            "window_browser find duplicates": "Rechercher les doublons",
            "window_browser select notes": "Sélectionner les notes",
            "window_browser manage note types": "Gérer les types de notes",
            "window_browser save current filter": "Enregistrer le filtre actuel",
            "window_browser remove current filter": "Supprimer le filtre",
            "window_browser sidebar search": "Recherche dans le panneau latéral",
            "window_browser sidebar select": "Sélectionner dans le panneau latéral",
            "window_browser forget card": "Réinitialiser l'historique (Oublier)",
            
            # Barre d'outils et menus
            "m_toolbox quit": "Quitter Anki",
            "m_toolbox preferences": "Préférences",
            "m_toolbox undo": "Annuler",
            "m_toolbox see documentation": "Consulter la documentation",
            "m_toolbox switch profile": "Changer de profil",
            "m_toolbox export": "Exporter des paquets",
            "m_toolbox import": "Importer un fichier",
            "m_toolbox study": "Étudier",
            "m_toolbox create filtered deck": "Créer un paquet filtré",
            "m_toolbox addons": "Gestionnaire des modules complémentaires"
        }
    },
    
    "en_US": {
        "window_title": "Keyboard Shortcuts",
        "preset_label": "Preset:",
        "default_preset": "Default Shortcuts",
        "commands_scope_label": "Commands:",
        "layout_label": "Keyboard Layout:",
        "layout_auto": "Windows Layout (Auto)",
        "layout_azerty": "AZERTY (FR)",
        "layout_qwerty": "QWERTY (US)",
        "layout_qwertz": "QWERTZ (DE/CH)",
        "layout_dvorak": "Dvorak",
        "layout_colemak": "Colemak",
        "language_label": "Language:",
        "lang_auto": "Anki Language (Auto)",
        "lang_fr": "French",
        "lang_en": "English",
        "lang_zh": "Chinese",
        
        "scope_all": "All Commands",
        "scope_main": "Main Screen",
        "scope_editor": "Card Editor",
        "scope_reviewer": "Reviewer",
        "scope_browser": "Browser",
        "scope_toolbar": "Tools & Menus",
        "scope_addons": "Other Add-ons",
        
        "key_inspector_title": "Key:",
        "no_key_selected": "No key selected",
        "no_key_hint": "Click a key on the virtual keyboard to inspect or edit its combinations.",
        "btn_deselect_key": "Deselect",
        "btn_edit_shortcut": "Edit...",
        "col_modifier": "Modifiers",
        "col_command": "Command",
        "mod_none": "None",
        "mod_ctrl": "Ctrl",
        "mod_alt": "Alt",
        "mod_shift": "Shift",
        "mod_ctrl_shift": "Ctrl+Shift",
        "mod_ctrl_alt": "Ctrl+Alt",
        "mod_alt_shift": "Alt+Shift",
        "mod_ctrl_alt_shift": "Ctrl+Alt+Shift",
        
        "legend_anki": "Active Anki Shortcuts",
        "legend_addon": "Other Add-ons Shortcuts",
        "filter_anki": "Active Anki Shortcuts",
        "filter_addons": "Other Add-ons Shortcuts",
        "legend_custom": "Customized Shortcuts",
        "legend_modifier": "Modifier Key Pressed",
        "legend_conflict": "Conflict Detected",
        
        "dialog_edit_title": "Edit Shortcut",
        "dialog_edit_instruction": "Press the desired key combination:",
        "dialog_edit_current": "Current Shortcut:",
        "dialog_edit_clear": "Clear (Disable)",
        "copy_cell": "Copy Cell",
        "copy_row": "Copy Row",
        
        "search_placeholder": "Search command or shortcut...",
        "col_action": "Command",
        "col_shortcut": "Shortcut",
        "col_category": "Category / Scope",
        "col_source": "Source",
        
        "btn_clear_shortcut": "Clear",
        "btn_reset_shortcut": "Reset",
        "btn_disable_tab": "Disable Category",
        "btn_disable_all": "Disable All",
        "btn_restore_tab": "Restore Category",
        "btn_restore_all": "Restore Defaults",
        "btn_apply": "Apply",
        "btn_cancel": "Cancel",
        "btn_ok": "OK",
        "btn_browse": "Browse",
        "btn_reset_path": "Reset Path",
        
        "nop_hint": "<nop> to disable",
        "changes_saved": "Settings saved. Please restart Anki if needed to apply changes.",
        "config_path_label": "Config File Path:",
        "config_path_note": "A custom configuration path allows syncing shortcuts across devices.",
        "save_success": "Configuration saved successfully.",
        "save_error": "Failed to save configuration.",
        "other_addons_count": "shortcuts detected from other add-ons",
        "conflict_warning": "Warning: this shortcut is already assigned to another command in this scope.",
        
        "readable_names": {
            "main debug": "Debug Console",
            "main deckbrowser": "Deck Browser",
            "main study": "Study",
            "main add": "Add Cards",
            "main browse": "Browse",
            "main stats": "Statistics",
            "main sync": "Sync Collection",
            
            "editor card layout": "Card Layout",
            "editor bold": "Bold",
            "editor italic": "Italic",
            "editor underline": "Underline",
            "editor superscript": "Superscript",
            "editor subscript": "Subscript",
            "editor remove format": "Remove Format",
            "editor foreground": "Text Color",
            "editor change col": "Background Color",
            "editor change deck": "Change Deck",
            "editor cloze": "Cloze",
            "editor cloze alt": "Cloze (Same Number)",
            "editor cloze forced increment": "Cloze (Forced Increment)",
            "editor cloze no increment": "Cloze (No Increment)",
            "editor add media": "Add Media / Image",
            "editor record sound": "Record Sound",
            "editor insert latex": "Insert LaTeX",
            "editor insert latex equation": "Insert LaTeX Equation",
            "editor insert latex math environment": "Insert LaTeX Math Environment",
            "editor insert mathjax inline": "Insert MathJax Inline",
            "editor insert mathjax block": "Insert MathJax Block",
            "editor insert mathjax chemistry": "Insert MathJax Chemistry",
            "editor html edit": "HTML Edit",
            "editor focus tags": "Focus Tags Field",
            "editor confirm add card": "Confirm Add Card",
            "editor add card close window": "Add Card and Close Window",
            "editor change note type": "Change Note Type",
            "editor toggle sticky current": "Toggle Sticky Current Field",
            "editor toggle sticky all": "Toggle Sticky All Fields",
            "editor block indent": "Block Indent",
            "editor block outdent": "Block Outdent",
            "editor list insert ordered": "Insert Ordered List",
            "editor list insert unordered": "Insert Unordered List",
            
            "reviewer edit current": "Edit Current Note",
            "reviewer flip card 1": "Show Answer (Space)",
            "reviewer flip card 2": "Show Answer (Return)",
            "reviewer flip card 3": "Show Answer (Numpad Enter)",
            "reviewer replay audio 1": "Replay Audio 1",
            "reviewer replay audio 2": "Replay Audio 2",
            "reviewer set flag 1": "Red Flag",
            "reviewer set flag 2": "Orange Flag",
            "reviewer set flag 3": "Green Flag",
            "reviewer set flag 4": "Blue Flag",
            "reviewer set flag 5": "Pink Flag",
            "reviewer set flag 6": "Turquoise Flag",
            "reviewer set flag 7": "Purple Flag",
            "reviewer set flag 0": "Clear Flag",
            "reviewer mark card": "Mark Card (*)",
            "reviewer bury note": "Bury Note",
            "reviewer bury card": "Bury Card",
            "reviewer suspend note": "Suspend Note",
            "reviewer suspend card": "Suspend Card",
            "reviewer delete note": "Delete Note",
            "reviewer play recorded voice": "Play Recorded Voice",
            "reviewer record voice": "Record Voice",
            "reviewer set due date": "Set Due Date",
            "reviewer options menu": "Options Menu",
            "reviewer choice 1": "Choice 1: Again",
            "reviewer choice 2": "Choice 2: Hard",
            "reviewer choice 3": "Choice 3: Good",
            "reviewer choice 4": "Choice 4: Easy",
            "reviewer pause audio": "Pause Audio",
            "reviewer seek backward": "Seek Backward",
            "reviewer seek forward": "Seek Forward",
            "reviewer card info": "Card Info",
            "reviewer previous card info": "Previous Card Info",
            "reviewer more options": "More Options Menu",
            
            "window_browser preview": "Preview Card",
            "window_browser reschedule": "Reschedule",
            "window_browser select all": "Select All",
            "window_browser undo": "Undo",
            "window_browser invert selection": "Invert Selection",
            "window_browser find": "Find",
            "window_browser goto note": "Go to Note",
            "window_browser goto next note": "Next Note",
            "window_browser goto previous note": "Previous Note",
            "window_browser guide": "Guide",
            "window_browser change note type": "Change Note Type",
            "window_browser find and replace": "Find and Replace",
            "window_browser filter": "Filter",
            "window_browser goto card list": "Go to Card List",
            "window_browser reposition": "Reposition",
            "window_browser first card": "First Card",
            "window_browser last card": "Last Card",
            "window_browser close": "Close Browser",
            "window_browser info": "Card Info",
            "window_browser add tag": "Add Tag",
            "window_browser remove tag": "Remove Tag",
            "window_browser suspend": "Toggle Suspend",
            "window_browser delete": "Delete Selected",
            "window_browser add note": "Add Note",
            "window_browser change deck": "Change Deck",
            "window_browser flag_red": "Red Flag",
            "window_browser flag_orange": "Orange Flag",
            "window_browser flag_green": "Green Flag",
            "window_browser flag_blue": "Blue Flag",
            "window_browser goto sidebar": "Go to Sidebar",
            "window_browser toggle mark": "Toggle Mark (*)",
            "window_browser clear unused tags": "Clear Unused Tags",
            "window_browser find duplicates": "Find Duplicates",
            "window_browser select notes": "Select Notes",
            "window_browser manage note types": "Manage Note Types",
            "window_browser save current filter": "Save Current Filter",
            "window_browser remove current filter": "Remove Current Filter",
            "window_browser sidebar search": "Sidebar Search",
            "window_browser sidebar select": "Sidebar Select",
            "window_browser forget card": "Reset Card Progress (Forget)",
            
            "m_toolbox quit": "Quit Anki",
            "m_toolbox preferences": "Preferences",
            "m_toolbox undo": "Undo",
            "m_toolbox see documentation": "See Documentation",
            "m_toolbox switch profile": "Switch Profile",
            "m_toolbox export": "Export",
            "m_toolbox import": "Import",
            "m_toolbox study": "Study",
            "m_toolbox create filtered deck": "Create Filtered Deck",
            "m_toolbox addons": "Add-ons Manager"
        }
    },
    
    "zh_CN": {
        "window_title": "快捷键设置",
        "preset_label": "预设：",
        "default_preset": "默认快捷键",
        "commands_scope_label": "命令范围：",
        "layout_label": "键盘布局：",
        "layout_azerty": "AZERTY (法文)",
        "layout_qwerty": "QWERTY (美式)",
        "language_label": "语言：",
        "lang_auto": "Anki原生语言 (自动)",
        "lang_fr": "法语",
        "lang_en": "英文",
        "lang_zh": "中文",
        
        "scope_all": "所有命令",
        "scope_main": "主界面",
        "scope_editor": "编辑器",
        "scope_reviewer": "复习界面",
        "scope_browser": "浏览器",
        "scope_toolbar": "工具栏与菜单",
        "scope_addons": "其他插件",
        
        "key_inspector_title": "按键：",
        "no_key_selected": "未选择按键",
        "col_modifier": "修饰键",
        "col_command": "命令",
        "mod_none": "无",
        "mod_ctrl": "Ctrl",
        "mod_alt": "Alt",
        "mod_shift": "Shift",
        "mod_ctrl_shift": "Ctrl+Shift",
        "mod_ctrl_alt": "Ctrl+Alt",
        "mod_alt_shift": "Alt+Shift",
        "mod_ctrl_alt_shift": "Ctrl+Alt+Shift",
        
        "legend_anki": "Anki原生/自定义快捷键",
        "legend_addon": "其他插件快捷键",
        "legend_custom": "已修改的快捷键",
        "legend_modifier": "修饰键已按下",
        "legend_conflict": "检测到冲突",
        
        "search_placeholder": "搜索命令或快捷键...",
        "col_action": "命令",
        "col_shortcut": "快捷键",
        "col_category": "分类",
        "col_source": "来源",
        
        "btn_clear_shortcut": "清除",
        "btn_reset_shortcut": "重置",
        "btn_disable_tab": "禁用当前分类",
        "btn_disable_all": "禁用全部",
        "btn_restore_tab": "恢复当前分类",
        "btn_restore_all": "恢复默认",
        "btn_apply": "应用",
        "btn_cancel": "取消",
        "btn_ok": "确定",
        "btn_browse": "浏览",
        "btn_reset_path": "重置路径",
        
        "nop_hint": "<nop> 表示禁用",
        "changes_saved": "设置已保存。如有需要请重启Anki以生效。",
        "config_path_label": "配置文件路径：",
        "config_path_note": "自定义路径可在多台设备间同步快捷键。",
        "save_success": "配置保存成功。",
        "save_error": "保存配置文件失败。",
        "other_addons_count": "个从其他插件检测到的快捷键",
        "conflict_warning": "警告：此快捷键在此范围内已分配给另一项命令。",
        
        "readable_names": {}
    }
}

class I18n:
    def __init__(self, lang_code=None):
        self.set_language(lang_code)

    def set_language(self, lang_code):
        self.lang = resolve_language(lang_code)
        self.dict = TRANSLATIONS.get(self.lang, TRANSLATIONS["en_US"])
        self.en_dict = TRANSLATIONS["en_US"]
        
    def t(self, key, default=None):
        """Recupere une chaine traduite."""
        if key in self.dict:
            return self.dict[key]
        if key in self.en_dict:
            return self.en_dict[key]
        return default if default is not None else key

    def get_action_name(self, action_key):
        """Traduit une cle d'action interne."""
        names = self.dict.get("readable_names", {})
        if action_key in names:
            return names[action_key]
        en_names = self.en_dict.get("readable_names", {})
        if action_key in en_names:
            return en_names[action_key]
        clean = action_key.replace("window_browser", "navigateur").replace("m_toolbox", "outils")
        return clean.replace("_", " ").title()
