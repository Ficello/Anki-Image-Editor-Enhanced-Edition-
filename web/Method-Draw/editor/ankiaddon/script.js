/*
 * Integrated Crop & Anki Bridge for Method-Draw
 */

(function () {
  let isCropMode = false;
  let cropBox = { x: 0, y: 0, w: 0, h: 0 };
  let currentRatio = "free";
  let isDragging = false;
  let dragType = null; // 'move', 'nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'
  let startMouse = { x: 0, y: 0 };
  let startBox = { x: 0, y: 0, w: 0, h: 0 };

  // --- Initialize UI Elements ---
  function setupCropUI() {
    if (document.getElementById("tool_crop")) return;

    // 1. Add Tool Button to Tools Left
    const toolsLeft = document.getElementById("tools_left");
    if (toolsLeft) {
      const cropBtn = document.createElement("div");
      cropBtn.className = "tool_button";
      cropBtn.id = "tool_crop";
      cropBtn.title = "Rogner l'image [C] (Crop Tool)";
      cropBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M6 2v14a2 2 0 0 0 2 2h14"></path>
          <path d="M18 22V8a2 2 0 0 0-2-2H2"></path>
        </svg>
      `;
      cropBtn.addEventListener("click", function (e) {
        e.preventDefault();
        enableCropMode();
      });
      // Insert as the very first tool
      toolsLeft.insertBefore(cropBtn, toolsLeft.firstChild);
    }

    // 2. Add Crop Context Panel to Tools Top
    const toolsTop = document.getElementById("tools_top");
    if (toolsTop) {
      const cropPanel = document.createElement("div");
      cropPanel.id = "crop_panel";
      cropPanel.className = "context_panel";
      cropPanel.innerHTML = `
        <h4 style="color:#eee; margin:0; font-size:13px; font-weight:600;">Rogner</h4>
        <button id="btn_apply_crop" class="btn_crop_action primary" title="Appliquer le rognage (Entrée)">✓ Appliquer (Entrée)</button>
        <button id="btn_reset_crop" class="btn_crop_action secondary" title="Tout sélectionner">✕ Tout sélectionner</button>
        <label style="display:inline-flex; align-items:center; gap:4px; font-size:12px; color:#ccc; margin-left:8px;">
          Ratio:
          <select id="crop_ratio_select" style="background:#222; color:#fff; border:1px solid #555; padding:2px 6px; border-radius:4px; font-size:12px;">
            <option value="free" selected>Libre</option>
            <option value="1:1">1:1 (Carré)</option>
            <option value="4:3">4:3</option>
            <option value="16:9">16:9</option>
            <option value="3:2">3:2</option>
          </select>
        </label>
        <span id="crop_dims_badge" style="font-size:12px; color:#aaa; margin-left:8px; font-variant-numeric:tabular-nums;"></span>
      `;
      toolsTop.appendChild(cropPanel);

      document.getElementById("btn_apply_crop").addEventListener("click", applyCrop);
      document.getElementById("btn_reset_crop").addEventListener("click", resetCropBoxToCanvas);
      document.getElementById("crop_ratio_select").addEventListener("change", function () {
        currentRatio = this.value;
        adjustBoxToRatio();
        updateCropOverlayDOM();
      });
    }

    // 3. Add Crop Overlay to SVG Canvas
    const svgCanvasEl = document.getElementById("svgcanvas");
    if (svgCanvasEl && !document.getElementById("crop_overlay")) {
      const overlay = document.createElement("div");
      overlay.id = "crop_overlay";
      overlay.style.display = "none";
      overlay.innerHTML = `
        <div id="crop_box">
          <div class="crop-grid-h" style="top: 33.33%;"></div>
          <div class="crop-grid-h" style="top: 66.66%;"></div>
          <div class="crop-grid-v" style="left: 33.33%;"></div>
          <div class="crop-grid-v" style="left: 66.66%;"></div>
          <div class="crop-handle handle-nw" data-handle="nw"></div>
          <div class="crop-handle handle-n" data-handle="n"></div>
          <div class="crop-handle handle-ne" data-handle="ne"></div>
          <div class="crop-handle handle-e" data-handle="e"></div>
          <div class="crop-handle handle-se" data-handle="se"></div>
          <div class="crop-handle handle-s" data-handle="s"></div>
          <div class="crop-handle handle-sw" data-handle="sw"></div>
          <div class="crop-handle handle-w" data-handle="w"></div>
        </div>
      `;
      svgCanvasEl.appendChild(overlay);

      setupCropMouseHandlers(overlay);
    }

    // 4. Listen to clicks on other tools to exit crop mode gracefully
    $("#tools_left .tool_button").not("#tool_crop").on("click", function () {
      if (isCropMode) {
        disableCropMode();
      }
    });

    // 5. Global Keyboard Shortcuts
    window.addEventListener("keydown", function (e) {
      if (isCropMode) {
        if (e.key === "Enter") {
          e.preventDefault();
          e.stopPropagation();
          applyCrop();
        } else if (e.key === "Escape") {
          e.preventDefault();
          e.stopPropagation();
          disableCropMode();
        }
      } else {
        if (e.key === "c" || e.key === "C") {
          if (document.activeElement && (document.activeElement.tagName === "INPUT" || document.activeElement.tagName === "TEXTAREA")) return;
          enableCropMode();
        }
      }
    });
  }

  // --- Crop Box Geometry & Ratio ---
  function getCanvasResolution() {
    if (typeof svgCanvas !== "undefined" && svgCanvas.getResolution) {
      return svgCanvas.getResolution();
    }
    return {
      w: parseFloat($("#canvas_width").val()) || 640,
      h: parseFloat($("#canvas_height").val()) || 480,
      zoom: (typeof svgCanvas !== "undefined" && svgCanvas.getZoom) ? svgCanvas.getZoom() : 1
    };
  }

  function resetCropBoxToCanvas() {
    const res = getCanvasResolution();
    // Full canvas bounds in SVG coordinates
    cropBox = {
      x: 0,
      y: 0,
      w: Math.round(res.w),
      h: Math.round(res.h)
    };
    adjustBoxToRatio();
    updateCropOverlayDOM();
  }

  function adjustBoxToRatio() {
    if (currentRatio === "free") return;
    const parts = currentRatio.split(":");
    if (parts.length !== 2) return;
    const targetRatio = parseFloat(parts[0]) / parseFloat(parts[1]);

    const res = getCanvasResolution();
    let newW = cropBox.w;
    let newH = Math.round(newW / targetRatio);

    if (newH > res.h) {
      newH = res.h;
      newW = Math.round(newH * targetRatio);
    }
    cropBox.w = newW;
    cropBox.h = newH;
    cropBox.x = Math.max(0, Math.min(cropBox.x, res.w - cropBox.w));
    cropBox.y = Math.max(0, Math.min(cropBox.y, res.h - cropBox.h));
  }

  function updateCropOverlayDOM() {
    const overlay = document.getElementById("crop_overlay");
    const boxEl = document.getElementById("crop_box");
    const dimsBadge = document.getElementById("crop_dims_badge");
    if (!overlay || !boxEl) return;

    const zoom = (typeof svgCanvas !== "undefined" && svgCanvas.getZoom) ? svgCanvas.getZoom() : 1;

    boxEl.style.left = (cropBox.x * zoom) + "px";
    boxEl.style.top = (cropBox.y * zoom) + "px";
    boxEl.style.width = (cropBox.w * zoom) + "px";
    boxEl.style.height = (cropBox.h * zoom) + "px";

    if (dimsBadge) {
      dimsBadge.textContent = `${Math.round(cropBox.w)} × ${Math.round(cropBox.h)} px`;
    }
  }

  // --- Mouse Drag and Resize Handlers ---
  function setupCropMouseHandlers(overlay) {
    const boxEl = document.getElementById("crop_box");

    boxEl.addEventListener("mousedown", function (e) {
      const handle = e.target.dataset.handle;
      isDragging = true;
      dragType = handle || "move";
      startMouse = { x: e.clientX, y: e.clientY };
      startBox = { ...cropBox };
      e.preventDefault();
      e.stopPropagation();
    });

    window.addEventListener("mousemove", function (e) {
      if (!isDragging) return;

      const zoom = (typeof svgCanvas !== "undefined" && svgCanvas.getZoom) ? svgCanvas.getZoom() : 1;
      const dx = (e.clientX - startMouse.x) / zoom;
      const dy = (e.clientY - startMouse.y) / zoom;
      const res = getCanvasResolution();

      let { x, y, w, h } = startBox;

      if (dragType === "move") {
        x = Math.max(0, Math.min(x + dx, res.w - w));
        y = Math.max(0, Math.min(y + dy, res.h - h));
      } else {
        if (dragType.includes("e")) w = Math.max(20, Math.min(w + dx, res.w - x));
        if (dragType.includes("s")) h = Math.max(20, Math.min(h + dy, res.h - y));
        if (dragType.includes("w")) {
          const maxDx = startBox.w - 20;
          const clampedDx = Math.max(-startBox.x, Math.min(dx, maxDx));
          x = startBox.x + clampedDx;
          w = startBox.w - clampedDx;
        }
        if (dragType.includes("n")) {
          const maxDy = startBox.h - 20;
          const clampedDy = Math.max(-startBox.y, Math.min(dy, maxDy));
          y = startBox.y + clampedDy;
          h = startBox.h - clampedDy;
        }

        // Lock ratio if specified
        if (currentRatio !== "free") {
          const parts = currentRatio.split(":");
          const r = parseFloat(parts[0]) / parseFloat(parts[1]);
          if (dragType === "e" || dragType === "w") {
            h = Math.min(res.h - y, w / r);
          } else {
            w = Math.min(res.w - x, h * r);
          }
        }
      }

      cropBox = { x: Math.round(x), y: Math.round(y), w: Math.round(w), h: Math.round(h) };
      updateCropOverlayDOM();
    });

    window.addEventListener("mouseup", function () {
      isDragging = false;
      dragType = null;
    });
  }

  // --- Enable / Disable Crop Mode ---
  function enableCropMode() {
    isCropMode = true;
    setupCropUI();

    // UI state
    $(".tool_button").removeClass("tool_button_current");
    $("#tool_crop").addClass("tool_button_current");
    $(".context_panel").hide();
    $("#crop_panel").css("display", "flex");

    const overlay = document.getElementById("crop_overlay");
    if (overlay) overlay.style.display = "block";

    if (cropBox.w === 0 || cropBox.h === 0) {
      resetCropBoxToCanvas();
    } else {
      updateCropOverlayDOM();
    }
  }

  function disableCropMode() {
    isCropMode = false;
    $("#tool_crop").removeClass("tool_button_current");
    $("#crop_panel").hide();
    const overlay = document.getElementById("crop_overlay");
    if (overlay) overlay.style.display = "none";
  }

  // --- Apply Crop Action ---
  function applyCrop() {
    if (!isCropMode) return;
    const cropX = cropBox.x;
    const cropY = cropBox.y;
    const cropW = Math.round(cropBox.w);
    const cropH = Math.round(cropBox.h);

    if (cropW <= 0 || cropH <= 0) {
      disableCropMode();
      return;
    }

    const svgContent = document.getElementById("svgcontent");
    if (svgContent) {
      // Shift all SVG elements by (-cropX, -cropY)
      const images = svgContent.querySelectorAll("image");
      images.forEach(img => {
        const curX = parseFloat(img.getAttribute("x") || 0);
        const curY = parseFloat(img.getAttribute("y") || 0);
        img.setAttribute("x", curX - cropX);
        img.setAttribute("y", curY - cropY);
      });

      // Shift paths, rects, circles, texts, etc.
      const shapes = svgContent.querySelectorAll("path, rect, circle, ellipse, line, text, polyline, polygon, g");
      shapes.forEach(shape => {
        if (shape.id === "canvas_background" || shape.closest("#canvas_background") || shape.tagName.toLowerCase() === "image") return;
        if (shape.parentElement === svgContent) {
          const currentTransform = shape.getAttribute("transform") || "";
          shape.setAttribute("transform", `translate(${-cropX}, ${-cropY}) ${currentTransform}`);
        }
      });
    }

    // Update canvas resolution in SVG Canvas
    if (typeof svgCanvas !== "undefined" && svgCanvas.setResolution) {
      svgCanvas.setResolution(cropW, cropH);
    }
    $("#canvas_width").val(cropW);
    $("#canvas_height").val(cropH);

    if (typeof methodDraw !== "undefined" && methodDraw.updateCanvas) {
      methodDraw.updateCanvas();
    }

    disableCropMode();

    // Switch back to Select Tool
    $("#tool_select").trigger("click");
  }

  // --- Anki Bridge Integration ---
  window.ankiAddonSetImg = function (data, type) {
    setupCropUI();

    if (type === "svg") {
      methodDraw.loadFromString(data);
      // Natively activate crop tool by default on load
      setTimeout(() => {
        enableCropMode();
      }, 200);
    } else {
      const setImage = function (img_width, img_height) {
        svgCanvas.setResolution(img_width, img_height);
        $("#canvas_width").val(img_width);
        $("#canvas_height").val(img_height);

        const newImage = svgCanvas.addSvgElementFromJson({
          "element": "image",
          "attr": {
            "x": 0,
            "y": 0,
            "width": img_width,
            "height": img_height,
            "id": svgCanvas.getNextId(),
            "style": "pointer-events:inherit"
          }
        });
        svgCanvas.setHref(newImage, data);
        svgCanvas.selectOnly([newImage]);
        svgCanvas.alignSelectedElements("m", "page");
        svgCanvas.alignSelectedElements("c", "page");
        svgCanvas.clearSelection();
        methodDraw.updateCanvas();

        // Natively select and activate the Crop Tool by default on image open!
        setTimeout(() => {
          enableCropMode();
        }, 150);
      };

      const img = new Image();
      img.src = data;
      document.body.appendChild(img);
      img.onload = function () {
        const img_width = img.offsetWidth || img.naturalWidth || 600;
        const img_height = img.offsetHeight || img.naturalHeight || 400;
        setImage(img_width, img_height);
        document.body.removeChild(img);
      };
    }
  };

  window.ankiAddonSaveImg = function () {
    // If user is currently in crop mode, automatically apply crop before saving!
    if (isCropMode) {
      applyCrop();
    }

    if (typeof svgCanvas !== "undefined") {
      svgCanvas.clearSelection();
      const svg_str = svgCanvas.getSvgString();
      if (typeof pycmd === "function") {
        pycmd("svg_save:" + svg_str);
      }
    }
  };

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async function wait_until_pycmd(cb) {
    while (typeof pycmd !== "function") {
      await sleep(50);
    }
    cb();
  }

  window.addEventListener("load", function () {
    setupCropUI();
    wait_until_pycmd(function () {
      pycmd("img_src");
    });
  });
})();