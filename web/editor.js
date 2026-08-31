(function () {
  let targetEl = { tagName: "" };
  let targetElOrd = 0;
  let targetField = null;
  const addonAnno = {};

  function verIsOver50() {
    return !(typeof getCurrentField === "function");
  }

  function getFromSvelteStore(store) {
    let v;
    const unsubscribe = store.subscribe((i) => {
      v = i;
    });
    unsubscribe();
    return v;
  }

  function currentField() {
    if (typeof getCurrentField === "function") {
      const fieldEl = window.getCurrentField();
      if (!fieldEl) return null;
      return fieldEl.shadowRoot || fieldEl;
    } else {
      // 2.1.50+
      try {
        const noteEditor = window.require("anki/NoteEditor").instances[0];
        const noteInput = getFromSvelteStore(noteEditor.focusedInput);
        if (noteInput === null) return null;
        return noteInput.element;
      } catch (e) {
        return null;
      }
    }
  }

  async function getFieldElements() {
    let fields = [];
    if (!verIsOver50()) {
      const fieldEls = document.getElementsByClassName("field");
      for (const el of fieldEls) {
        fields.push(el.shadowRoot || el);
      }
    } else {
      // 2.1.50+
      try {
        await window.require("anki/ui").loaded;
        const noteFields = window.require("anki/NoteEditor").instances[0].fields;
        fields = await Promise.all(
          noteFields.map((field) => {
            return getFromSvelteStore(field.editingArea.editingInputs)[0].element;
          })
        );
      } catch (e) {
        const fieldEls = document.querySelectorAll(".rich-text-input, .field, [contenteditable='true']");
        for (const el of fieldEls) {
          fields.push(el.shadowRoot || el);
        }
      }
    }
    return fields;
  }

  function updateTargetImage(img, field) {
    targetEl = img;
    if (field) {
      targetField = field;
      const images = field.getElementsByTagName("img");
      for (let i = 0; i < images.length; i++) {
        if (images[i] === img) {
          targetElOrd = i;
          break;
        }
      }
    }
  }

  function getActiveImage() {
    if (targetEl && targetEl.tagName === "IMG") {
      return targetEl;
    }
    return document.querySelector("img.ProseMirror-selectednode") ||
           (targetField && targetField.querySelector("img")) ||
           document.querySelector(".field img, [contenteditable='true'] img");
  }

  // Returns selected image src for Ctrl+Shift+I or null
  addonAnno.getSelectedImageSrc = function () {
    // 1. If user clicked on an image
    if (targetEl && targetEl.tagName === "IMG") {
      return targetEl.getAttribute("src") || targetEl.src;
    }
    // 2. If an image is selected in ProseMirror
    const selNode = document.querySelector("img.ProseMirror-selectednode");
    if (selNode) {
      targetEl = selNode;
      return selNode.getAttribute("src") || selNode.src;
    }
    // 3. If selection contains an image
    const sel = window.getSelection();
    if (sel && sel.anchorNode) {
      const parent = sel.anchorNode.nodeType === 1 ? sel.anchorNode : sel.anchorNode.parentElement;
      if (parent) {
        const img = parent.tagName === "IMG" ? parent : parent.querySelector("img");
        if (img) {
          targetEl = img;
          return img.getAttribute("src") || img.src;
        }
      }
    }
    return null;
  };

  addonAnno.openCropperForImage = function (img) {
    const target = img || getActiveImage();
    if (!target) return;
    const rawSrc = target.getAttribute("src") || target.src;
    if (typeof pycmd === "function") {
      pycmd("addonAnno_cropImage:" + encodeURIComponent(rawSrc));
    }
  };

  addonAnno.openFullEditorForImage = function (img) {
    const target = img || getActiveImage();
    if (!target) return;
    const rawSrc = target.getAttribute("src") || target.src;
    if (typeof pycmd === "function") {
      pycmd("addonAnno_editImage:" + encodeURIComponent(rawSrc));
    }
  };

  addonAnno.addListener = async function () {
    const fields = await getFieldElements();
    for (const field of fields) {
      if (!field) continue;

      const onImageEvent = function (e) {
        if (e.target && e.target.tagName === "IMG") {
          updateTargetImage(e.target, field);
        }
      };

      field.addEventListener("contextmenu", onImageEvent);
      field.addEventListener("click", onImageEvent);
      field.addEventListener("mousedown", onImageEvent);
    }

    startPopoverObserver();
  };

  const selectedIsImage = function () {
    return targetEl && targetEl.tagName === "IMG";
  };

  const hasSingleImage = function () {
    const field = currentField();
    if (!field) {
      return false;
    }
    return field.querySelectorAll("img").length === 1;
  };

  addonAnno.imageIsSelected = function () {
    if (selectedIsImage()) return true;
    const sel = document.querySelector("img.ProseMirror-selectednode");
    if (sel) {
      targetEl = sel;
      return true;
    }
    return hasSingleImage();
  };

  addonAnno.getSrc = function () {
    if (targetEl && targetEl.tagName === "IMG") {
      return targetEl.getAttribute("src") || targetEl.src;
    }
    return null;
  };

  const targetImage = function () {
    return verIsOver50() && targetField
      ? targetField.getElementsByTagName("img")[targetElOrd] || targetEl
      : targetEl;
  };

  // Precisely replace src while keeping <a> tag, hyperlinks, and other metadata intact!
  addonAnno.changeSpecificSrc = async function (oldSrcB64, newNameB64, replaceAll) {
    const oldSrc = new TextDecoder().decode(Uint8Array.from(atob(oldSrcB64), c => c.charCodeAt(0)));
    const newName = new TextDecoder().decode(Uint8Array.from(atob(newNameB64), c => c.charCodeAt(0)));

    const fields = await getFieldElements();
    let replaced = false;

    for (const field of fields) {
      if (!field) continue;
      const imgs = field.querySelectorAll("img");
      for (const img of imgs) {
        const currentSrc = img.getAttribute("src") || img.src;
        if (replaceAll) {
          if (currentSrc === oldSrc || img.src === oldSrc || currentSrc.endsWith(oldSrc)) {
            img.setAttribute("src", newName);
            img.src = newName;
            replaced = true;
          }
        } else {
          if (img === targetImage() || (!replaced && (currentSrc === oldSrc || img.src === oldSrc))) {
            img.setAttribute("src", newName);
            img.src = newName;
            replaced = true;
            break;
          }
        }
      }
    }
  };

  addonAnno.changeAllSrc = async function (src) {
    const newSrc = new TextDecoder().decode(Uint8Array.from(atob(src), c => c.charCodeAt(0)));
    const oldSrc = targetImage() ? (targetImage().getAttribute("src") || targetImage().src) : "";
    const fields = await getFieldElements();
    for (const field of fields) {
      if (!field) continue;
      const imgs = field.querySelectorAll("img");
      for (const img of imgs) {
        if ((img.getAttribute("src") || img.src) === oldSrc) {
          img.setAttribute("src", newSrc);
          img.src = newSrc;
        }
      }
    }
  };

  addonAnno.changeSrc = function (src) {
    const decoded = new TextDecoder().decode(Uint8Array.from(atob(src), c => c.charCodeAt(0)));
    const img = targetImage();
    if (img) {
      img.setAttribute("src", decoded);
      img.src = decoded;
    }
  };

  // --- Popover and UI Button Injection ---
  function createActionButton(title, iconSvg, onClick) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn-addon-anno-action";
    btn.title = title;
    btn.setAttribute("aria-label", title);

    btn.style.display = "inline-flex";
    btn.style.alignItems = "center";
    btn.style.justifyContent = "center";
    btn.style.background = "transparent";
    btn.style.border = "none";
    btn.style.borderRadius = "4px";
    btn.style.cursor = "pointer";
    btn.style.padding = "4px 6px";
    btn.style.margin = "0 1px";
    btn.style.color = "currentColor";
    btn.style.transition = "background-color 0.15s ease";

    btn.innerHTML = iconSvg;

    btn.addEventListener("mouseenter", () => {
      btn.style.backgroundColor = "rgba(128, 128, 128, 0.25)";
    });
    btn.addEventListener("mouseleave", () => {
      btn.style.backgroundColor = "transparent";
    });

    btn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      onClick();
    });

    return btn;
  }

  function isFloatingImagePopover(el) {
    if (!el || !el.querySelectorAll) return false;

    // STRICT CHECK: Never touch top bar, main toolbar, or field containers!
    if (el.closest(".toolbar, #top-bar, .editor-toolbar, .fields, header, #header")) {
      return false;
    }

    const isPopupContainer = el.matches(".popover, .bubble-menu, [role='tooltip'], [role='dialog'], .tippy-content, .tippy-box, .editor-popover, [data-popover], [data-tippy-root]") ||
                            el.closest(".popover, .bubble-menu, [role='tooltip'], [role='dialog'], .tippy-content, .tippy-box, .editor-popover, [data-popover], [data-tippy-root]");
    
    if (!isPopupContainer) {
      try {
        const style = window.getComputedStyle(el);
        if (style.position !== "absolute" && style.position !== "fixed") {
          return false;
        }
      } catch (e) {
        return false;
      }
    }

    const buttons = el.querySelectorAll("button");
    return buttons.length >= 2;
  }

  function checkAndInjectButtons(root) {
    if (!root || !root.querySelectorAll) return;

    const popoverCandidates = root.querySelectorAll(".popover, .bubble-menu, [role='tooltip'], [role='dialog'], .tippy-content, .editor-popover, [data-popover]");

    popoverCandidates.forEach(container => {
      if (!isFloatingImagePopover(container)) return;
      if (container.querySelector(".btn-addon-anno-action")) return;

      // Exact draw.svg icon for uniform appearance across Anki
      const drawIconSvg = `
        <svg width="18" height="18" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
          <g>
            <rect stroke-width="1.5" fill="none" stroke="currentColor" x="2.9" y="3.9" width="20.1" height="26.2" rx="1"/>
            <path stroke-width="1.5" fill="none" stroke="currentColor" d="m16 25c0 0-14.1 7.2-5.3-4.5c8.8-11.7-4.7-2.8-4.8-2.9"/>
            <path stroke-width="1.5" fill="currentColor" stroke="currentColor" d="m28.7 7.3l-2.2-1.4c-0.6-0.3-1.3-0.2-1.6 0.4l-0.9 1.4l4.2 2.6l0.9-1.4c0.3-0.5 0.2-1.3-0.4-1.6zm-12.4 12.4l4.5 2.2l6.8-10.7l-4.2-2.6l-6.8 10.7zm-0.7 3.3l-0.1 2.4l2.2-1.1l2-1.1l-4.1-2.5l-0.1 2.3z"/>
          </g>
        </svg>
      `;
      const btnTitle = addonAnno.actionBtnTitle || "Image Editor (Crop / Edit)";
      const editBtn = createActionButton(btnTitle, drawIconSvg, () => {
        addonAnno.openCropperForImage();
      });

      container.appendChild(editBtn);
    });
  }

  let observerStarted = false;
  function startPopoverObserver() {
    if (observerStarted) return;
    observerStarted = true;

    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.addedNodes.length) {
          checkAndInjectButtons(document.body);
          for (const node of mutation.addedNodes) {
            if (node.nodeType === 1) {
              checkAndInjectButtons(node);
              if (node.shadowRoot) {
                checkAndInjectButtons(node.shadowRoot);
              }
            }
          }
        }
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
    checkAndInjectButtons(document.body);
  }

  window.addonAnno = addonAnno;
})();
