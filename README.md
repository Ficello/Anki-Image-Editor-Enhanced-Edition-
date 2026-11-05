# Image Editor (Enhanced Edition) - Fast Crop, Annotate & Draw

An advanced, high-performance image editing and cropping add-on for Anki. Crop, rotate, flip, annotate, and edit images directly within the Note Editor in seconds without interrupting your review or card creation workflow.

---

## Key Enhancements vs Original Add-on (789309990)

| Feature | Original Upstream (789309990) | Enhanced Edition |
| :--- | :--- | :--- |
| **Instant Cropper Tool** | Not available (only full SVG canvas) | **Built-in fast cropper** with aspect ratio presets (Free, 1:1, 4:3, 16:9, 3:2), lossless rotations (-90° / +90°), horizontal/vertical flips, and zoom |
| **Floating Bubble Integration** | Not supported | **Automatic quick-action button** injected directly into Anki's floating image popover |
| **Internationalization (i18n)** | English only | **Native translation into over 40 Anki languages** with automatic locale detection |
| **UTF-8 Handling** | Path corruption risk on accented characters | **Robust TextDecoder UTF-8 parsing** for international filenames |
| **Design & Ergonomics** | Cluttered dialogs | **Clean, distraction-free minimalist interface** (zero emojis) |

---

## Screenshot

![Fast Cropper Interface](https://raw.githubusercontent.com/Ficello/Anki-Image-Editor-Enhanced-Edition-/main/screenshots/01_cropper_modal.png)

---

## How to Use

1. **Floating Toolbar** : Select an image and click the Image Editor icon in the floating bubble toolbar.
2. **Context Menu** : Right-click any image and choose *Image Editor (Crop / Edit)*.
3. **Toolbar Button / Shortcut** : Press `Ctrl + Shift + I` to edit the selected image, or open a blank canvas to create a new vector drawing from scratch.
4. **Switch to Full Vector Editor** : From the Cropper, click *Full Editor (Shapes / Text)* to add arrows, text labels, shapes, and freehand drawings.

---

## Keyboard Shortcuts

| Shortcut | Context | Action |
| :--- | :--- | :--- |
| `Ctrl + Shift + I` | Editor | Open Image Editor on selected image (or create blank drawing) |
| `Enter` | Cropper Modal | Save and apply crop |
| `Esc` | Cropper Modal | Cancel and close dialog |

---

## Installation

### Via AnkiWeb (Recommended)
1. In Anki, go to **Tools > Add-ons > Get Add-ons...**
2. Enter the Add-on Code: **789309990** (or enhanced edition code: **1177622942**)
3. Restart Anki.

### Manual Installation (.ankiaddon)
1. Download the `.ankiaddon` package from GitHub releases.
2. In Anki, go to **Tools > Add-ons > Install from file...**
3. Select the file and restart Anki.

---

## Credits & Attribution

This add-on is an enhanced edition building upon the contributions of the Anki open-source community:
- Original author: **BlueGreenMagick** ([GitHub](https://github.com/BlueGreenMagick))
- Upstream maintainer: **Shigeyuki (Shige)** ([AnkiWeb 789309990](https://ankiweb.net/shared/info/789309990) / [Patreon](http://patreon.com/Shigeyuki))
- Enhanced edition & maintenance: **Ficello** ([GitHub Repository](https://github.com/Ficello/Anki-Image-Editor-Enhanced-Edition-))
- License: GNU Affero General Public License (AGPLv3)

---

## Compatibility

- Anki 2.1.20 up to Anki 23.x / 24.x / 25.x+
- Full Qt5 and Qt6 support
- Windows, macOS, and Linux
