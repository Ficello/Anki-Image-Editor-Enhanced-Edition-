# Copyright (C) BlueGreenMagick 2020-2022 <https://github.com/BlueGreenMagick>
# Copyright (C) Shigeyuki 2025 <http://patreon.com/Shigeyuki>
# License: GNU AGPL version 3 or later <http://www.gnu.org/licenses/agpl.html>

import os
import json
from pathlib import Path
from urllib.parse import unquote
from typing import Any

import anki
from anki.hooks import addHook
from aqt import mw
from aqt.editor import EditorWebView, Editor
import aqt.editor
EDITOR_CLASSES = (Editor, getattr(aqt.editor, "NewEditor", Editor))
WEBVIEW_CLASSES = (EditorWebView, getattr(aqt.editor, "NewEditorWebView", EditorWebView))
from aqt.utils import tooltip
from aqt.qt import QMenu, QT_VERSION_STR
from aqt import gui_hooks
from aqt.webview import WebContent

from .annotation import AnnotateDialog
from .cropper_dialog import CropDialog
from .utils import get_config
from .i18n import tr

ADDON_PACKAGE = mw.addonManager.addonFromModule(__name__) or "789309990"
ICONS_PATH = os.path.join(os.path.dirname(__file__), "icons")
QT6 = QT_VERSION_STR.split(".")[0] == "6"


def open_annotate_window(editor: Editor, name="", path="", src="", create_new=False, data_url="", skip_crop_init=False):
    mw.annodial = AnnotateDialog(
        editor, name=name, path=path, src=src, create_new=create_new, data_url=data_url, skip_crop_init=skip_crop_init
    )


def open_crop_window(editor: Editor, name="", path="", src=""):
    mw.cropdial = CropDialog(
        editor, name=name, path=path, src=src
    )


def handle_open_image(editor: Editor, raw_src: str):
    if "/" in raw_src:
        image_name = raw_src.split("/")[-1].split("?")[0]
    elif "\\" in raw_src:
        image_name = raw_src.split("\\")[-1].split("?")[0]
    else:
        image_name = raw_src.split("?")[0]

    is_external = raw_src.startswith("http://") or raw_src.startswith("https://") or raw_src.startswith("data:image/")
    image_path = Path(mw.col.media.dir()) / image_name if not is_external and image_name else None
    path_str = str(image_path) if (image_path and image_path.is_file()) else ""

    if path_str or is_external:
        open_crop_window(editor, name=image_name, path=path_str, src=raw_src)
    else:
        tooltip(tr("err_image_not_found", name=image_name), parent=editor.widget)


def add_context_menu_action(wv: EditorWebView, m: QMenu):
    if QT6:
        context_data = wv.lastContextMenuRequest()
    else:
        context_data = wv.page().contextMenuData()
    url = context_data.mediaUrl()
    raw_url_str = url.toString() if url.isValid() else ""
    image_name = url.fileName() if url.isValid() else ""

    image_path = Path(mw.col.media.dir()) / image_name if image_name else None
    is_local = image_path and image_path.is_file()
    is_external = raw_url_str.startswith("http://") or raw_url_str.startswith("https://")

    if url.isValid() and (is_local or is_external):
        path_str = str(image_path) if is_local else ""

        edit_act = m.addAction(tr("edit_image_menu"))
        edit_act.triggered.connect(
            lambda _, path=path_str, nm=image_name, src=raw_url_str: open_crop_window(
                wv.editor, name=nm, path=path, src=src
            )
        )


