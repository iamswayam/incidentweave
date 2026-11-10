(() => {
  "use strict";
  const SETTINGS_KEY = "iw.settings";
  const ACTIVE_REPO_KEY = "iw.activeRepository";
  const HISTORY_KEY = "iw.history";
  const MAX_QUERY_CHARS = 2000;
  const MAX_LIMIT = 20;
  const HISTORY_CAP = 200;
  const BATCH_GAP_MS = 6500;
  const BATCH_START_MARGIN_MS = 250;
  const $ = (selector) => document.querySelector(selector);
  const e = {
    repoList: $("#repository-list"), repoEmpty: $("#repository-empty"), activeTitle: $("#active-repository-title"),
    historyList: $("#history-list"), historyEmpty: $("#history-empty"), historyCount: $("#history-count"), loadMore: $("#load-more"),
    question: $("#question-input"), charCount: $("#character-count"), askForm: $("#ask-form"), askButton: $("#ask-button"),
    askReason: $("#ask-reason"), answerLimit: $("#answer-limit"), answerRegion: $("#answer-region"), loading: $("#loading-indicator"),
    elapsed: $("#elapsed-time"), message: $("#global-message"), settingsDialog: $("#settings-dialog"), settingsForm: $("#settings-form"),
    apiBase: $("#api-base"), apiSecret: $("#api-secret"), batchInput: $("#batch-input"), batchQuestionCount: $("#batch-question-count"),
    runBatch: $("#run-batch"), cancelBatch: $("#cancel-batch"), batchStatus: $("#batch-status"), batchTable: $("#batch-table"),
    batchResults: $("#batch-results"), batchEmpty: $("#batch-empty"), exportCsv: $("#export-csv"), themeLabel: $("#theme-label"),
  };
  function readStored(key, fallback) {
    try { const value = localStorage.getItem(key); return value === null ? fallback : JSON.parse(value); }
    catch { return fallback; }
  }
  const storedSettings = readStored(SETTINGS_KEY, {});
  const settings = storedSettings && typeof storedSettings === "object" ? storedSettings : {};
  const savedRepository = readStored(ACTIVE_REPO_KEY, "");
  let activeRepository = typeof savedRepository === "string" ? savedRepository : "";
  let localHistory = readStored(HISTORY_KEY, []);
  if (!Array.isArray(localHistory)) localHistory = [];
  let serverHistory = [];
  let serverCursor = null;
  let serverHasMore = true;
  let batchResults = [];
  let batchRunning = false;
  let batchCancelRequested = false;
  let busy = false;
  let messageTimer = null;
  e.apiBase.value = typeof settings.apiBase === "string" ? settings.apiBase : "";
  e.apiSecret.value = typeof settings.apiSecret === "string" ? settings.apiSecret : "";

  class ApiError extends Error {
    constructor(status, message, retryAfter = null) { super(message); this.status = status; this.retryAfter = retryAfter; }
  }
  function currentApiBase() { return String(e.apiBase.value || "").trim().replace(/\/+$/, ""); }
  function apiUrl(path) {
    const base = currentApiBase();
    let url;
    try { url = new URL(`${base}${path}`, window.location.origin); }
    catch { throw new ApiError(0, "Could not reach the API at the configured base URL. Is the app running?"); }
    if (url.origin !== window.location.origin) throw new ApiError(0, "The API base URL must use this page's origin. The secret was not sent.");
    return url;
  }
  function errorMessage(status, payload) {
    const code = payload && payload.error && payload.error.code;
    const message = payload && payload.error && payload.error.message;
    if (status === 401) return "Check your API secret in Settings.";
    if (status === 404 && code === "repository_not_found") return "That repository has not been ingested yet.";
    if (status === 404) return typeof message === "string" ? message : "The requested record was not found.";
    if (status === 422) return typeof message === "string" ? message : "The request could not be validated.";
    if (status === 429) return typeof message === "string" ? message : "Request limit exceeded. Try again later.";
    if (status === 500 || status === 502) return "The service had a problem; see its logs.";
    return typeof message === "string" ? message : "The request could not be completed.";
  }
  async function apiFetch(path, options = {}) {
    const url = apiUrl(path);
    const secret = e.apiSecret.value;
    if (!secret) throw new ApiError(401, "Check your API secret in Settings.");
    const headers = new Headers(options.headers || {});
    headers.set("X-API-Secret", secret);
    if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    let response;
    try { response = await fetch(url, { ...options, headers }); }
    catch {
      const base = currentApiBase() || window.location.origin;
      throw new ApiError(0, `Could not reach the API at ${base}. Is the app running?`);
    }
    let payload = null;
    if (response.status !== 204) { try { payload = await response.json(); } catch { payload = null; } }
    if (!response.ok) throw new ApiError(response.status, errorMessage(response.status, payload), response.headers.get("Retry-After"));
    return payload;
  }
  function retrySeconds(value) {
    const seconds = Number.parseInt(value || "", 10);
    if (Number.isFinite(seconds)) return Math.max(0, seconds);
    const timestamp = Date.parse(value || "");
    return Number.isFinite(timestamp) ? Math.max(0, Math.ceil((timestamp - Date.now()) / 1000)) : null;
  }
  function showMessage(message, kind = "error", retryAfter = null) {
    window.clearInterval(messageTimer);
    e.message.hidden = false;
    e.message.className = `message-banner ${kind === "error" ? "is-error" : kind === "success" ? "is-success" : ""}`;
    let remaining = retrySeconds(retryAfter);
    const paint = () => {
      e.message.textContent = remaining !== null && remaining > 0 ? `${message} Retry in ${remaining}s.` : message;
      if (remaining !== null && remaining > 0) remaining -= 1;
      else window.clearInterval(messageTimer);
    };
    paint();
    if (remaining !== null && remaining > 0) messageTimer = window.setInterval(paint, 1000);
  }
  function clearMessage() { window.clearInterval(messageTimer); e.message.hidden = true; e.message.textContent = ""; }
  function showApiError(error) { showMessage(error instanceof ApiError ? error.message : "The request could not be completed.", "error", error instanceof ApiError ? error.retryAfter : null); }
  function node(tag, className = "", text = undefined) {
    const item = document.createElement(tag);
    if (className) item.className = className;
    if (text !== undefined) item.textContent = text;
    return item;
  }
  function outcomePresentation(outcome, degraded) {
    const values = {
      answered: ["Answered", "success"], refused_guard: ["Insufficient evidence", "warning"],
      embedding_unavailable: ["Embedding unavailable", "warning"], generation_unavailable: ["Generation unavailable", "danger"],
      degraded: ["Degraded response", "warning"],
    };
    if (degraded && outcome === "answered") return ["Degraded response", "warning"];
    return values[outcome] || ["Other outcome", "neutral"];
  }
  function confidencePresentation(rating) {
    const values = { high: ["High confidence", "success"], medium: ["Medium confidence", "warning"], low: ["Low confidence", "danger"], not_applicable: ["Not applicable", "neutral"] };
    return values[String(rating || "not_applicable").toLowerCase()] || ["Unrated", "neutral"];
  }
  function formatLatency(value) { return value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value)) ? `${(Number(value) / 1000).toFixed(2)}s` : "Not available"; }
  function formatTime(value) {
    if (!value) return "Time unavailable";
    const time = new Date(value).getTime();
    if (!Number.isFinite(time)) return "Time unavailable";
    const seconds = Math.round((time - Date.now()) / 1000);
    const units = [[31536000, "year"], [2592000, "month"], [86400, "day"], [3600, "hour"], [60, "minute"], [1, "second"]];
    const formatter = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });
    for (const [size, name] of units) if (Math.abs(seconds) >= size || size === 1) return formatter.format(Math.round(seconds / size), name);
    return "Just now";
  }
  function persistHistory() {
    localHistory = localHistory.slice(0, HISTORY_CAP);
    try { localStorage.setItem(HISTORY_KEY, JSON.stringify(localHistory)); }
    catch { showMessage("Could not save investigation history in this browser."); }
    renderHistory();
  }
  function addToHistory(response) {
    const id = response.investigation_id;
    if (id !== null && id !== undefined) localHistory = localHistory.filter((item) => item.investigation_id !== id);
    localHistory.unshift(response);
    persistHistory();
  }
  function saveActiveRepository() {
    try { localStorage.setItem(ACTIVE_REPO_KEY, JSON.stringify(activeRepository)); }
    catch { showMessage("Could not save the selected repository in this browser."); }
  }
  function renderRepositories(repositories) {
    e.repoList.replaceChildren();
    e.repoEmpty.hidden = repositories.length > 0;
    if (!repositories.length) {
      e.repoEmpty.textContent = "No repositories ingested yet. Run scripts/ingest_repo.py locally, then refresh.";
      return;
    }
    if (!repositories.some((repo) => repo.name === activeRepository)) { activeRepository = ""; saveActiveRepository(); }
    repositories.forEach((repo) => {
      const button = node("button", `repo-chip${repo.name === activeRepository ? " is-active" : ""}`);
      button.type = "button";
      button.setAttribute("aria-pressed", String(repo.name === activeRepository));
      const status = repo.chunk_count === 0 ? "is-empty" : repo.embedded_chunk_count === repo.chunk_count ? "is-success" : "is-warning";
      button.append(node("span", `status-dot ${status}`));
      const content = node("span", "repo-chip-content");
      const title = node("span", "repo-name-row");
      title.append(node("span", "repo-name", repo.name));
      if (repo.name === activeRepository) title.append(node("span", "active-label", "ACTIVE"));
      content.append(title, node("span", "repo-count", `${repo.embedded_chunk_count}/${repo.chunk_count} chunks`));
      button.append(content);
      button.addEventListener("click", () => {
        activeRepository = repo.name;
        saveActiveRepository();
        renderRepositories(repositories);
        e.activeTitle.textContent = activeRepository;
        updateAskState();
        updateBatchState();
      });
      e.repoList.append(button);
    });
    e.activeTitle.textContent = activeRepository || "Choose a repository";
    updateAskState();
    updateBatchState();
  }
  async function refreshRepositories() {
    clearMessage();
    try {
      const repositories = await apiFetch("/repositories");
      renderRepositories(Array.isArray(repositories) ? repositories : []);
      if (repositories.length === 0) showMessage("No repositories ingested yet. Run scripts/ingest_repo.py locally, then refresh.", "info");
    } catch (error) { showApiError(error); }
  }
  function renderHistory() {
    const merged = new Map();
    localHistory.forEach((item, index) => {
      if (!item || typeof item !== "object") return;
      const key = item.investigation_id === undefined || item.investigation_id === null ? `local-${index}` : String(item.investigation_id);
      merged.set(key, { kind: "local", item });
    });
    serverHistory.forEach((item) => { if (!merged.has(String(item.id))) merged.set(String(item.id), { kind: "server", item }); });
    const sortKey = (entry) => {
      const id = Number(entry.kind === "local" ? entry.item.investigation_id : entry.item.id);
      return Number.isFinite(id) ? id : Date.parse(entry.item.created_at || "") || 0;
    };
    const entries = Array.from(merged.values()).sort((a, b) => sortKey(b) - sortKey(a));
    e.historyList.replaceChildren();
    e.historyCount.textContent = String(entries.length);
    e.historyEmpty.hidden = entries.length > 0;
    entries.slice(0, HISTORY_CAP).forEach(({ kind, item }) => {
      const [label, tone] = outcomePresentation(item.outcome, item.degraded);
      const dotTone = tone === "success" ? "is-success" : tone === "warning" ? "is-warning" : tone === "danger" ? "is-danger" : "is-empty";
      const button = node("button", "history-entry");
      button.type = "button";
      button.append(node("span", `status-dot ${dotTone}`), node("span", "history-query", item.query || "Investigation"), node("span", "history-time", formatTime(item.created_at)));
      button.title = `${label} - ${item.repository_name || ""}`;
      button.addEventListener("click", () => openHistoryEntry(kind, item));
      e.historyList.append(button);
    });
    e.loadMore.disabled = !serverHasMore;
    if (!serverHasMore && serverHistory.length) e.loadMore.textContent = "No more server history";
  }
  async function loadMoreHistory() {
    clearMessage();
    e.loadMore.disabled = true;
    const params = new URLSearchParams({ limit: "20" });
    if (serverCursor !== null) params.set("before_id", String(serverCursor));
    try {
      const results = await apiFetch(`/investigations?${params.toString()}`);
      const page = Array.isArray(results) ? results : [];
      const known = new Set(serverHistory.map((item) => String(item.id)));
      page.forEach((item) => { if (!known.has(String(item.id))) serverHistory.push(item); });
      if (page.length) serverCursor = Math.min(...page.map((item) => Number(item.id)));
      serverHasMore = page.length === 20;
      renderHistory();
    } catch (error) { e.loadMore.disabled = false; showApiError(error); }
  }
  async function openHistoryEntry(kind, item) {
    clearMessage();
    if (kind === "local") {
      renderAnswer(item);
      e.activeTitle.textContent = item.repository_name || activeRepository || "Investigation history";
      activateTab("chat");
      return;
    }
    try {
      const payload = await apiFetch(`/investigations/${encodeURIComponent(item.id)}`);
      const full = { ...payload, created_at: item.created_at };
      addToHistory(full);
      renderAnswer(full);
      e.activeTitle.textContent = full.repository_name || item.repository_name;
      activateTab("chat");
    } catch (error) { showApiError(error); }
  }
  function appendClaim(parent, claim) {
    const item = node("article", "claim-item");
    item.append(node("p", "", claim && typeof claim.text === "string" ? claim.text : "Claim text unavailable."));
    const references = Array.isArray(claim && claim.evidence) ? claim.evidence : [];
    if (references.length) {
      const list = node("ul");
      references.forEach((reference) => {
        const line = node("li");
        line.append(node("span", "chunk-id", reference.chunk_id || "unknown chunk"));
        if (reference.quote) line.append(node("blockquote", "", reference.quote));
        list.append(line);
      });
      item.append(list);
    }
    parent.append(item);
  }
  function renderAnswer(response) {
    e.answerRegion.replaceChildren();
    const card = node("article", "answer-card");
    const top = node("div", "answer-topline");
    const badges = node("div", "badge-stack");
    const [outcomeLabel, outcomeTone] = outcomePresentation(response.outcome, response.degraded);
    const [ratingLabel, ratingTone] = confidencePresentation(response.model_self_rating);
    badges.append(node("span", `badge badge-${outcomeTone}`, outcomeLabel));
    badges.append(node("span", "raw-outcome", response.outcome || "unknown"));
    badges.append(node("span", `badge badge-${ratingTone}`, ratingLabel));
    const ratingInfo = node("details", "confidence-info");
    const infoSummary = node("summary", "", "i");
    infoSummary.setAttribute("aria-label", "About model self-rating");
    ratingInfo.append(infoSummary, node("span", "confidence-popover", response.rating_note || "No rating note was provided."));
    badges.append(ratingInfo);
    const actions = node("div", "answer-actions");
    const copy = node("button", "secondary-button", "Copy as Markdown");
    copy.type = "button";
    copy.addEventListener("click", () => copyMarkdown(response));
    actions.append(copy);
    top.append(badges, actions);
    card.append(top);
    if (response.query) card.append(node("p", "answer-query", response.query));
    card.append(node("h2", "", response.unavailable_answer ? "No answer: insufficient evidence" : response.diagnosis || "No diagnosis returned."));
    const claims = Array.isArray(response.claims) ? response.claims : [];
    if (claims.length) {
      const section = node("section", "answer-section");
      section.append(node("h3", "", "Claims and citations"));
      const list = node("div", "claim-list");
      claims.forEach((claim) => appendClaim(list, claim));
      section.append(list);
      card.append(section);
    }
    const evidence = Array.isArray(response.evidence) ? response.evidence : [];
    const evidenceSection = node("section", "answer-section");
    evidenceSection.append(node("h3", "", "Evidence locations"));
    const evidenceList = node("div", "evidence-list");
    evidence.forEach((entry) => {
      const row = node("div", "evidence-row");
      const start = entry.start_line === null || entry.start_line === undefined ? "?" : entry.start_line;
      const end = entry.end_line === null || entry.end_line === undefined ? "?" : entry.end_line;
      row.append(node("span", "evidence-location", `${entry.file_path || "unknown path"}:${start}-${end}`));
      const rrf = entry.rrf_score === null || entry.rrf_score === undefined ? "n/a" : entry.rrf_score;
      const vector = entry.vector_score === null || entry.vector_score === undefined ? "n/a" : entry.vector_score;
      row.append(node("span", "evidence-meta", `Rank ${entry.rank ?? "n/a"} | RRF ${rrf} | Vector ${vector}`));
      evidenceList.append(row);
    });
    if (!evidence.length) evidenceList.append(node("p", "empty-state", "No evidence locations were returned."));
    evidenceSection.append(evidenceList, node("p", "evidence-note", "Retrieved chunk content is not shown; the API exposes only cited quotes and evidence locations by design."));
    card.append(evidenceSection);
    if (response.uncertainty_note) card.append(node("p", "callout", response.uncertainty_note));
    if (response.degraded_reason) card.append(node("p", "callout warning", response.degraded_reason));
    const footer = node("footer", "answer-footer");
    footer.append(node("span", "", `Model: ${response.model || "Not available"}`));
    footer.append(node("span", "", `Latency: ${formatLatency(response.latency_ms)}`));
    if (response.retry_used) footer.append(node("span", "retry-tag", "retried"));
    footer.append(node("span", "", `Investigation: ${response.investigation_id ?? "Not persisted"}`));
    footer.append(node("span", "", `Created: ${response.created_at || "Time unavailable"}`));
    card.append(footer);
    e.answerRegion.append(card);
  }
  function markdownFor(response) {
    const outcome = outcomePresentation(response.outcome, response.degraded)[0];
    const confidence = confidencePresentation(response.model_self_rating)[0];
    const diagnosis = response.unavailable_answer ? "No answer: insufficient evidence" : response.diagnosis || "No diagnosis returned.";
    const lines = [`# ${diagnosis}`, ...(response.query ? ["", `**Question:**`, `> ${response.query.split("\n").join("\n> ")}`] : []), `**Outcome:** ${outcome} (${response.outcome || "unknown"})`, `**Confidence:** ${confidence}`];
    if (response.rating_note) lines.push(`> ${response.rating_note}`);
    if (response.claims && response.claims.length) {
      lines.push("", "## Claims and citations");
      response.claims.forEach((claim) => {
        lines.push(`- ${claim.text || "Claim text unavailable."}`);
        (claim.evidence || []).forEach((reference) => lines.push(`  - \`${reference.chunk_id || "unknown chunk"}\`: > ${reference.quote || ""}`));
      });
    }
    lines.push("", "## Evidence locations");
    (response.evidence || []).forEach((entry) => lines.push(`- \`${entry.file_path || "unknown path"}:${entry.start_line ?? "?"}-${entry.end_line ?? "?"}\` (rank ${entry.rank ?? "n/a"}; RRF ${entry.rrf_score ?? "n/a"}; vector ${entry.vector_score ?? "n/a"})`));
    lines.push("", "Retrieved chunk content is not shown; the API exposes only cited quotes and evidence locations by design.");
    if (response.uncertainty_note) lines.push("", `**Uncertainty:** ${response.uncertainty_note}`);
    if (response.degraded_reason) lines.push("", `**Degraded:** ${response.degraded_reason}`);
    lines.push("", `**Model:** ${response.model || "Not available"}`, `**Latency:** ${formatLatency(response.latency_ms)}`, `**Investigation:** ${response.investigation_id ?? "Not persisted"}`, `**Created:** ${response.created_at || "Time unavailable"}`);
    if (response.retry_used) lines.push("**Retry:** retried");
    return lines.join("\n");
  }
  async function copyMarkdown(response) {
    try { await navigator.clipboard.writeText(markdownFor(response)); showMessage("Investigation copied as Markdown.", "success"); }
    catch { showMessage("Could not copy to the clipboard. Check browser clipboard permissions."); }
  }
  function validLimit() {
    const limit = Number(e.answerLimit.value);
    return Number.isInteger(limit) && limit >= 1 && limit <= MAX_LIMIT;
  }
  function updateAskState() {
    const length = e.question.value.length;
    let reason = "";
    if (!activeRepository) reason = "Choose an active repository.";
    else if (!e.apiSecret.value) reason = "Set an API secret in Settings.";
    else if (length === 0 || !e.question.value.trim()) reason = "Enter a question.";
    else if (length > MAX_QUERY_CHARS) reason = "Question exceeds 2,000 characters.";
    else if (!validLimit()) reason = "Evidence limit must be from 1 to 20.";
    e.askReason.textContent = reason;
    e.askButton.disabled = busy || Boolean(reason);
    e.askButton.title = reason || "Ask this question";
    e.charCount.textContent = `${length.toLocaleString()} / 2,000`;
    e.charCount.classList.toggle("is-near-limit", length >= 1800 && length <= MAX_QUERY_CHARS);
    e.charCount.classList.toggle("is-over-limit", length > MAX_QUERY_CHARS);
  }
  function updateBatchState() {
    const count = e.batchInput.value.split(/\r?\n/).map((question) => question.trim()).filter(Boolean).length;
    e.batchQuestionCount.textContent = `${count} question${count === 1 ? "" : "s"}`;
    e.runBatch.disabled = batchRunning || count === 0 || !activeRepository || !e.apiSecret.value || !validLimit();
  }
  function showLoading(show) {
    e.loading.hidden = !show;
    if (!show) return null;
    const started = Date.now();
    const timer = window.setInterval(() => { e.elapsed.textContent = `${Math.floor((Date.now() - started) / 1000)}s elapsed`; }, 1000);
    e.elapsed.textContent = "0s elapsed";
    return () => window.clearInterval(timer);
  }
  async function submitQuestion(question, repositoryName = activeRepository, limit = Number(e.answerLimit.value)) {
    const result = await apiFetch("/investigations", {
      method: "POST",
      body: JSON.stringify({ repository_name: repositoryName, query: question, limit }),
    });
    const response = { ...result, created_at: result.created_at || new Date().toISOString() };
    addToHistory(response);
    return response;
  }
  async function askQuestion(event) {
    event.preventDefault();
    updateAskState();
    if (e.askButton.disabled) return;
    clearMessage();
    busy = true;
    updateAskState();
    const stopLoading = showLoading(true);
    try {
      const response = await submitQuestion(e.question.value.trim());
      renderAnswer(response);
      showMessage("Investigation complete.", "success");
    } catch (error) { showApiError(error); }
    finally {
      if (stopLoading) stopLoading();
      showLoading(false);
      busy = false;
      updateAskState();
    }
  }
  function activateTab(tab) {
    const chat = tab === "chat";
    $("#tab-chat").classList.toggle("is-active", chat);
    $("#tab-batch").classList.toggle("is-active", !chat);
    $("#tab-chat").setAttribute("aria-selected", String(chat));
    $("#tab-batch").setAttribute("aria-selected", String(!chat));
    $("#panel-chat").hidden = !chat;
    $("#panel-batch").hidden = chat;
  }
  function appendBatchRow(question, response) {
    const [outcome] = outcomePresentation(response.outcome, response.degraded);
    const [confidence] = confidencePresentation(response.model_self_rating);
    batchResults.push({ question, outcome: response.outcome || "unknown", confidence: response.model_self_rating || "not_applicable", latency_ms: response.latency_ms ?? "", investigation_id: response.investigation_id ?? "" });
    const row = document.createElement("tr");
    [["Question", question], ["Outcome", outcome], ["Confidence", confidence], ["Latency", formatLatency(response.latency_ms)]].forEach(([label, value]) => {
      const cell = node("td", "", value);
      cell.dataset.label = label;
      row.append(cell);
    });
    const action = node("td");
    action.dataset.label = "View";
    const view = node("button", "view-result", "View");
    view.type = "button";
    view.addEventListener("click", () => {
      renderAnswer(response);
      e.activeTitle.textContent = response.repository_name || activeRepository;
      activateTab("chat");
    });
    action.append(view);
    row.append(action);
    e.batchResults.append(row);
    e.batchEmpty.hidden = true;
    e.batchTable.hidden = false;
    e.exportCsv.disabled = false;
  }
  function wait(milliseconds) { return new Promise((resolve) => window.setTimeout(resolve, milliseconds)); }
  async function waitForBatchGap(milliseconds) {
    const deadline = Date.now() + milliseconds;
    while (!batchCancelRequested && Date.now() < deadline) await wait(Math.min(100, deadline - Date.now()));
  }
  async function runBatch() {
    if (batchRunning) return;
    const questions = e.batchInput.value.split(/\r?\n/).map((question) => question.trim()).filter(Boolean);
    const repositoryForBatch = activeRepository;
    const limitForBatch = Number(e.answerLimit.value);
    if (!questions.length || !activeRepository || !e.apiSecret.value || !validLimit()) return;
    clearMessage();
    batchResults = [];
    e.batchResults.replaceChildren();
    e.batchTable.hidden = true;
    e.batchEmpty.hidden = false;
    e.exportCsv.disabled = true;
    batchRunning = true;
    batchCancelRequested = false;
    e.runBatch.textContent = "Running...";
    e.cancelBatch.hidden = false;
    e.batchStatus.textContent = "Starting batch...";
    updateBatchState();
    let previousStart = 0;
    try {
      for (let index = 0; index < questions.length; index += 1) {
        if (previousStart) {
          await waitForBatchGap(Math.max(0, BATCH_GAP_MS + BATCH_START_MARGIN_MS - (Date.now() - previousStart)));
          if (batchCancelRequested) break;
        }
        previousStart = Date.now();
        e.batchStatus.textContent = `Running question ${index + 1} of ${questions.length}...`;
        try {
          const response = await submitQuestion(questions[index], repositoryForBatch, limitForBatch);
          appendBatchRow(questions[index], response);
          if (batchCancelRequested) break;
        } catch (error) {
          showApiError(error);
          e.batchStatus.textContent = error instanceof ApiError && error.status === 429
            ? "Batch stopped after the API rate limit response. Completed rows are preserved."
            : "Batch stopped after a request error. Completed rows are preserved.";
          break;
        }
      }
      if (batchCancelRequested) e.batchStatus.textContent = "Batch cancelled after the current request.";
      else if (batchResults.length) e.batchStatus.textContent = `Batch finished. ${batchResults.length} completed question${batchResults.length === 1 ? "" : "s"}.`;
      else if (!e.batchStatus.textContent.startsWith("Batch stopped")) e.batchStatus.textContent = "No questions were completed.";
    } finally {
      batchRunning = false;
      e.runBatch.textContent = "Run batch";
      e.cancelBatch.hidden = true;
      updateBatchState();
    }
  }
  function exportBatchCsv() {
    const quote = (value) => `"${String(value).replace(/"/g, '""')}"`;
    const rows = [["question", "outcome", "confidence", "latency_ms", "investigation_id"], ...batchResults.map((item) => [item.question, item.outcome, item.confidence, item.latency_ms, item.investigation_id])];
    const csv = rows.map((row) => row.map(quote).join(",")).join("\r\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = node("a");
    anchor.href = url;
    anchor.download = "incidentweave-batch-results.csv";
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }
  function openSettings() {
    if (typeof e.settingsDialog.showModal === "function") e.settingsDialog.showModal();
    else e.settingsDialog.setAttribute("open", "");
  }
  function closeSettings() {
    if (typeof e.settingsDialog.close === "function") e.settingsDialog.close();
    else e.settingsDialog.removeAttribute("open");
  }
  function updateThemeLabel() {
    const light = document.documentElement.dataset.theme === "light";
    e.themeLabel.textContent = light ? "Dark theme" : "Light theme";
    $("#theme-toggle").setAttribute("aria-label", light ? "Switch to dark theme" : "Switch to light theme");
  }
  function setTheme(theme) {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("iw.theme", theme); }
    catch { showMessage("Could not save the theme preference in this browser."); }
    updateThemeLabel();
  }
  $("#refresh-repositories").addEventListener("click", refreshRepositories);
  $("#settings-open").addEventListener("click", openSettings);
  $("#settings-open-mobile").addEventListener("click", openSettings);
  $("#settings-close").addEventListener("click", closeSettings);
  $("#settings-cancel").addEventListener("click", closeSettings);
  $("#secret-toggle").addEventListener("click", () => {
    const reveal = e.apiSecret.type === "password";
    e.apiSecret.type = reveal ? "text" : "password";
    $("#secret-toggle").textContent = reveal ? "Hide" : "Show";
    $("#secret-toggle").setAttribute("aria-pressed", String(reveal));
  });
  e.settingsForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const base = currentApiBase();
    if (base) {
      try {
        if (new URL(base, window.location.origin).origin !== window.location.origin) {
          showMessage("The API base URL must use this page's origin. The secret was not saved for another origin.");
          return;
        }
      } catch { showMessage("Enter a valid same-origin API base URL."); return; }
    }
    settings.apiBase = base;
    settings.apiSecret = e.apiSecret.value;
    try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings)); }
    catch { showMessage("Could not save settings in this browser."); return; }
    closeSettings();
    updateAskState();
    updateBatchState();
    showMessage("Settings saved in this browser.", "success");
  });
  $("#theme-toggle").addEventListener("click", () => setTheme(document.documentElement.dataset.theme === "light" ? "dark" : "light"));
  $("#tab-chat").addEventListener("click", () => activateTab("chat"));
  $("#tab-batch").addEventListener("click", () => activateTab("batch"));
  e.question.addEventListener("input", updateAskState);
  e.answerLimit.addEventListener("input", () => { updateAskState(); updateBatchState(); });
  e.askForm.addEventListener("submit", askQuestion);
  e.question.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      e.askForm.requestSubmit();
    }
  });
  e.batchInput.addEventListener("input", updateBatchState);
  e.runBatch.addEventListener("click", runBatch);
  e.cancelBatch.addEventListener("click", () => {
    batchCancelRequested = true;
    e.batchStatus.textContent = "Cancellation requested; waiting for the current request to finish.";
  });
  e.exportCsv.addEventListener("click", exportBatchCsv);
  e.loadMore.addEventListener("click", loadMoreHistory);
  e.apiSecret.addEventListener("input", () => { updateAskState(); updateBatchState(); });
  e.apiBase.addEventListener("input", () => { updateAskState(); updateBatchState(); });
  updateThemeLabel();
  updateAskState();
  updateBatchState();
  renderHistory();
  e.activeTitle.textContent = activeRepository || "Choose a repository";
  e.repoEmpty.textContent = "No repositories loaded. Refresh to check the API.";
  if (!e.apiSecret.value) showMessage("Add your X-API-Secret in Settings to use the API.", "info");
})();
