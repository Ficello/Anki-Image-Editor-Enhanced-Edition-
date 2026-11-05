# Copyright (C) BlueGreenMagick 2020-2022 <https://github.com/BlueGreenMagick>
# Copyright (C) Shigeyuki 2025 <http://patreon.com/Shigeyuki>
# License: GNU AGPL version 3 or later <http://www.gnu.org/licenses/agpl.html>

import os
import base64
import json
import urllib.parse
from pathlib import Path

import anki.find
import aqt
from aqt import mw
from aqt.qt import *
from aqt.webview import AnkiWebView, AnkiWebPage
from aqt.utils import tooltip, askUserDialog, restoreGeom, saveGeom
from aqt.editor import Editor
from aqt.browser import Browser

from . import COMPAT
from .utils import get_config, set_config, checked
from .settings_dialog import get_tooltip_qss
from .i18n import tr

method_draw_path = os.path.join(
    os.path.dirname(__file__), "web", "Method-Draw", "editor", "index.html"
)

MIME_TYPE = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "bmp": "image/bmp",
    "ico": "image/vnd.microsoft.icon",
    "svg": "image/svg+xml",
    "avif": "image/avif"
}


class myPage(AnkiWebPage):
    def acceptNavigationRequest(self, url, navType, isMainFrame):
        "Needed so the link don't get opened in external browser"
        return True


