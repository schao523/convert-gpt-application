const token = new URLSearchParams(location.search).get("token") || "";
const state = {
  kind: "gap", offset: 0, limit: 25, total: 0, items: [], selectedIndex: -1,
  selected: null, editing: null, dirty: false, pending: false,
};

const byId = (id) => document.getElementById(id);
const statusNode = byId("app-status");
const form = byId("verse-form");
const mutationButtons = [...document.querySelectorAll("[data-mutation]")];
const ragSyncButton = byId("rag-metadata-sync");

async function api(path, options = {}) {
  const url = new URL(path, location.href);
  url.searchParams.set("token", token);
  const headers = new Headers(options.headers || {});
  headers.set("X-Review-Token", token);
  if (options.body) headers.set("Content-Type", "application/json");
  let response;
  try {
    response = await fetch(url, { ...options, headers });
  } catch (cause) {
    throw Object.assign(new Error("無法連線至本機核對服務；目前編輯內容仍保留。"), { cause });
  }
  const payload = await response.json();
  if (!response.ok) {
    throw Object.assign(new Error(payload.error?.message || "核對服務發生錯誤"), {
      status: response.status, payload,
    });
  }
  return payload;
}

function showStatus(message, isError = false) {
  statusNode.textContent = message;
  statusNode.classList.toggle("is-error", isError);
}

function setPending(pending) {
  state.pending = pending;
  mutationButtons.forEach((button) => { button.disabled = pending || !state.selected; });
  ragSyncButton.disabled = pending;
}

function queryFilters() {
  const values = new FormData(byId("filters"));
  const query = new URLSearchParams({ kind: state.kind, offset: state.offset, limit: state.limit });
  for (const [name, value] of values) if (String(value).trim()) query.set(name, value);
  return query;
}

async function loadSummary() {
  const payload = await api("/api/summary");
  byId("verse-count").textContent = payload.summary.verse_count.toLocaleString();
  byId("gap-count").textContent = payload.summary.gap_count.toLocaleString();
  byId("unverified-count").textContent = payload.summary.unverified_count.toLocaleString();
  byId("backup-state").textContent = payload.review.backup_created ? "已建立" : "首次寫入前建立";
  const stale = payload.review.rag_index_state === "stale";
  const sync = payload.review.rag_metadata_sync || { available: false };
  ragSyncButton.hidden = !stale || !sync.available;
  ragSyncButton.disabled = state.pending;
  byId("rag-state").textContent = stale
    ? sync.available ? "STALE · 可同步" : "STALE · 需重建"
    : "CURRENT";
  byId("rag-state").title = stale
    ? sync.available
      ? "若經文與來源未變，可重用現有嵌入，只同步核實資料。"
      : "目前設定不支援只同步核實資料；請執行完整 RAG ingestion。"
    : "RAG discovery 與目前語料一致。";
}

