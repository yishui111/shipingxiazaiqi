// B站下载助手 选项页逻辑
"use strict";

const input = document.getElementById("token");
const msg = document.getElementById("msg");

chrome.storage.local.get("token", ({ token }) => {
  if (token) input.value = token;
});

document.getElementById("save").addEventListener("click", async () => {
  const t = input.value.trim();
  if (!t) { msg.textContent = "令牌不能为空"; return; }
  await chrome.storage.local.set({ token: t });
  msg.textContent = "已保存 ✓";
  setTimeout(() => (msg.textContent = ""), 2000);
});
