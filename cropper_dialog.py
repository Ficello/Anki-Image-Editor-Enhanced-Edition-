import os
import base64
import json
import re
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional

import anki
from anki.utils import pointVersion
import aqt
from aqt import mw
from aqt.qt import *
from aqt.webview import AnkiWebView, AnkiWebPage
from aqt.utils import tooltip, restoreGeom, saveGeom
from aqt.editor import Editor

from .utils import get_config, set_config
from .settings_dialog import get_tooltip_qss
from .i18n import tr, get_all_translations

cropper_html_path = os.path.join(
    os.path.dirname(__file__), "web", "cropper", "index.html"
)

MIME_MAP = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "bmp": "image/bmp",
    "ico": "image/vnd.microsoft.icon",
    "svg": "image/svg+xml",
    "avif": "image/avif",
    "gif": "image/gif",
}


class CropperWebPage(AnkiWebPage):
    def acceptNavigationRequest(self, url, navType, isMainFrame):
        return True


class CropDialog(QDialog):
    def __init__(self, editor: Editor, name: str, path: str = "", src: str = ""):
        super().__init__(editor.widget, Qt.WindowType.Window)
        mw.setupDialogGC(self)
        self.editor = editor
        self.editor_wv = editor.web
        self.image_name = name
        self.image_path = path
        self.original_src = src or name
        self.image_data_url = ""
        self.mime_type = "image/png"

        self.setStyleSheet(get_tooltip_qss())
        self.prepare_image_data()
        self.setupUI()

    def prepare_image_data(self):
        src = self.original_src
        path = self.image_path

        # 1. Base64 data URL
        if src.startswith("data:image/"):
            self.image_data_url = src
            mime = src.split(";")[0].replace("data:", "")
            self.mime_type = mime
            return

        # 2. External URL (http:// or https://)
        if src.startswith("http://") or src.startswith("https://"):
            try:
                req = urllib.request.Request(
                    src,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )
                with urllib.request.urlopen(req, timeout=6) as resp:
                    raw_bytes = resp.read()
                    content_type = resp.headers.get("Content-Type", "")
                    if content_type and "image/" in content_type:
                        self.mime_type = content_type.split(";")[0]
                    else:
                        ext = src.split(".")[-1].split("?")[0].lower()
                        self.mime_type = MIME_MAP.get(ext, "image/png")

                    encoded = base64.b64encode(raw_bytes).decode("ascii")
                    self.image_data_url = f"data:{self.mime_type};base64,{encoded}"
                    return
            except Exception as e:
                print(f"[Image Cropper] Error fetching external image: {e}")

        # 3. Local file in media directory
        local_path = None
        if path and os.path.isfile(path):
            local_path = Path(path)
        elif self.image_name:
            cand = Path(mw.col.media.dir()) / self.image_name
            if cand.is_file():
                local_path = cand
            else:
                # Try unquoting URL-encoded names (e.g. %20 -> space)
                cand_unquoted = Path(mw.col.media.dir()) / urllib.parse.unquote(self.image_name)
                if cand_unquoted.is_file():
                    local_path = cand_unquoted

        if local_path and local_path.is_file():
            ext = local_path.suffix.lstrip(".").lower()
            self.mime_type = MIME_MAP.get(ext, "image/png")
            try:
                raw_bytes = local_path.read_bytes()
                encoded = base64.b64encode(raw_bytes).decode("ascii")
                self.image_data_url = f"data:{self.mime_type};base64,{encoded}"
                return
            except Exception as e:
                print(f"[Image Cropper] Error reading local image: {e}")

        self.image_data_url = ""

    def setupUI(self):
        self.setWindowTitle(tr("crop_window_title"))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.web = AnkiWebView(parent=self, title=tr("crop_window_title"))
        url = QUrl.fromLocalFile(cropper_html_path)
        self.web._page = CropperWebPage(self.web._onBridgeCmd)
        self.web.setPage(self.web._page)
        self.web.setUrl(url)
        self.web.set_bridge_command(self.on_bridge_cmd, self)
        layout.addWidget(self.web, stretch=1)

        self.setMinimumWidth(640)
        self.setMinimumHeight(480)
        self.resize(960, 680)
        restoreGeom(self, "addon_image_cropper")
        self.show()

    def closeEvent(self, evt):
        saveGeom(self, "addon_image_cropper")
        if hasattr(mw, "cropdial") and mw.cropdial is self:
            del mw.cropdial
        evt.accept()

    def on_bridge_cmd(self, cmd: str):
        if cmd == "crop_ready":
            replace_all = get_config("replace_all", hidden=True, notexist=False)
            default_ratio = get_config("default_ratio", notexist="free")
            default_filter = get_config("default_filter", notexist="none")
            translations = get_all_translations()
            js = (
                f"window.initCropperLocale({json.dumps(translations)});\n"
                f"window.loadCropImage("
                f"{json.dumps(self.image_data_url)}, "
                f"{json.dumps(self.image_name)}, "
                f"{json.dumps(self.mime_type)}, "
                f"{json.dumps(bool(replace_all))}"
                f");\n"
            )
            # Apply default ratio and filter if configured
            if default_ratio and default_ratio != "free":
                ratio_map = {"1:1": "1", "4:3": "1.333333", "16:9": "1.777778", "3:2": "1.5"}
                if default_ratio in ratio_map:
                    val = ratio_map[default_ratio]
                    js += f"setTimeout(() => {{ const b = document.querySelector('[data-ratio=\"{val}\"]'); if (b) b.click(); }}, 100);\n"
            if default_filter and default_filter != "none":
                js += f"setTimeout(() => {{ const sel = document.getElementById('select-filter'); if (sel) {{ sel.value = '{default_filter}'; sel.dispatchEvent(new Event('change')); }} }}, 100);\n"

            self.web.eval(js)

        elif cmd.startswith("crop_save:"):
            payload_str = cmd[len("crop_save:"):]
            try:
                payload = json.loads(payload_str)
                self.save_cropped_image(payload)
            except Exception as e:
                print(f"[Image Cropper] Save error: {e}")
                tooltip(tr("err_write_media", error=str(e)), parent=self.editor.widget)

        elif cmd.startswith("crop_open_full_editor"):
            data_url = ""
            if ":" in cmd:
                try:
                    payload = json.loads(cmd[len("crop_open_full_editor:"):])
                    data_url = payload.get("data", "")
                except Exception:
                    pass
            self.close()
            from .editor import open_annotate_window
            open_annotate_window(
                self.editor,
                name=self.image_name,
                path=self.image_path,
                src=self.original_src,
                data_url=data_url,
                skip_crop_init=True
            )

        elif cmd == "crop_cancel":
            self.close()

    def save_cropped_image(self, payload: dict):
        data_url = payload.get("data", "")
        filename = payload.get("filename", self.image_name) or "cropped_image.png"
        replace_all = payload.get("replaceAll", False)
        set_config("replace_all", bool(replace_all), hidden=True)

        if not data_url or "," not in data_url:
            tooltip(tr("err_invalid_data"), parent=self.editor.widget)
            return

        header, b64data = data_url.split(",", 1)
        image_bytes = base64.b64decode(b64data)

        # Determine extension from MIME or filename
        ext = ".png"
        if "image/jpeg" in header:
            ext = ".jpg"
        elif "image/webp" in header:
            ext = ".webp"
        elif "." in filename:
            cand_ext = "." + filename.split(".")[-1].split("?")[0].lower()
            if cand_ext in [".png", ".jpg", ".jpeg", ".webp"]:
                ext = cand_ext

        base_name = os.path.splitext(filename)[0]
        # Preserve Unicode characters (accents, numbers, letters) while stripping illegal filesystem chars
        base_name = re.sub(r'[^\w\-\.]', '_', base_name, flags=re.UNICODE)[:40]
        if not base_name or base_name == "_":
            base_name = "cropped_image"

        target_name = f"{base_name}{ext}"

        # Write to Anki collection.media
        try:
            if hasattr(mw.col.media, "write_data"):
                new_media_name = mw.col.media.write_data(target_name, image_bytes)
            else:
                new_media_name = mw.col.media.writeData(target_name, image_bytes)
        except Exception as e:
            print(f"[Image Cropper] Error writing media: {e}")
            tooltip(tr("err_write_media", error=str(e)), parent=self.editor.widget)
            return

        # Replace in Editor webview
        self.apply_replacement_to_editor(self.original_src, new_media_name, replace_all)

        tooltip(tr("crop_save_success"), parent=self.editor.widget)
        self.close()

    def apply_replacement_to_editor(self, old_src: str, new_name: str, replace_all: bool):
        # 1. Update JS DOM in the active note editor immediately
        old_src_b64 = base64.b64encode(old_src.encode("utf-8")).decode("ascii")
        new_name_b64 = base64.b64encode(new_name.encode("utf-8")).decode("ascii")

        js_code = f"addonAnno.changeSpecificSrc('{old_src_b64}', '{new_name_b64}', {json.dumps(replace_all)});"
        self.editor_wv.eval(js_code)

        # 2. If replace_all is selected and not in addMode, replace across notes in database
        is_add_mode = getattr(self.editor, "addMode", False)
        if replace_all and not is_add_mode:
            cb = lambda s=self, o=old_src, n=new_name: s.replace_across_collection(o, n)
            if hasattr(self.editor, "call_after_note_saved"):
                self.editor.call_after_note_saved(cb)
            elif hasattr(self.editor, "saveNow"):
                self.editor.saveNow(cb)
            else:
                cb()

    def replace_across_collection(self, orig_src: str, new_name: str):
        browser = aqt.dialogs._dialogs["Browser"][1] if "Browser" in aqt.dialogs._dialogs else None
        if browser and hasattr(browser, "model"):
            try:
                browser.model.beginReset()
            except Exception:
                pass

        # Prepare regex escaping for both raw and URL-encoded variations
        clean_name = self.image_name or orig_src
        names_to_replace = {clean_name}
        try:
            unquoted = urllib.parse.unquote(clean_name)
            quoted = urllib.parse.quote(clean_name)
            names_to_replace.add(unquoted)
            names_to_replace.add(quoted)
        except Exception:
            pass

        to_escape = r"\.+*?()|[]{}^$#&-~"
        total_cnt = 0
        nids = mw.col.findNotes("<img")

        for nm in names_to_replace:
            escaped_src = "".join(("\\" + c) if c in to_escape else c for c in nm)
            reg = r"""(?P<first><img[^>]* src=)(?:"{src}"|'{src}'|{src})(?P<second>[^>]*>)""".format(
                src=escaped_src
            )
            repl = """${first}"%s"${second}""" % new_name

            try:
                res = mw.col.find_and_replace(
                    note_ids=nids,
                    search=reg,
                    replacement=repl,
                    regex=True,
                    match_case=False,
                    field_name=None,
                )
                cnt = res.count if hasattr(res, "count") else res
                total_cnt += cnt
            except Exception as e:
                print(f"[Image Cropper] replace_across_collection error for {nm}: {e}")

        if hasattr(self.editor, "loadNoteKeepingFocus"):
            try:
                self.editor.loadNoteKeepingFocus()
            except Exception:
                pass
        elif not getattr(self.editor, "addMode", False):
            mw.requireReset()

        if browser and hasattr(browser, "model"):
            try:
                browser.model.endReset()
            except Exception:
                pass

        tooltip(tr("replace_cnt_success", count=total_cnt), parent=self.editor.widget)
