# Customize Keyboard Shortcuts (Enhanced Edition)

An advanced keyboard shortcuts manager and interactive visualizer for Anki. Inspired by Adobe After Effects and professional creative suites, this add-on brings a visual keyboard map, automatic Windows layout detection, and third-party add-on shortcut discovery to Anki.

---

## Key Features

- **Interactive Virtual Keyboard** : Live graphical layout rendering key mappings dynamically as you press or select modifiers (`Ctrl`, `Alt`, `Shift`).
- **Native Layout Detection** : Automatically adapts to your active system keyboard layout (**AZERTY**, **QWERTY**, **QWERTZ**, **Dvorak**, **Colemak**).
- **Third-Party Add-on Discovery** : Scans and displays shortcuts registered by other installed add-ons (EDN ecosystem, Card Management, Diff viewers, etc.).
- **Multi-Language Support** : Seamless localization in **French**, **English**, and **Chinese** with automatic Anki language detection.
- **Quick Key Sequence Capture** : Modal recorder to capture and assign shortcuts on the fly.
- **Search & Filter** : Instantly search by action name, key, or category.

---

## How to Use

1. Go to **Tools > Customize Keyboard Shortcuts...** in the main Anki window.
2. Click any key on the virtual keyboard to inspect its bound action, or browse actions by section (Main, Editor, Reviewer, Browser, etc.).
3. Double-click an action or click a key to modify the keybinding.
4. Click **Apply** to save your changes.

---

## Developer Protocol: Zero-Collision Integration for Add-on Authors

Ensure zero shortcut conflicts for your users with zero friction:

### Option 1: Declarative Manifest (`shortcuts.json`) - 0 Lines of Python

Place a `shortcuts.json` at your add-on root (`addons21/<your_addon>/shortcuts.json`):

```json
{
  "schema_version": 1,
  "addon_name": "My Add-on Name",
  "shortcuts": [
    {
      "id": "my_addon.open_panel",
      "label": "Open Analysis Panel",
      "scope": "browser",
      "default": "Ctrl+Alt+A",
      "fallbacks": ["Ctrl+Shift+A", "Alt+A", "F10"],
      "config_key": "shortcut_open_panel"
    }
  ]
}
```

The enhanced manager maps declared shortcuts to the virtual keyboard and prevents overlapping bindings automatically.

### Option 2: Dynamic Broker API (`mw.shortcut_broker`) - Python

For add-ons that generate actions dynamically:

```python
from aqt import mw

broker = getattr(mw, "shortcut_broker", None)
if broker:
    shortcut_key = broker.claim(
        action_id="my_addon.open_panel",
        label="Open Analysis Panel",
        scope="browser",
        preferred=["Ctrl+Alt+P", "Ctrl+Shift+P", "Alt+P"],
        on_change=lambda new_key: my_action.setShortcut(new_key),
        addon_id="my_addon",
        addon_name="My Add-on Name"
    )
else:
    shortcut_key = "Ctrl+Alt+P"
```

See `DEVELOPER_PROTOCOL.md` for full schema details and examples.

---

## Installation

### Via AnkiWeb (Recommended)
1. In Anki, go to **Tools > Add-ons > Get Add-ons...**
2. Enter the Add-on Code: **353547840** (or upstream: **1762336370**)
3. Restart Anki.

### Manual Installation (.ankiaddon)
1. Download the `.ankiaddon` package from GitHub releases.
2. In Anki, go to **Tools > Add-ons > Install from file...**
3. Select the file and restart Anki.

---

## Compatibility

- Anki 2.1.50+ up to latest Anki 24.x / 25.x+
- Windows, macOS, and Linux
- Qt6 & Qt5 compatible
