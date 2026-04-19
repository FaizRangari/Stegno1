const API = "http://127.0.0.1:8765";
const state = { decodedTempPath: "", activeEditorId: "" };

const $ = (id) => document.getElementById(id);

function setProgress(value) {
  $("progressBar").style.width = `${Math.max(0, Math.min(100, value))}%`;
}

function setStatus(text, type = "") {
  const pill = $("statusPill");
  pill.textContent = text;
  pill.className = "status-pill";
  if (type) pill.classList.add(type);
}

function setSidebarCollapsed(collapsed) {
  $("appShell").classList.toggle("sidebar-collapsed", collapsed);
  $("sidebarToggle").setAttribute("aria-expanded", String(!collapsed));
  localStorage.setItem("stegotool.sidebarCollapsed", collapsed ? "1" : "0");
}

function initSidebar() {
  const saved = localStorage.getItem("stegotool.sidebarCollapsed");
  const shouldCollapse = window.innerWidth < 1000 ? true : saved === "1";
  setSidebarCollapsed(shouldCollapse);
  $("sidebarToggle").addEventListener("click", () => {
    setSidebarCollapsed(!$("appShell").classList.contains("sidebar-collapsed"));
  });
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function field(label, value) {
  return `<div class="result-row"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value || "Not available")}</strong></div>`;
}

function section(title, rows, extra = "") {
  return `<section class="result-section"><h3>${escapeHtml(title)}</h3><div class="result-list">${rows.join("")}</div>${extra}</section>`;
}

function renderNotice(text, kind = "muted") {
  return `<div class="notice ${kind}">${escapeHtml(text)}</div>`;
}

function formatBytes(bytes) {
  const size = Number(bytes || 0);
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  if (size < 1024 * 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`;
  return `${(size / 1024 / 1024 / 1024).toFixed(2)} GB`;
}

function previewMeta(info) {
  return `<div class="preview-meta"><strong>${escapeHtml(info.name)}</strong><span>${escapeHtml(formatBytes(info.size))} · ${escapeHtml(info.mime || info.extension || "file")}</span></div>`;
}

function mediaHint(info) {
  const ext = (info.extension || "").toLowerCase();
  if (info.kind === "video" && [".mkv", ".avi", ".mov"].includes(ext)) {
    return `<div class="preview-hint">This container may not preview reliably in the embedded desktop runtime.</div>`;
  }
  if (info.kind === "audio" && [".flac", ".m4a"].includes(ext)) {
    return `<div class="preview-hint">This audio format may not preview reliably in the embedded desktop runtime.</div>`;
  }
  return "";
}

function previewFallbackMarkup(info) {
  return [
    previewMeta(info),
    `<div class="preview-fallback">`,
    `<strong>Preview unavailable in embedded viewer</strong>`,
    `<p>This file may use a codec or container not supported by the desktop preview runtime.</p>`,
    `<button class="tertiary-btn open-external-btn" data-path="${escapeHtml(info.path)}">Open externally</button>`,
    `</div>`,
  ].join("");
}

function renderPreviewMarkup(info, directText = null) {
  if (!info?.exists) return `<div class="preview-empty">${escapeHtml(info?.error || "No file selected.")}</div>`;
  const meta = previewMeta(info);
  if (info.kind === "image") return `${meta}<img class="media-preview" src="${escapeHtml(info.uri)}" alt="${escapeHtml(info.name)}">`;
  if (info.kind === "audio") return `${meta}${mediaHint(info)}<audio class="media-control guarded-media" data-path="${escapeHtml(info.path)}" controls preload="metadata" src="${escapeHtml(info.uri)}"></audio>`;
  if (info.kind === "video") return `${meta}${mediaHint(info)}<video class="media-control video-control guarded-media" data-path="${escapeHtml(info.path)}" controls preload="metadata" src="${escapeHtml(info.uri)}"></video>`;
  if (info.kind === "text") return `${meta}<pre class="text-preview">${escapeHtml(directText ?? info.text ?? "")}</pre>`;
  return `${meta}<div class="preview-empty">Preview unavailable for this binary file.</div>`;
}

function armMediaPreviewGuards(container, info) {
  if (!info || !["audio", "video"].includes(info.kind)) return;
  const media = container.querySelector(".guarded-media");
  if (!media) return;
  let playable = false;
  let settled = false;
  const fail = () => {
    if (settled || playable) return;
    settled = true;
    container.innerHTML = `<div class="preview-title">${escapeHtml(container.dataset.previewTitle || "Preview")}</div>${previewFallbackMarkup(info)}`;
    bindExternalOpenButtons(container);
  };
  const ok = () => {
    playable = true;
    settled = true;
    media.classList.add("is-playable");
  };
  media.addEventListener("loadedmetadata", () => {
    if (Number.isNaN(media.duration) && media.readyState < 1) fail();
  }, { once: true });
  media.addEventListener("canplay", ok, { once: true });
  media.addEventListener("error", fail, { once: true });
  media.addEventListener("stalled", fail, { once: true });
  media.addEventListener("abort", fail, { once: true });
  setTimeout(() => {
    if (!playable && media.readyState < 3) fail();
  }, 2500);
}

async function renderFilePreview(containerId, path, title, directText = null) {
  const el = $(containerId);
  if (!path) {
    el.innerHTML = `<div class="preview-title">${escapeHtml(title)}</div><div class="preview-empty">No file selected.</div>`;
    return;
  }
  if (!window.pywebview?.api?.file_preview) {
    el.innerHTML = `<div class="preview-title">${escapeHtml(title)}</div><div class="preview-empty">Preview bridge unavailable.</div>`;
    return;
  }
  try {
    const info = await window.pywebview.api.file_preview(path);
    el.dataset.previewTitle = title;
    el.innerHTML = `<div class="preview-title">${escapeHtml(title)}</div>${renderPreviewMarkup(info, directText)}`;
    armMediaPreviewGuards(el, info);
  } catch {
    el.innerHTML = `<div class="preview-title">${escapeHtml(title)}</div><div class="preview-empty">Preview failed.</div>`;
  }
}

async function renderMiniFilePreview(containerId, path) {
  const el = $(containerId);
  if (!path) {
    el.textContent = containerId.includes("secret") ? "No secret file selected." : "No decoy file selected.";
    return;
  }
  if (!window.pywebview?.api?.file_preview) {
    el.textContent = "Preview bridge unavailable.";
    return;
  }
  try {
    const info = await window.pywebview.api.file_preview(path);
    if (!info.exists) {
      el.textContent = info.error || "File not found.";
      return;
    }
    if (info.kind === "text") {
      el.innerHTML = `<strong>${escapeHtml(info.name)}</strong><pre>${escapeHtml((info.text || "").slice(0, 360))}</pre>`;
    } else {
      el.innerHTML = `<strong>${escapeHtml(info.name)}</strong><span>${escapeHtml(formatBytes(info.size))} · ${escapeHtml(info.kind)}</span>`;
    }
  } catch {
    el.textContent = "Preview failed.";
  }
}

async function post(path, body) {
  const response = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return response.json();
}

async function checkHealthForFailureOnly() {
  try {
    const response = await fetch(`${API}/health`);
    const data = await response.json();
    if (data.status !== "ok") {
      setStatus("Backend unavailable", "danger");
    }
  } catch {
    setStatus("Backend unavailable", "danger");
  }
}

function activateView(name) {
  document.querySelectorAll(".nav-item").forEach((btn) => btn.classList.toggle("active", btn.dataset.view === name));
  document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
  $(`${name}View`).classList.add("active");
  const titles = {
    encode: ["Encode", "Build a dual-slot payload and embed it into image, audio, or video media."],
    decode: ["Decode", "Extract a primary or decoy payload with one password field."],
    tutorial: ["Tutorial", "Learn the encode and decode workflows with guided screenshots."],
    about: ["About", "A local desktop shell around the StegoTool core."],
  };
  $("pageTitle").textContent = titles[name][0];
  $("pageSubtitle").textContent = titles[name][1];
}

function setTutorialFlow(flow) {
  document.querySelectorAll(".tutorial-tab").forEach((btn) => btn.classList.toggle("active", btn.dataset.tutorialFlow === flow));
  $("encodeTutorial").classList.toggle("active", flow === "encode");
  $("decodeTutorial").classList.toggle("active", flow === "decode");
}

function dialogTypes(kind) {
  if (kind === "media") return ["Media files (*.png;*.bmp;*.wav;*.mkv;*.mov;*.mp4;*.avi)", "All files (*.*)"];
  if (kind === "secret") return ["All files (*.*)"];
  return ["All files (*.*)"];
}

async function browsePath(button) {
  const target = $(button.dataset.target);
  if (!window.pywebview?.api) {
    setStatus("File dialog unavailable", "danger");
    return;
  }
  try {
    const suggestedName = target.value || button.dataset.suggest || "";
    const path = button.dataset.dialog === "save"
      ? await window.pywebview.api.save_file(suggestedName)
      : await window.pywebview.api.open_file(dialogTypes(button.dataset.kind));
    if (path) {
      target.value = path;
      updatePreviewForTarget(target.id);
    }
  } catch {
    setStatus("File dialog failed", "danger");
  }
}

function updatePreviewForTarget(id) {
  if (id === "coverMediaPath") renderFilePreview("coverPreview", $("coverMediaPath").value.trim(), "Cover Media Preview");
  if (id === "stegoFilePath") renderFilePreview("stegoPreview", $("stegoFilePath").value.trim(), "Selected File Preview");
  if (id === "secretFilePath") renderMiniFilePreview("secretFilePreview", $("secretFilePath").value.trim());
  if (id === "decoyFilePath") renderMiniFilePreview("decoyFilePreview", $("decoyFilePath").value.trim());
  if (id === "saveDecodedPath" && $("saveDecodedPath").value.trim()) {
    setStatus("Save destination updated");
  }
}

function openEditorModal(textareaId, title) {
  state.activeEditorId = textareaId;
  $("editorModalTitle").textContent = title || "Edit text";
  $("editorModalText").value = $(textareaId).value;
  updateEditorCount();
  $("editorModal").hidden = false;
  $("editorModalText").focus();
}

function closeEditorModal(save = false) {
  if (save && state.activeEditorId) {
    $(state.activeEditorId).value = $("editorModalText").value;
  }
  $("editorModal").hidden = true;
  state.activeEditorId = "";
}

function updateEditorCount() {
  const count = $("editorModalText").value.length;
  $("editorCharCount").textContent = `${count.toLocaleString()} character${count === 1 ? "" : "s"}`;
}

function renderEncodeWorking() {
  $("encodeSummary").className = "result-card";
  $("encodeSummary").innerHTML = [
    section("Status", [
      field("Current step", "Encoding payload and saving output"),
      field("Technique", $("encodeTechnique").value),
      field("Cover media", $("coverMediaPath").value.trim()),
    ], renderNotice("Video carriers may take longer because output is written losslessly.", "warning")),
  ].join("");
}

function renderEncodeSuccess(result) {
  $("encodeSummary").className = "result-card";
  $("encodeSummary").innerHTML = [
    section("Status", [
      field("Result", "Success"),
      field("Technique", result.technique),
      field("Integrity / hint", `${result.integrity ? "on" : "off"} / ${result.hint ? "on" : "off"}`),
    ], renderNotice("Stego file saved successfully.", "success")),
    section("Payload summary", [
      field("Secret filename", result.secret_filename),
      field("Secret size", `${result.secret_size} bytes`),
      field("Decoy filename", result.decoy_filename),
      field("Decoy size", `${result.decoy_size} bytes`),
      field("Embedded envelope", `${result.embedded_bytes} bytes`),
    ]),
    section("Output", [
      field("Output path", result.output_path),
      field("Primary SHA-256", result.sha256),
    ]),
  ].join("");
}

function renderEncodeError(message) {
  $("encodeSummary").className = "result-card";
  $("encodeSummary").innerHTML = section("Status", [field("Result", "Failed")], renderNotice(message, "danger"));
}

async function runEncode() {
  setStatus("Encoding", "warning");
  setProgress(18);
  $("encodeBtn").disabled = true;
  renderEncodeWorking();
  try {
    const result = await post("/encode", {
      secret_text: $("secretText").value,
      secret_file_path: $("secretFilePath").value.trim(),
      decoy_text: $("decoyText").value,
      decoy_file_path: $("decoyFilePath").value.trim(),
      cover_media_path: $("coverMediaPath").value.trim(),
      technique: $("encodeTechnique").value,
      primary_password: $("primaryPassword").value,
      decoy_password: $("decoyPassword").value,
      use_integrity: $("useIntegrity").checked,
      use_hint: $("useHint").checked,
      output_path: $("outputPath").value.trim(),
    });
    if (!result.success) throw new Error(result.error || "Encode failed.");
    setProgress(100);
    setStatus("Encode complete", "success");
    renderEncodeSuccess(result);
  } catch (error) {
    setProgress(0);
    setStatus("Encode failed", "danger");
    renderEncodeError(error.message);
  } finally {
    $("encodeBtn").disabled = false;
  }
}

function renderDecodeWorking() {
  $("decodeResult").className = "result-card";
  $("decodeResult").innerHTML = section("Summary", [
    field("Status", "Extracting carrier envelope"),
    field("Technique", $("decodeTechnique").value),
    field("Stego file", $("stegoFilePath").value.trim()),
  ]);
}

function renderDecodeSuccess(result) {
  $("decodeResult").className = "result-card";
  const preview = result.is_text
    ? `<div class="preview">${escapeHtml(result.text_preview)}</div>`
    : `<div class="preview muted">Binary payload saved to a temporary file.</div>`;
  $("decodeResult").innerHTML = [
    section("Summary", [
      field("Status", "Success"),
      field("Payload label", result.payload_label),
      field("Filename", result.filename),
      field("Size", `${result.size} bytes`),
      field("Technique", result.technique),
      field("Integrity", result.integrity_tag_found ? (result.integrity_ok ? "verified" : "failed") : "not present"),
    ]),
    section("File info", [
      field("SHA-256", result.sha256),
      field("Temp path", result.decoded_temp_path),
    ]),
    section("Preview", [], preview),
  ].join("");
}

function renderDecodeError(message) {
  $("decodeResult").className = "result-card";
  $("decodeResult").innerHTML = section("Summary", [field("Status", "Failed")], renderNotice(message, "danger"));
}

async function runDecode() {
  setStatus("Decoding", "warning");
  setProgress(20);
  $("decodeBtn").disabled = true;
  $("saveDecodedBtn").disabled = true;
  $("openDecodedBtn").disabled = true;
  $("copyDecodedPathBtn").disabled = true;
  state.decodedTempPath = "";
  renderFilePreview("decodedOutputPreview", "", "Decoded Output Preview");
  renderDecodeWorking();
  try {
    const result = await post("/decode", {
      stego_file_path: $("stegoFilePath").value.trim(),
      password: $("decodePassword").value,
      technique: $("decodeTechnique").value,
    });
    if (!result.success) throw new Error(result.error || "Decode failed.");
    state.decodedTempPath = result.decoded_temp_path;
    setProgress(100);
    setStatus("Decode complete", "success");
    if (!$("saveDecodedPath").value.trim()) $("saveDecodedPath").value = result.filename || "decoded-output.bin";
    renderDecodeSuccess(result);
    renderFilePreview("decodedOutputPreview", result.decoded_temp_path, "Decoded Output Preview", result.is_text ? result.text_preview : null);
    $("saveDecodedBtn").disabled = false;
    $("openDecodedBtn").disabled = false;
    $("copyDecodedPathBtn").disabled = false;
  } catch (error) {
    setProgress(0);
    setStatus("Decode failed", "danger");
    renderDecodeError(error.message);
  } finally {
    $("decodeBtn").disabled = false;
  }
}

async function saveDecoded() {
  if (!state.decodedTempPath) return;
  const outputPath = $("saveDecodedPath").value.trim();
  if (!outputPath) {
    setStatus("Save path required", "warning");
    return;
  }
  const result = await post("/save-decoded", { source_path: state.decodedTempPath, output_path: outputPath });
  setStatus(result.success ? "Decoded saved" : "Save failed", result.success ? "success" : "danger");
}

async function openDecodedFolder() {
  if (!state.decodedTempPath) return;
  const result = await post("/open-folder", { path: state.decodedTempPath });
  setStatus(result.success ? "Folder opened" : "Open failed", result.success ? "success" : "danger");
}

async function openExternal(path) {
  if (!path) return;
  if (!window.pywebview?.api?.open_external) {
    setStatus("External open unavailable", "danger");
    return;
  }
  const result = await window.pywebview.api.open_external(path);
  setStatus(result.success ? "Opened externally" : "Open failed", result.success ? "success" : "danger");
}

function bindExternalOpenButtons(root = document) {
  root.querySelectorAll(".open-external-btn").forEach((btn) => {
    if (btn.dataset.bound) return;
    btn.dataset.bound = "1";
    btn.addEventListener("click", () => openExternal(btn.dataset.path));
  });
}

async function copyDecodedPath() {
  if (!state.decodedTempPath) return;
  try {
    await navigator.clipboard.writeText(state.decodedTempPath);
    setStatus("Path copied", "success");
  } catch {
    setStatus("Copy failed", "danger");
  }
}

document.querySelectorAll(".nav-item").forEach((btn) => btn.addEventListener("click", () => activateView(btn.dataset.view)));
document.querySelectorAll(".tutorial-tab").forEach((btn) => btn.addEventListener("click", () => setTutorialFlow(btn.dataset.tutorialFlow)));
document.querySelectorAll(".browse-btn").forEach((btn) => btn.addEventListener("click", () => browsePath(btn)));
document.querySelectorAll(".compact-expand").forEach((btn) => btn.addEventListener("click", () => openEditorModal(btn.dataset.editor, btn.dataset.title)));
["coverMediaPath", "stegoFilePath", "secretFilePath", "decoyFilePath", "saveDecodedPath"].forEach((id) => {
  $(id).addEventListener("change", () => updatePreviewForTarget(id));
  $(id).addEventListener("blur", () => updatePreviewForTarget(id));
});
$("editorModalText").addEventListener("input", updateEditorCount);
$("editorModalClose").addEventListener("click", () => closeEditorModal(true));
$("editorSaveBtn").addEventListener("click", () => closeEditorModal(true));
$("editorClearBtn").addEventListener("click", () => {
  $("editorModalText").value = "";
  updateEditorCount();
});
$("editorModal").addEventListener("click", (event) => {
  if (event.target.id === "editorModal") closeEditorModal(true);
});
$("encodeBtn").addEventListener("click", runEncode);
$("decodeBtn").addEventListener("click", runDecode);
$("saveDecodedBtn").addEventListener("click", saveDecoded);
$("openDecodedBtn").addEventListener("click", openDecodedFolder);
$("copyDecodedPathBtn").addEventListener("click", copyDecodedPath);
initSidebar();
checkHealthForFailureOnly();
