(() => {
  const state = {
    studies: [],
    studyId: null,
    history: [],
    index: 0,
    playing: false,
    timer: null,
    requestId: 0,
    vectors: true,
    footprint: true,
    nasaImagery: true,
    theme: "dark",
  };

  const el = (id) => document.getElementById(id);

  async function api(path) {
    const response = await fetch(path, { headers: { Accept: "application/json" } });
    if (!response.ok) {
      const detail = response.headers.get("content-type")?.includes("application/json")
        ? (await response.json()).detail
        : response.statusText;
      throw new Error(detail || `Request failed (${response.status})`);
    }
    return response.json();
  }

  function setStatus(ready, message) {
    const status = el("api-status");
    status.textContent = message;
    status.parentElement.classList.toggle("failed", !ready);
  }

  function showError(error) {
    const banner = el("error-banner");
    banner.textContent = error instanceof Error ? error.message : String(error);
    banner.hidden = false;
    setStatus(false, "API ISSUE");
  }

  function hideError() {
    el("error-banner").hidden = true;
    setStatus(true, "LOCAL API READY");
  }

  function applyTheme(theme, persist = true) {
    state.theme = theme === "light" ? "light" : "dark";
    document.documentElement.dataset.theme = state.theme;
    const isDark = state.theme === "dark";
    el("theme-label").textContent = isDark ? "Light mode" : "Dark mode";
    el("theme-toggle").setAttribute("aria-label", `Switch to ${isDark ? "light" : "dark"} mode`);
    if (persist) {
      try { localStorage.setItem("dancing-sars-theme", state.theme); } catch (_) { /* Theme still works for this session. */ }
    }
    if (state.studyId) updateMap();
  }

  function selectedStudy() {
    return state.studies.find((study) => study.id === state.studyId);
  }

  function dateObject(isoDate) {
    return new Date(`${isoDate}T00:00:00Z`);
  }

  function formatDate(isoDate, options = { day: "2-digit", month: "short", year: "numeric" }) {
    return new Intl.DateTimeFormat("en", { ...options, timeZone: "UTC" }).format(dateObject(isoDate)).toUpperCase();
  }

  function formatDistance(meters) {
    if (meters >= 1000) return `${(meters / 1000).toFixed(2)} km`;
    if (meters >= 1) return `${meters.toFixed(meters >= 100 ? 0 : 1)} m`;
    if (meters >= 0.01) return `${(meters * 100).toFixed(1)} cm`;
    return `${(meters * 1000).toFixed(1)} mm`;
  }

  function formatRate(metersPerYear) {
    if (metersPerYear >= 1) return `${Math.round(metersPerYear).toLocaleString()} m/yr`;
    return `${(metersPerYear * 100).toFixed(2)} cm/yr`;
  }

  function formatCoordinate(value, positive, negative) {
    return `${Math.abs(value).toFixed(2)}° ${value >= 0 ? positive : negative}`;
  }

  function fillStudyHeader(study) {
    el("study-region").textContent = study.region;
    el("study-phenomenon").textContent = study.phenomenon.toUpperCase();
    el("mission-phenomenon").textContent = study.phenomenon.toUpperCase();
    el("mission-study").textContent = study.name.toUpperCase();
    el("mission-region").textContent = study.region.split("·")[0].trim().toUpperCase();
    el("coordinates").textContent = `${formatCoordinate(study.latitude, "N", "S")}  ${formatCoordinate(study.longitude, "E", "W")}`;
    el("study-description").textContent = study.description;
    el("timeline-title").textContent = study.phenomenon;
  }

  async function loadStudies() {
    state.studies = await api("/api/studies");
    const select = el("study-select");
    select.replaceChildren();
    for (const study of state.studies) {
      const option = document.createElement("option");
      option.value = study.id;
      option.textContent = study.name;
      select.append(option);
    }
    state.studyId = state.studies[0]?.id;
    if (!state.studyId) throw new Error("The API did not return any study areas.");
    select.value = state.studyId;
  }

  async function loadStudy() {
    stopPlayback();
    state.index = 0;
    const study = selectedStudy();
    fillStudyHeader(study);
    hideError();
    state.history = await api(`/api/studies/${encodeURIComponent(state.studyId)}/history`);
    el("date-slider").max = String(state.history.length - 1);
    el("date-start").textContent = formatDate(state.history[0].date, { month: "short", year: "numeric" });
    el("date-end").textContent = formatDate(state.history.at(-1).date, { month: "short", year: "numeric" });
    el("range-start").textContent = el("date-start").textContent;
    el("range-end").textContent = el("date-end").textContent;
    el("timeline-ticks").innerHTML = [0, 4, 8, 12]
      .map((index) => `<span>${formatDate(state.history[index].date, { month: "short", year: "numeric" })}</span>`)
      .join("");
    renderHistory();
    await loadObservation();
  }

  async function loadObservation() {
    const currentRequest = ++state.requestId;
    const slider = el("date-slider");
    slider.value = String(state.index);
    const progress = state.history.length > 1 ? (state.index / (state.history.length - 1)) * 100 : 0;
    slider.style.setProperty("--range-progress", `${progress}%`);
    const record = state.history[state.index];
    if (!record) return;
    el("selected-date").textContent = formatDate(record.date);
    el("map-loading").classList.add("visible");
    try {
      const observation = await api(`/api/studies/${encodeURIComponent(state.studyId)}/observations/${state.index}`);
      if (currentRequest !== state.requestId) return;
      hideError();
      el("metric-velocity").textContent = formatRate(observation.median_velocity_m_year);
      el("metric-displacement").textContent = formatDistance(observation.mean_displacement_m);
      el("metric-displacement-foot").textContent = `Since ${formatDate(state.history[0].date, { month: "short", year: "numeric" })}`;
      el("metric-samples").textContent = observation.sample_count.toLocaleString();
      el("metric-interval").textContent = `${observation.interval_days} days`;
      el("download-button").href = `/api/studies/${encodeURIComponent(state.studyId)}/observations/${state.index}/csv`;
      updateMap();
    } catch (error) {
      if (currentRequest === state.requestId) showError(error);
    }
  }

  function updateMap() {
    if (!state.studyId) return;
    const query = new URLSearchParams({
      vectors: String(state.vectors),
      footprint: String(state.footprint),
      nasa_imagery: String(state.nasaImagery),
      theme: state.theme,
      cache: String(Date.now()),
    });
    el("map-loading").classList.add("visible");
    el("map-frame").src = `/api/studies/${encodeURIComponent(state.studyId)}/observations/${state.index}/map?${query}`;
  }

  function renderHistory() {
    const host = el("history-chart");
    if (!state.history.length) {
      host.replaceChildren();
      return;
    }
    const width = 740;
    const height = 184;
    const left = 52;
    const right = 18;
    const top = 12;
    const bottom = 31;
    const values = state.history.map((point) => Number(point.mean_displacement_m));
    const maximum = Math.max(...values) * 1.12 || 1;
    const plotWidth = width - left - right;
    const plotHeight = height - top - bottom;
    const points = values.map((value, index) => ({
      x: left + index * plotWidth / Math.max(1, values.length - 1),
      y: top + plotHeight * (1 - value / maximum),
    }));
    const path = points.map((point, index) => `${index ? "L" : "M"}${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(" ");
    const area = `${path} L${points.at(-1).x.toFixed(1)},${(top + plotHeight).toFixed(1)} L${left},${(top + plotHeight).toFixed(1)} Z`;
    const grid = [0, 1, 2, 3].map((step) => {
      const y = top + plotHeight * step / 3;
      const value = maximum * (1 - step / 3);
      return `<line class="grid-line" x1="${left}" y1="${y}" x2="${width - right}" y2="${y}"/><text x="${left - 8}" y="${y + 3}" text-anchor="end">${formatDistance(value)}</text>`;
    }).join("");
    const dots = points.map((point, index) => `<circle class="chart-dot" cx="${point.x}" cy="${point.y}" r="${index === state.index ? 4 : 2.5}"/>`).join("");
    const labels = [0, 4, 8, 12].map((index) => {
      const point = points[index];
      return `<text x="${point.x}" y="${height - 7}" text-anchor="middle">${formatDate(state.history[index].date, { month: "short", year: "numeric" })}</text>`;
    }).join("");
    host.innerHTML = `<svg viewBox="0 0 ${width} ${height}" aria-hidden="true">${grid}<path class="chart-area" d="${area}"/><path class="chart-line" d="${path}"/>${dots}${labels}</svg>`;
  }

  function stopPlayback() {
    if (state.timer) window.clearInterval(state.timer);
    state.timer = null;
    state.playing = false;
    el("play-button").innerHTML = '<span class="play-glyph">▶</span><span>Play</span>';
    el("play-button").setAttribute("aria-label", "Play timeline");
  }

  function startPlayback() {
    if (state.index >= state.history.length - 1) state.index = 0;
    state.playing = true;
    el("play-button").innerHTML = '<span class="play-glyph">Ⅱ</span><span>Pause</span>';
    el("play-button").setAttribute("aria-label", "Pause timeline");
    const tick = () => {
      if (!state.playing) return;
      if (state.index >= state.history.length - 1) {
        stopPlayback();
        return;
      }
      state.index += 1;
      loadObservation();
      renderHistory();
    };
    state.timer = window.setInterval(tick, Number(el("speed-select").value));
  }

  function bindEvents() {
    el("study-select").addEventListener("change", async (event) => {
      state.studyId = event.target.value;
      try { await loadStudy(); } catch (error) { showError(error); }
    });
    el("date-slider").addEventListener("input", () => {
      stopPlayback();
      state.index = Number(el("date-slider").value);
      loadObservation();
      renderHistory();
    });
    el("play-button").addEventListener("click", () => {
      if (state.playing) stopPlayback();
      else startPlayback();
    });
    el("reset-button").addEventListener("click", () => {
      stopPlayback();
      state.index = 0;
      loadObservation();
      renderHistory();
    });
    el("speed-select").addEventListener("change", () => {
      if (state.playing) {
        stopPlayback();
        startPlayback();
      }
    });
    el("theme-toggle").addEventListener("click", () => applyTheme(state.theme === "dark" ? "light" : "dark"));
    el("vectors-toggle").addEventListener("change", (event) => {
      state.vectors = event.target.checked;
      updateMap();
    });
    el("footprint-toggle").addEventListener("change", (event) => {
      state.footprint = event.target.checked;
      updateMap();
    });
    el("nasa-imagery-toggle").addEventListener("change", (event) => {
      state.nasaImagery = event.target.checked;
      updateMap();
    });
    el("map-frame").addEventListener("load", () => el("map-loading").classList.remove("visible"));
    window.addEventListener("beforeunload", stopPlayback);
  }

  async function initialize() {
    try {
      const savedTheme = localStorage.getItem("dancing-sars-theme");
      applyTheme(savedTheme || "dark", false);
    } catch (_) {
      applyTheme("dark", false);
    }
    bindEvents();
    try {
      await api("/api/health");
      setStatus(true, "LOCAL API READY");
      await loadStudies();
      await loadStudy();
    } catch (error) {
      showError(error);
    }
  }

  document.addEventListener("DOMContentLoaded", initialize);
})();
