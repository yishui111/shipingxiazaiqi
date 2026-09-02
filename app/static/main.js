/* B站视频下载器 —— 页面逻辑 */
(function () {
  "use strict";

  var APP = window.__APP__ || {};
  var TOKEN = APP.token || "";
  var GUI = "http://" + (APP.host || "127.0.0.1") + ":" + (APP.port || 8787);
  var $ = function (s) { return document.querySelector(s); };

  var STATUS_TEXT = {
    queued: "排队中", working: "下载中", done: "已完成", error: "出错", cancelled: "已取消"
  };

  /* ---------- 书签 ---------- */
  function buildBookmarklet() {
    // 只使用双引号，避免粘贴到书签时被转义破坏
    // 点击后自动下载当前视频；若它属于某个合集，则自动把整个合集全部下载
    var body = [
      "(function(){",
      "var t=\"" + TOKEN + "\";",
      "var g=window.open(\"" + GUI + "/\",\"_blank\");",
      "var u=location.href;",
      "fetch(\"" + GUI + "/api/add?url=\"+encodeURIComponent(u)+\"&token=\"+t)",
      ".then(function(r){return r.json()})",
      ".then(function(j){if(j.ok){if(g){g.location.href=j.gui_url}}else{if(g){g.close()}alert(\"下载器返回：\"+(j.error||\"未知错误\"))}})",
      ".catch(function(){if(g){g.close()}alert(\"下载器未启动！请先运行 start.bat\")})",
      "})();"
    ].join("");
    return "javascript:" + body;
  }

  function copyText(text, btn) {
    var done = function () {
      if (btn) { btn.textContent = "已复制 ✓"; setTimeout(function () { btn.textContent = "复制书签代码"; }, 1500); }
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { fallbackCopy(text); done(); });
    } else { fallbackCopy(text); done(); }
  }
  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text; document.body.appendChild(ta);
    ta.select(); try { document.execCommand("copy"); } catch (e) {}
    document.body.removeChild(ta);
  }

  /* ---------- 请求封装 ---------- */
  function api(path, opts) {
    opts = opts || {};
    var url = path + (path.indexOf("?") >= 0 ? "&" : "?") + "token=" + encodeURIComponent(TOKEN);
    if (opts.query) {
      Object.keys(opts.query).forEach(function (k) {
        url += "&" + encodeURIComponent(k) + "=" + encodeURIComponent(opts.query[k]);
      });
    }
    var init = { method: opts.method || "GET" };
    if (opts.body) {
      init.method = "POST";
      init.headers = { "Content-Type": "application/json" };
      init.body = JSON.stringify(opts.body);
    }
    return fetch(url, init).then(function (r) { return r.json(); });
  }

  /* ---------- 设置 ---------- */
  var currentInfo = null;

  function loadSettings() {
    api("/api/settings").then(function (j) {
      if (!j.ok) return;
      var s = j.settings;
      $("#quality").value = s.quality || "best";
      $("#range").value = s.range || "all";
      $("#series-mode").value = s.series || "auto";
      $("#cookie-source").value = s.cookie_source || "none";
      $("#overwrite").checked = !!s.overwrite;
      if (s.cookie_text === "已保存") {
        $("#cookie-text").placeholder = "已保存 Cookie（重新粘贴可覆盖）";
      } else {
        $("#cookie-text").placeholder = "登录 www.bilibili.com 后复制整串 Cookie 粘贴到这里";
      }
      toggleCookieText();
    });
  }

  function toggleCookieText() {
    $("#cookie-text-wrap").classList.toggle("hidden", $("#cookie-source").value !== "text");
  }

  $("#cookie-source").addEventListener("change", toggleCookieText);

  $("#btn-save-settings").addEventListener("click", function () {
    var btn = this; btn.disabled = true;
    api("/api/settings", {
      method: "POST",
      body: {
        quality: $("#quality").value,
        range: $("#range").value,
        series: $("#series-mode").value,
        cookie_source: $("#cookie-source").value,
        cookie_text: $("#cookie-text").value,
        overwrite: $("#overwrite").checked
      }
    }).then(function (j) {
      btn.disabled = false;
      var msg = $("#save-msg");
      msg.textContent = j.ok ? "✓ 已保存" : "保存失败：" + (j.error || "");
      msg.style.color = j.ok ? "var(--ok)" : "var(--err)";
      setTimeout(function () { msg.textContent = ""; }, 2000);
    });
  });

  /* ---------- 手动下载 ---------- */
  $("#btn-parse").addEventListener("click", function () {
    var url = $("#url").value.trim();
    if (!url) { alert("请先粘贴视频链接"); return; }
    var btn = this; btn.disabled = true; btn.textContent = "解析中…";
    api("/api/parse", { query: { url: url } }).then(function (j) {
      btn.disabled = false; btn.textContent = "解析";
      if (!j.ok) { alert(j.error || "解析失败"); return; }
      currentInfo = j;
      $("#title").textContent = j.title;
      $("#meta").textContent = (j.parts > 1 ? "共 " + j.parts + " 集/P · " : "") + "UP主：" + (j.uploader || "未知");
      var img = $("#thumb");
      if (j.thumbnail) { img.src = j.thumbnail; img.hidden = false; } else { img.hidden = true; }
      $("#info").classList.remove("hidden");
      showSeries(j.series);
      $("#info").scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
  });

  function showSeries(series) {
    var box = $("#series-box");
    if (!series || !series.episodes || !series.episodes.length) {
      box.classList.add("hidden");
      return;
    }
    $("#series-title").textContent = series.title || "未命名合集";
    $("#series-count").textContent = series.count || series.episodes.length;
    var eps = series.episodes.slice(0, 8);
    $("#series-eps").innerHTML = eps.map(function (e, i) {
      return '<div class="ep">' + (i + 1) + '. ' + esc(e.title) + "</div>";
    }).join("");
    if ((series.count || eps.length) > eps.length) {
      $("#series-eps").insertAdjacentHTML("beforeend", '<div class="ep muted">… 共 ' + (series.count || eps.length) + " 集</div>");
    }
    $("#btn-download-series").textContent = "⬇ 下载整个合集（" + (series.count || series.episodes.length) + " 集）";
    var auto = $("#series-mode").value === "auto";
    $("#series-hint").textContent = auto ? "当前设置为「自动」，点上方「开始下载」也会直接下整个合集" : "当前设置为「仅当前视频」，点上方「开始下载」只下这一集";
    box.classList.remove("hidden");
  }

  function addTasks(j, btn) {
    btn.disabled = false;
    if (!j.ok) { alert(j.error || "添加任务失败"); return; }
    (j.task_ids || []).forEach(function (id) { highlightTask(id); });
    $("#info").classList.add("hidden");
    $("#series-box").classList.add("hidden");
    $("#url").value = "";
    currentInfo = null;
    refreshTasks();
  }

  $("#btn-download").addEventListener("click", function () {
    if (!currentInfo) return;
    var url = $("#url").value.trim();
    var btn = this; btn.disabled = true;
    api("/api/add", {
      method: "POST",
      body: {
        url: url,
        quality: $("#quality").value,
        range: $("#range").value,
        series: $("#series-mode").value
      }
    }).then(function (j) { addTasks(j, btn); });
  });

  $("#btn-download-series").addEventListener("click", function () {
    if (!currentInfo) return;
    var url = $("#url").value.trim();
    var btn = this; btn.disabled = true;
    api("/api/add_series", {
      method: "POST",
      body: { url: url, quality: $("#quality").value }
    }).then(function (j) { addTasks(j, btn); });
  });

  /* ---------- 任务列表 ---------- */
  var HIGHLIGHT = null;

  function highlightTask(id) {
    HIGHLIGHT = id;
    setTimeout(function () { HIGHLIGHT = null; }, 3000);
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function fileLink(name) {
    return '<a href="' + GUI + "/files/" + encodeURIComponent(name) + '" target="_blank" rel="noopener">▶ 播放</a>';
  }

  function taskCard(t) {
    var st = t.status || "queued";
    var files = (t.files || []).filter(function (n) { return /\.(mp4|m4a|webm|mkv|flv|mp3|aac|mov)$/i.test(n); });
    var filesHtml = files.length
      ? '<div class="t-files">' + files.map(function (n) {
          return '<span>📄 ' + esc(n) + "　" + fileLink(n) + '</span>';
        }).join("") + "</div>"
      : "";
    var actions = "";
    if (st === "queued" || st === "working") {
      actions += '<button class="btn small danger act-cancel" data-id="' + t.id + '">取消</button>';
    }
    if (st === "done" || st === "error" || st === "cancelled") {
      actions += '<button class="btn small ghost act-remove" data-id="' + t.id + '">删除记录</button>';
    }
    var pct = Math.min(100, Math.max(0, Number(t.progress) || 0)).toFixed(1);
    var meta = ["进度 " + pct + "%"];
    if (t.parts_total > 1) meta.push("第 " + Math.min(t.parts_done + 1, t.parts_total) + " / " + t.parts_total + " P");
    if (st === "working") { if (t.speed) meta.push("速度 " + t.speed); if (t.eta) meta.push("剩余 " + t.eta); }
    meta.push("画质 " + (t.quality || "best"));
    var hl = (HIGHLIGHT === t.id) ? " highlight" : "";
    return '<div class="task' + hl + '" id="task-' + t.id + '">' +
      '<div class="t-head">' +
        '<span class="t-title">' + esc(t.title || "（解析中…）") + '</span>' +
        '<span class="status ' + st + '">' + (STATUS_TEXT[st] || st) + '</span>' +
      "</div>" +
      '<div class="t-url">' + esc(t.url) + "</div>" +
      '<div class="bar ' + (st === "error" || st === "cancelled" ? st : "") + '"><div style="width:' + pct + '%"></div></div>' +
      '<div class="t-meta">' + meta.join("　·　") + '</div>' +
      (t.error ? '<div class="t-err">⚠ ' + esc(t.error) + "</div>" : "") +
      (t.note ? '<div class="t-note">ℹ ' + esc(t.note) + "</div>" : "") +
      filesHtml +
      '<div class="t-actions">' + actions + "</div>" +
      "</div>";
  }

  function refreshTasks() {
    api("/api/tasks").then(function (j) {
      if (!j.ok) return;
      var tasks = j.tasks || [];
      var box = $("#tasks");
      box.innerHTML = tasks.map(taskCard).join("");
      $("#empty").style.display = tasks.length ? "none" : "";
      bindTaskActions();
    }).catch(function () {});
  }

  function bindTaskActions() {
    document.querySelectorAll(".act-cancel").forEach(function (b) {
      b.addEventListener("click", function () {
        api("/api/cancel", { method: "POST", body: { id: b.dataset.id } }).then(refreshTasks);
      });
    });
    document.querySelectorAll(".act-remove").forEach(function (b) {
      b.addEventListener("click", function () {
        api("/api/remove", { method: "POST", body: { id: b.dataset.id } }).then(refreshTasks);
      });
    });
  }

  /* ---------- 其他 ---------- */
  $("#btn-open-folder").addEventListener("click", function () {
    api("/api/openfolder").then(function (j) {
      if (!j.ok) alert(j.error || "打开失败");
    });
  });

  $("#btn-clear-finished").addEventListener("click", function () {
    api("/api/tasks").then(function (j) {
      if (!j.ok) return;
      var ids = (j.tasks || [])
        .filter(function (t) { return ["done", "error", "cancelled"].indexOf(t.status) >= 0; })
        .map(function (t) { return t.id; });
      var chain = Promise.resolve();
      ids.forEach(function (id) {
        chain = chain.then(function () {
          return api("/api/remove", { method: "POST", body: { id: id } });
        });
      });
      chain.then(refreshTasks);
    });
  });

  $("#copy-bookmark").addEventListener("click", function () {
    copyText($("#bookmarklet").value, this);
  });

  /* ---------- 初始化 ---------- */
  $("#bookmarklet").value = buildBookmarklet();
  loadSettings();
  refreshTasks();
  setInterval(refreshTasks, 1000);

  // 从书签跳转过来的进度页：高亮对应任务（支持 ?task= 单个或 ?tasks= 多个）
  function highlightFromUrl() {
    var ids = [];
    var m1 = /[?&]task=([0-9a-f]+)/.exec(location.search);
    var m2 = /[?&]tasks=([0-9a-f,]+)/.exec(location.search);
    if (m1) ids.push(m1[1]);
    if (m2) ids = ids.concat(m2[1].split(",").filter(Boolean));
    ids.forEach(function (id) { highlightTask(id); });
    if (ids.length) {
      setTimeout(function () {
        var el = document.getElementById("task-" + ids[0]);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 600);
    }
  }
  highlightFromUrl();
})();
