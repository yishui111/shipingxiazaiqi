// B站下载助手 弹窗逻辑
"use strict";

const GUI = "http://127.0.0.1:8787";

document.getElementById("go").addEventListener("click", async () => {
  const btn = document.getElementById("go");
  btn.disabled = true;
  btn.textContent = "发送中…";

  const { token } = await chrome.storage.local.get("token");
  if (!token) {
    btn.textContent = "下载当前视频";
    btn.disabled = false;
    chrome.runtime.openOptionsPage();
    return;
  }

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.url) {
    alert("无法获取当前页面地址");
    btn.textContent = "下载当前视频";
    btn.disabled = false;
    return;
  }

  try {
    const resp = await fetch(GUI + "/api/add?url=" + encodeURIComponent(tab.url) + "&token=" + encodeURIComponent(token));
    const j = await resp.json();
    if (j.ok) {
      await chrome.tabs.create({ url: j.gui_url });
      window.close();
    } else {
      alert("下载器返回：" + (j.error || "未知错误"));
      btn.textContent = "下载当前视频";
      btn.disabled = false;
    }
  } catch (e) {
    alert("下载器未启动！请先运行 start.bat 再点扩展按钮。");
    btn.textContent = "下载当前视频";
    btn.disabled = false;
  }
});