class AnnotateDialog(QDialog):
    def __init__(self, editor: "Editor", name="", path="", src="", create_new=False, data_url="", skip_crop_init=False):
        super().__init__(editor.widget, Qt.WindowType.Window)
        mw.setupDialogGC(self)
        self.editor_wv = editor.web
        self.editor = editor
        self.image_name = name
        self.image_path = path
        self.image_src = src
        self.create_new = create_new
        self.data_url = data_url
        self.skip_crop_init = skip_crop_init
        self.close_queued = False
        self.setStyleSheet(get_tooltip_qss())

        if not create_new and not path and not data_url:
            self.check_editor_image_selected()
        self.setupUI()

    def closeEvent(self, evt):
        if self.close_queued:
            saveGeom(self, "addon_image_editor")
            if hasattr(mw, "annodial") and mw.annodial is self:
                del mw.annodial
            evt.accept()
        else:
            self.ask_on_close(evt)

    def setupUI(self):
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)

        addon_title = tr("addon_name")
        self.web = AnkiWebView(parent=self, title=addon_title)
        url = QUrl.fromLocalFile(method_draw_path)
        self.web._page = myPage(self.web._onBridgeCmd)
        self.web.setPage(self.web._page)
        self.web.setUrl(url)
        self.web.set_bridge_command(self.on_bridge_cmd, self)
        mainLayout.addWidget(self.web, stretch=1)

        btnLayout = QHBoxLayout()
        btnLayout.addStretch(1)

        replaceAll = QCheckBox(tr("chk_replace_all"))
        self.replaceAll = replaceAll
        ch = get_config("replace_all", hidden=True, notexist=False)
        replaceAll.setCheckState(checked(ch))
        replaceAll.stateChanged.connect(self.check_changed)
        btnLayout.addWidget(replaceAll)

        okButton = QPushButton(tr("btn_ok"))
        okButton.clicked.connect(self.save)
        btnLayout.addWidget(okButton)

        cancelButton = QPushButton(tr("btn_discard"))
        cancelButton.clicked.connect(self.discard)
        btnLayout.addWidget(cancelButton)

        resetButton = QPushButton(tr("btn_reset"))
        resetButton.clicked.connect(self.reset)
        btnLayout.addWidget(resetButton)

        okButton.setDefault(False)
        okButton.setAutoDefault(False)
        cancelButton.setDefault(False)
        cancelButton.setAutoDefault(False)
        resetButton.setDefault(False)
        resetButton.setAutoDefault(False)

        mainLayout.addLayout(btnLayout)

        self.setWindowTitle(addon_title)
        self.setMinimumWidth(300)
        self.setMinimumHeight(300)
        self.setGeometry(0, 0, 720, 680)
        restoreGeom(self, "addon_image_editor")
        if not self.close_queued:
            self.show()

    def check_changed(self, state: int):
        set_config("replace_all", bool(state), hidden=True)

    def discard(self):
        self.close_queued = True
        self.close()

    def save(self):
        self.close_queued = True
        self.web.eval("ankiAddonSaveImg()")

    def reset(self):
        self.load_img()

    def on_bridge_cmd(self, cmd):
        if cmd == "img_src":
            if not self.create_new:
                self.load_img()

        elif cmd.startswith("svg_save:"):
            if self.create_new:
                svg_str = cmd[len("svg_save:"):]
                self.create_svg(svg_str)
            else:
                svg_str = cmd[len("svg_save:"):]
                self.save_svg(svg_str)

    def check_editor_image_selected(self):
        def check_image_selected(selected):
            if selected == False:
                self.close_queued = True
                self.close()
                tooltip(tr("err_select_failed"), parent=self.editor.widget)

        self.editor_wv.evalWithCallback(
            "addonAnno.imageIsSelected()", check_image_selected)

    def load_img(self):
        # 1. Direct data URL (e.g. transferred from CropDialog)
        if self.data_url:
            mime_str = self.data_url.split(";")[0].replace("data:", "")
            img_format = mime_str.split("/")[-1].lower() if "/" in mime_str else "png"
            img_data = json.dumps(self.data_url)
            skip_crop_js = "true" if self.skip_crop_init else "false"
            self.web.eval(f"ankiAddonSetImg({img_data}, '{img_format}', {skip_crop_js})")
            return

        # 2. Handle external URL
        if self.image_src and (self.image_src.startswith("http://") or self.image_src.startswith("https://")):
            try:
                import urllib.request
                req = urllib.request.Request(
                    self.image_src,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )
                with urllib.request.urlopen(req, timeout=6) as resp:
                    raw_bytes = resp.read()
                    content_type = resp.headers.get("Content-Type", "")
                    if content_type and "image/" in content_type:
                        mime_str = content_type.split(";")[0]
                        img_format = mime_str.split("/")[-1].lower()
                    else:
                        img_format = self.image_src.split(".")[-1].split("?")[0].lower()
                        mime_str = MIME_TYPE.get(img_format, "image/png")
                    encoded_img_data = base64.b64encode(raw_bytes).decode("ascii")
                    img_data = f"'data:{mime_str};base64,{encoded_img_data}'"
                    skip_crop_js = "true" if self.skip_crop_init else "false"
                    self.web.eval(f"ankiAddonSetImg({img_data}, '{img_format}', {skip_crop_js})")
                    return
            except Exception as e:
                print(f"[AnnotateDialog] Error downloading external image: {e}")

        # 3. Handle local file
        if self.image_path:
            img_path = Path(self.image_path) if not isinstance(self.image_path, Path) else self.image_path
            if img_path.is_file():
                img_path_str = img_path.resolve().as_posix()
                img_format = img_path_str.split(".")[-1].lower()
                if img_format not in MIME_TYPE:
                    tooltip(tr("err_not_supported"), parent=self.editor.widget)
                    return

                if img_format == "svg":
                    img_data = json.dumps(img_path.read_text(encoding="utf-8"))
                else:
                    mime_str = MIME_TYPE[img_format]
                    encoded_img_data = base64.b64encode(img_path.read_bytes()).decode()
                    img_data = "'data:{};base64,{}'".format(mime_str, encoded_img_data)
                skip_crop_js = "true" if self.skip_crop_init else "false"
                self.web.eval("ankiAddonSetImg({}, '{}', {})".format(
                    img_data, img_format, skip_crop_js))
                return

        tooltip(tr("err_cannot_load"), parent=self.editor.widget)

    def create_svg(self, svg_str):
        "When creating an image from scratch"
        if COMPAT["write_data"]:
            new_name = mw.col.media.write_data(
                "svg_drawing.svg", svg_str.encode("utf-8"))
        else:
            new_name = mw.col.media.writeData(
                "svg_drawing.svg", svg_str.encode("utf-8"))
        img_el = '"<img src=\\"{}\\">"'.format(new_name)
        write_image_script = "document.execCommand('inserthtml', false, {});".format(img_el)
        self.editor_wv.evalWithCallback(
            write_image_script, 
            lambda res: not res and self.editor_wv.eval("focusField(0); setTimeout(() => {" + write_image_script + "},25)"))
        self.create_new = False
        self.image_path = Path(mw.col.media.dir()) / new_name
        tooltip(tr("image_created"), parent=self.editor.widget)
        if self.close_queued:
            self.close()

    def save_svg(self, svg_str):
        "When editing existing image"
        img_name = self.image_name or "image.svg"
        desired_name = ".".join(img_name.split(".")[:-1])
        desired_name = desired_name[:20] if len(desired_name) > 20 else desired_name
        desired_name += ".svg"
        desired_name = desired_name.replace(" ", "_").replace('"', "").replace("$", "")
        if not desired_name or desired_name == ".svg":
            desired_name = "annotated_image.svg"

        if COMPAT["write_data"]:
            new_name = mw.col.media.write_data(
                desired_name, svg_str.encode("utf-8"))
        else:
            new_name = mw.col.media.writeData(
                desired_name, svg_str.encode("utf-8"))

        if self.replaceAll.checkState() == Qt.CheckState.Checked:
            self.replace_img_src_webview(new_name, replace_all=True)
            is_add_mode = getattr(self.editor, "addMode", False)
            if is_add_mode:
                self.replace_all_img_src(img_name, new_name)
            else:
                cb = lambda s=self, i=img_name, n=new_name: s.replace_all_img_src(i, n)
                if hasattr(self.editor, "call_after_note_saved"):
                    self.editor.call_after_note_saved(cb)
                elif hasattr(self.editor, "saveNow"):
                    self.editor.saveNow(cb)
                else:
                    cb()
        else:
            self.replace_img_src_webview(new_name)
            tooltip(tr("save_success"), parent=self.editor.widget)

        if self.close_queued:
            self.close()

    def replace_img_src_webview(self, name: str, replace_all=False):
        namestr = base64.b64encode(str(name).encode("utf-8")).decode("ascii")
        if replace_all:
            self.editor_wv.eval("addonAnno.changeAllSrc('{}')".format(namestr))
        else:
            self.editor_wv.eval("addonAnno.changeSrc('{}')".format(namestr))

    def ask_on_close(self, evt):
        opts = [tr("btn_cancel"), tr("btn_discard"), tr("btn_ok")]
        diag = askUserDialog(tr("dialog_discard_msg"), opts, parent=self)
        diag.setDefault(0)
        ret = diag.run()
        if ret == opts[0]:
            evt.ignore()
        elif ret == opts[1]:
            saveGeom(self, "addon_image_editor")
            evt.accept()
        elif ret == opts[2]:
            self.save()
            saveGeom(self, "addon_image_editor")
            evt.ignore()

    def replace_all_img_src(self, orig_name: str, new_name: str):
        browser = aqt.dialogs._dialogs["Browser"][1] if "Browser" in aqt.dialogs._dialogs else None
        if browser and hasattr(browser, "model"):
            try:
                browser.model.beginReset()
            except Exception:
                pass

        cnt = self._replace_all_img_src(orig_name, new_name)

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

        tooltip(tr("replace_cnt_success", count=cnt), parent=self.editor.widget)

    def _replace_all_img_src(self, orig_name: str, new_name: str):
        names_to_replace = {orig_name}
        try:
            names_to_replace.add(urllib.parse.unquote(orig_name))
            names_to_replace.add(urllib.parse.quote(orig_name))
        except Exception:
            pass

        to_escape = r"\.+*?()|[]{}^$#&-~"
        nids = mw.col.findNotes("<img")
        total_cnt = 0

        for name in names_to_replace:
            escaped_name = "".join(("\\" + c) if c in to_escape else c for c in name)
            reg1 = r"""(?P<first><img[^>]* src=)(?:"{name}"|'{name}')(?P<second>[^>]*>)""".format(
                name=escaped_name
            )
            reg2 = r"""(?P<first><img[^>]* src=){name}(?P<second>(?: [^>]*>)|>)""".format(
                name=escaped_name
            )
            img_regs = [reg1]
            if " " not in name:
                img_regs.append(reg2)

            if COMPAT["find_replace"]:
                repl = """${first}"%s"${second}""" % new_name
            else:
                repl = """\\g<first>"%s"\\g<second>""" % new_name

            for reg in img_regs:
                try:
                    if COMPAT["find_replace"]:
                        res = mw.col.find_and_replace(
                            note_ids=nids,
                            search=reg,
                            replacement=repl,
                            regex=True,
                            match_case=False,
                            field_name=None,
                        )
                    else:
                        res = anki.find.findReplace(
                            col=mw.col, nids=nids, src=reg, dst=repl, regex=True, fold=False)
                    if COMPAT["find_replace_cnt"]:
                        total_cnt += res.count
                    else:
                        total_cnt += res
                except Exception as e:
                    print(f"[AnnotateDialog] replace error for {name}: {e}")

        return total_cnt
