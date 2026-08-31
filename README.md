# Anki Image Editor (Enhanced Edition)

An advanced image editing, cropping, and annotation add-on for Anki. It allows you to quickly crop, rotate, flip, annotate, and edit images directly within the Anki Note Editor without leaving your study workflow.

---

## Credits & Attribution

This project is an enhanced fork of the original work by community developers:
- **Original Author**: BlueGreenMagick ([GitHub Repository](https://github.com/BlueGreenMagick))
- **Upstream Fixes & Maintenance**: Shigeyuki ([AnkiWeb Add-on #789309990](https://ankiweb.net/shared/info/789309990) / [Patreon](http://patreon.com/Shigeyuki))
- **Enhanced Edition**: Developed with modern cropping tools, multi-language internationalization (i18n), floating popover integration, remote image handling, and performance optimizations.

---

## Comparison: Enhancements vs Original Add-on

| Feature | Original / Upstream (789309990) | Enhanced Edition |
| :--- | :--- | :--- |
| **Instant Cropper Tool** | Not available (only full SVG vector canvas) | **Built-in fast cropper** with aspect ratio presets (1:1, 4:3, 16:9, 3:2, Free), rotations (-90°/+90°), horizontal/vertical flips, and zoom controls |
| **Double-Click Workflow** | Not supported | **Double-click any image** in the note editor to instantly open the cropper dialog |
| **Floating Popover Button** | Not supported | **Automatic quick-action button** injected into Anki's floating image bubble menu |
| **Remote URLs & Base64** | Limited to local collection media files | **Full support for `http://`, `https://`, and `data:image/...`** base64 data URLs |
| **Hyperlink Preservation** | Could overwrite or strip enclosing anchor tags | **Preserves `<a>` links and attributes** intact when replacing edited images |
| **Internationalization (i18n)**| English only | **Full localization across 40+ Anki languages** (French, German, Spanish, Japanese, Chinese, Russian, Italian, Portuguese, Arabic, Korean, etc.) |
| **UTF-8 & Non-ASCII Filenames**| Risk of corrupted paths on special characters | **Robust TextDecoder UTF-8 parsing** for international filenames |
| **User Interface Aesthetics** | Basic interface elements | **Minimalist, sleek, sober UI** adhering to strict typography and distraction-free design |

---

## How to Use

### 1. Fast Cropping
- **Double-click** on any image in the note editor.
- Or click the **Image Editor** button on the floating image bubble popover.
- Adjust your crop area, select an aspect ratio preset, or use rotation/flip buttons.
- Press `Enter` or click **Save** to update the image in your card.

### 2. Full Vector Drawing & Annotation
- From the Cropper window, click **Full Editor (Shapes / Text)** to switch to the vector editor.
- Add arrows, shapes, text boxes, freehand drawings, or highlights on top of your image.
- Click **Save** to replace the image with the annotated SVG version.

### 3. Creating a New Drawing from Scratch
- With no image selected, click the **Image Editor** toolbar button or press `Ctrl + Shift + I`.
- Draw your diagram or illustration and click **Save** to insert it directly into your current field.

### 4. Right-Click Context Menu
- Right-click any image in the note editor and select **Image Editor (Crop / Edit)**.

---

## Keyboard Shortcuts

- `Ctrl + Shift + I`: Open Image Editor on selected image, or open a blank canvas if nothing is selected.
- `Enter` (in Cropper): Save the cropped image.
- `Esc` (in Cropper): Cancel and close dialog.

---

## Supported Languages

The add-on automatically detects your Anki language setting and provides native translations for:
- Arabic (`ar`)
- Bulgarian (`bg`)
- Catalan (`ca`)
- Czech (`cs`)
- Danish (`da`)
- Dutch (`nl`)
- English (`en`)
- Esperanto (`eo`)
- Estonian (`et`)
- Basque (`eu`)
- Persian (`fa`)
- Finnish (`fi`)
- French (`fr`)
- German (`de`)
- Greek (`el`)
- Hebrew (`he`)
- Croatian (`hr`)
- Hungarian (`hu`)
- Indonesian (`id`)
- Italian (`it`)
- Japanese (`ja`)
- Korean (`ko`)
- Malay (`ms`)
- Norwegian (`nb_NO`)
- Polish (`pl`)
- Portuguese / Brazil (`pt_BR`, `pt_PT`)
- Romanian (`ro`)
- Russian (`ru`)
- Slovak (`sk`)
- Slovenian (`sl`)
- Spanish (`es`)
- Serbian (`sr`)
- Swedish (`sv`)
- Thai (`th`)
- Turkish (`tr`)
- Ukrainian (`uk`)
- Vietnamese (`vi`)
- Chinese Simplified & Traditional (`zh_CN`, `zh_TW`)

---

## Compatibility

- Anki 2.1.20 through Anki 23.x / 24.x / 25.x+
- Compatible with both Qt5 and Qt6 builds
- Tested on Windows, macOS, and Linux

---

## License

This program is free software: you can redistribute it and/or modify it under the terms of the **GNU Affero General Public License (AGPLv3)** as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.