def handle_webview_message(handled: tuple[bool, Any], message: str, context: Any) -> tuple[bool, Any]:
    if message == "addonAnno_editSelected":
        editor = None
        if isinstance(context, EDITOR_CLASSES):
            editor = context
        elif isinstance(context, WEBVIEW_CLASSES):
            editor = getattr(context, "editor", None)
        if editor:
            on_toolbar_button_clicked(editor)
            return (True, None)

    if message.startswith("addonAnno_cropImage:") or message.startswith("addonAnno_editImage:"):
        is_full_draw = message.startswith("addonAnno_editImage:")
        prefix_len = len("addonAnno_editImage:") if is_full_draw else len("addonAnno_cropImage:")
        raw_src = unquote(message[prefix_len:])

        if "/" in raw_src:
            image_name = raw_src.split("/")[-1].split("?")[0]
        elif "\\" in raw_src:
            image_name = raw_src.split("\\")[-1].split("?")[0]
        else:
            image_name = raw_src.split("?")[0]

        is_external = raw_src.startswith("http://") or raw_src.startswith("https://") or raw_src.startswith("data:image/")
        image_path = Path(mw.col.media.dir()) / image_name if not is_external and image_name else None

        editor = None
        if isinstance(context, EDITOR_CLASSES):
            editor = context
        elif isinstance(context, WEBVIEW_CLASSES):
            editor = getattr(context, "editor", None)
        elif hasattr(mw, "app"):
            for widget in mw.app.topLevelWidgets():
                if hasattr(widget, "editor") and isinstance(widget.editor, EDITOR_CLASSES):
                    editor = widget.editor
                    break

        if not editor:
            return handled

        path_str = str(image_path) if (image_path and image_path.is_file()) else ""

        if path_str or is_external:
            if is_full_draw:
                open_annotate_window(editor, name=image_name, path=path_str, src=raw_src)
            else:
                open_crop_window(editor, name=image_name, path=path_str, src=raw_src)
            return (True, None)
        else:
            tooltip(tr("err_image_not_found", name=image_name), parent=editor.widget)
            return (True, None)

    return handled


def insert_js(web_content: "WebContent", context):
    if not isinstance(context, EDITOR_CLASSES):
        return
    web_content.js.append(f"/_addons/{ADDON_PACKAGE}/web/editor.js")


def on_toolbar_button_clicked(editor: Editor):
    def callback(selected_src):
        if selected_src:
            handle_open_image(editor, selected_src)
        else:
            open_annotate_window(editor, create_new=True)

    editor.web.evalWithCallback("addonAnno.getSelectedImageSrc()", callback)


def setup_editor_buttons(btns, editor: "Editor"):
    hotkey = get_config("shortcut_editor", notexist="Ctrl+Shift+I")
    broker = getattr(mw, "shortcut_broker", None)
    if broker and hasattr(broker, "claim"):
        try:
            hotkey = broker.claim(
                action_id="image_editor.edit",
                label=tr("toolbar_tooltip"),
                scope="editor",
                preferred=[hotkey, "Ctrl+Shift+I", "Ctrl+Alt+I", "F10"],
                addon_id=ADDON_PACKAGE,
                addon_name="Image Editor Enhanced"
            )
        except Exception:
            pass
    icon = os.path.join(ICONS_PATH, "draw.svg")
    b = editor.addButton(icon, "Image Editor",
                         lambda o=editor: on_toolbar_button_clicked(o),
                         tip=tr("toolbar_tooltip"),
                         keys=hotkey, disables=True)
    btns.append(b)
    return btns


def on_editor_note_load(js: str, note: anki.notes.Note, editor: Editor):
    action_label = tr("edit_image_menu")
    js += f"\nif (window.addonAnno) {{ addonAnno.actionBtnTitle = {json.dumps(action_label)}; addonAnno.addListener(); }}"
    return js


def on_config():
    from .settings_dialog import open_settings_dialog
    open_settings_dialog()


def register_with_shared_menu():
    try:
        if hasattr(mw, "_edn_registered_modules"):
            if "image_editor" not in mw._edn_registered_modules:
                mw._edn_registered_modules["image_editor"] = {
                    "name": "Image Editor Enhanced",
                    "description": "Éditeur, recadreur et annotateur d'illustrations médicales"
                }
    except Exception:
        pass


register_with_shared_menu()
mw.addonManager.setWebExports(__name__, r"web/editor.js")
mw.addonManager.setConfigAction(__name__, on_config)
addHook("EditorWebView.contextMenuEvent", add_context_menu_action)
addHook('setupEditorButtons', setup_editor_buttons)
gui_hooks.webview_will_set_content.append(insert_js)
gui_hooks.editor_will_load_note.append(on_editor_note_load)
gui_hooks.webview_did_receive_js_message.append(handle_webview_message)
