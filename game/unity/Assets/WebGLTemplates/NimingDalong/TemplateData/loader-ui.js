(function () {
  "use strict";

  const screen = document.getElementById("loading-screen");
  const progress = document.getElementById("loading-progress");
  const progressbar = document.querySelector("[role='progressbar']");
  const percent = document.getElementById("loading-percent");
  const label = document.getElementById("loading-label");
  const stage = document.getElementById("loading-stage");
  const time = document.getElementById("loading-time");
  const retry = document.getElementById("retry-button");
  const warning = document.getElementById("unity-warning");

  const state = {
    startedAt: 0,
    lastAt: 0,
    lastProgress: 0,
    smoothedRate: 0,
    script: null
  };

  function showBanner(message, type) {
    const item = document.createElement("div");
    item.className = "unity-banner" + (type === "error" ? " error" : "");
    item.textContent = message;
    warning.appendChild(item);
    if (type !== "error") {
      window.setTimeout(() => item.remove(), 5200);
    }
  }

  function formatRemaining(seconds) {
    if (!Number.isFinite(seconds) || seconds <= 0 || seconds > 3600) {
      return "估計尚餘 --";
    }
    if (seconds < 8) {
      return "即將完成";
    }
    if (seconds < 60) {
      return `估計尚餘 ${Math.ceil(seconds)} 秒`;
    }
    return `估計尚餘 ${Math.ceil(seconds / 60)} 分鐘`;
  }

  function stageFor(value) {
    if (value < 0.08) return "整理行裝";
    if (value < 0.36) return "下載陽谷縣";
    if (value < 0.72) return "搭建城門與燈火";
    if (value < 0.94) return "喚醒命盤";
    return "準備入城";
  }

  function update(value) {
    const now = performance.now();
    const safe = Math.max(0, Math.min(1, value || 0));
    const deltaProgress = safe - state.lastProgress;
    const deltaSeconds = (now - state.lastAt) / 1000;

    if (deltaProgress > 0.0001 && deltaSeconds > 0) {
      const instantRate = deltaProgress / deltaSeconds;
      state.smoothedRate = state.smoothedRate
        ? state.smoothedRate * 0.76 + instantRate * 0.24
        : instantRate;
    }

    state.lastAt = now;
    state.lastProgress = safe;
    const valuePercent = Math.floor(safe * 100);
    progress.style.width = `${Math.max(1, safe * 100)}%`;
    progressbar.setAttribute("aria-valuenow", String(valuePercent));
    percent.textContent = `${valuePercent}%`;
    stage.textContent = stageFor(safe);
    label.textContent = safe > 0.94 ? "正在點亮最後一盞燈⋯⋯" : "正在打開陽谷縣⋯⋯";
    time.textContent = formatRemaining(
      state.smoothedRate > 0 ? (1 - safe) / state.smoothedRate : NaN
    );
  }

  function finish() {
    update(1);
    label.textContent = "命盤已開";
    stage.textContent = "歡迎重返陽谷縣";
    time.textContent = "完成";
    screen.setAttribute("aria-busy", "false");
    window.setTimeout(() => {
      screen.classList.add("is-complete");
      window.setTimeout(() => screen.remove(), 720);
    }, 360);
  }

  function fail(error) {
    console.error(error);
    label.textContent = "未能打開陽谷縣";
    stage.textContent = "請檢查網絡後再試";
    time.textContent = "";
    retry.classList.add("is-visible");
    retry.onclick = () => window.location.reload();
    showBanner(
      error && error.message ? error.message : String(error || "Unity 載入失敗"),
      "error"
    );
  }

  function start(loaderUrl, canvas, config) {
    state.startedAt = performance.now();
    state.lastAt = state.startedAt;
    update(0);

    const script = document.createElement("script");
    state.script = script;
    script.src = loaderUrl;
    script.onload = () => {
      createUnityInstance(canvas, config, update)
        .then((instance) => {
          window.unityInstance = instance;
          finish();
        })
        .catch(fail);
    };
    script.onerror = () => fail(new Error("未能下載 Unity 啟動器。"));
    document.body.appendChild(script);
  }

  window.NimingLoader = {
    start,
    showBanner
  };
})();
