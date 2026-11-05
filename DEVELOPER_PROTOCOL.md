# Protocole Universel de Déclaration de Raccourcis pour Add-ons Anki
Ce protocole permet à votre add-on d'être compatible avec le gestionnaire de raccourcis (`Customize Keyboard Shortcuts Enhanced` - `1762336370`), d'apparaître sur le clavier virtuel interactif, et de **s'adapter automatiquement aux touches déjà occupées chez l'utilisateur** sans aucun conflit.

---

## Option 1 : Déclaration Statique (`shortcuts.json`) — Zéro Ligne de Python

Déposez un fichier nommé `shortcuts.json` à la racine du dossier de votre add-on (`addons21/<votre_addon>/shortcuts.json`) :

```json
{
  "schema_version": 1,
  "addon_name": "Mon Super Add-on",
  "shortcuts": [
    {
      "id": "mon_addon.action_principale",
      "label": "Ouvrir le panneau d'analyse",
      "scope": "browser",
      "default": "Ctrl+Alt+A",
      "fallbacks": ["Ctrl+Shift+A", "Alt+A", "F10"],
      "config_key": "shortcut_open_panel"
    },
    {
      "id": "mon_addon.action_revision",
      "label": "Action de révision rapide",
      "scope": "reviewer",
      "default": "Alt+R",
      "fallbacks": ["Ctrl+Alt+R", "Ctrl+Shift+R"],
      "config_key": "shortcut_review_action"
    }
  ]
}
```

### Champs du manifeste :
- `id` *(requis)* : Identifiant unique de l'action (`<addon_nom>.<action>`).
- `label` *(requis)* : Libellé lisible affiché dans le tableau et sur les touches du clavier virtuel.
- `scope` *(requis)* : Portée du raccourci :
  - `"main"` : Écran d'accueil / général
  - `"reviewer"` : Réviseur / étude des cartes
  - `"browser"` : Navigateur de cartes
  - `"editor"` : Éditeur de champs de note
  - `"toolbar"` : Barre d'outils supérieure
- `default` *(requis)* : Raccourci idéal souhaité par défaut.
- `fallbacks` *(optionnel)* : Liste ordonnée de combinaisons de repli si la touche par défaut est déjà occupée par Anki natif ou un autre add-on chez l'utilisateur.
- `config_key` *(optionnel)* : Clé correspondante dans votre `config.json` si votre add-on persiste ses raccourcis localement.

---

## Option 2 : API Dynamique via `mw.shortcut_broker` (8 Lignes)

Pour les add-ons qui créent leurs `QAction` ou `QShortcut` dynamiquement en Python, `1762336370` expose `mw.shortcut_broker`.

### Exemple d'intégration :

```python
from aqt import mw

def setup_my_action():
    # 1. Obtenir le broker (sans crash si l'addon de raccourcis n'est pas installé)
    broker = getattr(mw, "shortcut_broker", None)
    
    if broker:
        # Retourne le raccourci choisi par l'utilisateur ou la première touche libre sans collision
        shortcut_key = broker.claim(
            action_id="mon_addon.toggle_panel",
            label="Afficher / Masquer le volet",
            scope="browser",
            preferred=["Ctrl+Alt+P", "Ctrl+Shift+P", "Alt+P"],
            on_change=lambda new_key: my_action.setShortcut(new_key),
            addon_id="mon_addon",
            addon_name="Mon Add-on"
        )
    else:
        shortcut_key = "Ctrl+Alt+P"

    my_action.setShortcut(shortcut_key)
```

### Méthodes utiles du Broker :
- `broker.get_occupied(scope="reviewer")` : Retourne la liste de toutes les touches actuellement utilisées dans ce contexte.
- `broker.is_free(shortcut="Ctrl+Alt+C", scope="browser")` : Vérifie si la combinaison est libre.
- `broker.suggest_alternative(preferred=["Ctrl+Alt+C", "Alt+C"], scope="browser")` : Calcule immédiatement la meilleure alternative sans conflit.
- `broker.claim(...)` : Réserve et synchronise l'action avec l'interface graphique de `1762336370` et active le rechargement en direct (*Hot-Reload* sans redémarrer Anki via `on_change`).