function queueLabel(item) {
  if (state.kind === "gap") {
    return `${item.missing_references.join("、")}<small>${item.previous.reference} → ${item.next.reference}</small>`;
  }
  return `${escapeHtml(item.source_file)} · 第 ${item.source_page} 頁<small>${item.row_count} 節待核實；${item.low_confidence_count} 節低信心</small>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[character]);
}

function renderQueue() {
  const list = byId("queue-list");
  list.replaceChildren();
  state.items.forEach((item, index) => {
    const entry = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.innerHTML = queueLabel(item);
    button.classList.toggle("is-selected", index === state.selectedIndex);
    button.addEventListener("click", () => selectIssue(index));
    entry.append(button);
    list.append(entry);
  });
  const start = state.total ? state.offset + 1 : 0;
  const end = Math.min(state.offset + state.items.length, state.total);
  byId("queue-position").textContent = `${start}–${end} / ${state.total}`;
  byId("previous-page").disabled = state.offset === 0;
  byId("next-page").disabled = state.offset + state.limit >= state.total;
}

async function loadQueue(selectFirst = true) {
  showStatus("正在載入核對佇列……");
  const payload = await api(`/api/issues?${queryFilters()}`);
  state.items = payload.result.items;
  state.total = payload.result.total;
  state.selectedIndex = -1;
  state.selected = null;
  state.editing = null;
  renderQueue();
  if (selectFirst && state.items.length) await selectIssue(0);
  else if (!state.items.length) {
    clearEditor();
    showStatus("目前篩選條件下沒有待處理項目。")
  }
}

async function selectIssue(index) {
  if (state.dirty && !confirm("尚有未儲存的輸入。確定切換項目？")) return;
  state.selectedIndex = index;
  renderQueue();
  const issue = state.items[index];
  const payload = await api(`/api/review-item?kind=${state.kind}&id=${encodeURIComponent(issue.id)}`);
  state.selected = payload.item;
  state.dirty = false;
  byId("conflict-panel").hidden = true;
  renderReviewItem();
  await loadHistory();
  setPending(false);
}

function sourceUrl(source, page) {
  const url = new URL(`/source/${source.id}.pdf`, location.href);
  url.searchParams.set("token", token);
  url.hash = `page=${page}`;
  return url.href;
}

function showPdf(source, page) {
  const url = sourceUrl(source, page);
  byId("pdf-viewer").src = url;
  byId("pdf-direct-link").href = url;
  byId("pdf-placeholder").hidden = true;
}

function contextCard(snapshot, title) {
  return `<article class="context-card"><strong>${escapeHtml(title)} · ${escapeHtml(snapshot.reference)}</strong>${escapeHtml(snapshot.text)}</article>`;
}

function renderReviewItem() {
  const item = state.selected;
  if (state.kind === "unverified") {
    showPdf(item.source, item.source_page);
    const target = item.verses.find((verse) => !verse.verified) || item.verses[0];
    state.editing = target;
    fillForm(target);
    byId("context-verses").innerHTML = item.verses.map((verse) => contextCard(
      verse, verse === target ? "目前編輯" : "同頁經文"
    )).join("");
    byId("selection-kind").textContent = `第 ${item.source_page} 頁 · ${item.verses.length} 節`;
    byId("insert-verse").hidden = true;
    byId("verify-page").hidden = false;
  } else {
    const source = item.sources.find((entry) => entry.filename === item.next.source_file) || item.sources[0];
    showPdf(source, item.next.source_page);
    const replacement = {
      book_id: item.previous.book_id, chapter: item.previous.chapter,
      verse: item.previous.verse + 1, text: "", source_file: item.next.source_file,
      source_page: item.next.source_page, ocr_confidence: 100, verified: true,
    };
    state.editing = null;
    fillForm(replacement);
    byId("context-verses").innerHTML = contextCard(item.previous, "前一節") + contextCard(item.next, "後一節");
    byId("selection-kind").textContent = `缺少 ${item.missing_references.length} 節`;
    byId("insert-verse").hidden = false;
    byId("verify-page").hidden = true;
  }
  byId("save-verse").hidden = !state.editing;
  byId("verify-verse").hidden = !state.editing;
  byId("unverify-verse").hidden = !state.editing;
  showStatus("請對照左側 PDF；系統不會自動核實任何經文。")
}

function fillForm(verse) {
  byId("book-id").value = verse.book_id;
  byId("chapter").value = verse.chapter;
  byId("verse").value = verse.verse;
  byId("verse-text").value = verse.text;
  byId("source-file").value = verse.source_file;
  byId("source-page").value = verse.source_page;
  byId("confidence").value = verse.ocr_confidence;
  byId("verified").checked = Boolean(verse.verified);
  byId("review-note").value = "";
  state.dirty = false;
}

function formVerse() {
  return {
    book_id: Number(byId("book-id").value), chapter: Number(byId("chapter").value),
    verse: Number(byId("verse").value), text: byId("verse-text").value,
    source_file: byId("source-file").value, source_page: Number(byId("source-page").value),
    ocr_confidence: Number(byId("confidence").value), verified: byId("verified").checked,
  };
}

async function mutate(path, payload, successMessage) {
  setPending(true);
  try {
    await api(path, { method: "POST", body: JSON.stringify(payload) });
    state.dirty = false;
    showStatus(successMessage);
    await Promise.all([loadSummary(), loadHistory()]);
    await loadQueue(true);
  } catch (error) {
    if (error.status === 409) await showConflict(error.message);
    else showStatus(error.message, true);
  } finally {
    setPending(false);
  }
}

async function showConflict(message) {
  byId("conflict-panel").hidden = false;
  let current = { message };
  try {
    const issue = state.items[state.selectedIndex];
    current = (await api(`/api/review-item?kind=${state.kind}&id=${encodeURIComponent(issue.id)}`)).item;
  } catch (_) { /* Keep the original conflict message. */ }
  byId("server-values").textContent = JSON.stringify(current, null, 2);
  showStatus("偵測到同步衝突；你的表單內容尚未被覆蓋。", true);
}

function confirmExact(message, phrase) {
  const dialog = byId("confirm-dialog");
  byId("confirm-message").textContent = `${message} 請輸入「${phrase}」。`;
  byId("confirm-input").value = "";
  dialog.showModal();
  return new Promise((resolve) => {
    dialog.addEventListener("close", () => {
      resolve(dialog.returnValue === "confirm" && byId("confirm-input").value === phrase);
    }, { once: true });
  });
}

async function loadHistory() {
  const payload = await api("/api/history");
  const list = byId("history-list");
  list.replaceChildren();
  if (!payload.history.length) {
    const item = document.createElement("li"); item.textContent = "本工作階段尚無變更。"; list.append(item); return;
  }
  payload.history.slice().reverse().slice(0, 20).forEach((event) => {
    const item = document.createElement("li");
    item.textContent = `${event.timestamp_utc} · ${event.action} · ${event.status}${event.note ? ` · ${event.note}` : ""}`;
    list.append(item);
  });
}

function clearEditor() {
  form.reset();
  byId("context-verses").replaceChildren();
  byId("pdf-viewer").removeAttribute("src");
  byId("pdf-placeholder").hidden = false;
  setPending(false);
}

form.addEventListener("input", () => { state.dirty = true; });
form.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!state.editing) return;
  mutate("/api/verses/update", {
    expected: state.editing, replacement: formVerse(), note: byId("review-note").value,
  }, "經文修改已儲存，RAG 索引已標記為 stale。")
});

byId("verify-verse").addEventListener("click", () => mutate("/api/verses/verification", {
  expected: [state.editing], verified: true, note: byId("review-note").value,
}, "此節已標記為人工核實。"));
byId("unverify-verse").addEventListener("click", () => mutate("/api/verses/verification", {
  expected: [state.editing], verified: false, note: byId("review-note").value,
}, "此節已取消核實。"));
byId("insert-verse").addEventListener("click", async () => {
  const verse = formVerse();
  const phrase = `補入 ${verse.book_id} ${verse.chapter}:${verse.verse}`;
  if (await confirmExact("這會新增一節經文，且必須是你已在 PDF 中親自確認的文字。", phrase)) {
    await mutate("/api/verses/insert", { replacement: verse, note: byId("review-note").value }, "缺少的經節已補入。")
  }
});
byId("verify-page").addEventListener("click", async () => {
  const item = state.selected;
  const phrase = `核實 ${item.source_file} 第${item.source_page}頁`;
  if (await confirmExact(`這會核實畫面載入的 ${item.verses.length} 節；低信心列仍需逐一目視。`, phrase)) {
    await mutate("/api/pages/verify", {
      expected: item.verses, note: byId("review-note").value,
    }, "本頁載入的全部經文已核實。")
  }
});

ragSyncButton.addEventListener("click", async () => {
  const phrase = "同步 RAG 核實資料";
  const confirmed = await confirmExact(
    "服務會先確認經文與來源未變，備份 JSON 向量檔，再只更新核實資料。",
    phrase,
  );
  if (!confirmed) return;
  setPending(true);
  showStatus("正在檢查並同步 RAG 核實資料……");
  try {
    const payload = await api("/api/rag/metadata-sync", {
      method: "POST", body: JSON.stringify({ confirmation: phrase }),
    });
    const result = payload.result;
    showStatus(
      `RAG 核實資料已同步 ${result.targeted_items.toLocaleString()} 個區塊；`
      + `嵌入與經文未變。備份：${result.backup_name}`,
    );
    await loadSummary();
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    setPending(false);
  }
});

document.querySelectorAll("[data-kind]").forEach((button) => button.addEventListener("click", async () => {
  state.kind = button.dataset.kind;
  state.offset = 0;
  document.querySelectorAll("[data-kind]").forEach((tab) => {
    const active = tab === button;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", String(active));
  });
  await loadQueue();
}));
byId("filters").addEventListener("submit", async (event) => { event.preventDefault(); state.offset = 0; await loadQueue(); });
byId("previous-page").addEventListener("click", async () => { state.offset = Math.max(0, state.offset - state.limit); await loadQueue(); });
byId("next-page").addEventListener("click", async () => { state.offset += state.limit; await loadQueue(); });

document.addEventListener("keydown", async (event) => {
  if (event.altKey && event.key === "ArrowLeft" && state.selectedIndex > 0) {
    event.preventDefault(); await selectIssue(state.selectedIndex - 1);
  }
  if (event.altKey && event.key === "ArrowRight" && state.selectedIndex + 1 < state.items.length) {
    event.preventDefault(); await selectIssue(state.selectedIndex + 1);
  }
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s" && state.editing) {
    event.preventDefault(); form.requestSubmit();
  }
});

setPending(true);
Promise.all([loadSummary(), loadQueue(), loadHistory()]).catch((error) => showStatus(error.message, true));
