# -*- coding: utf-8 -*-
"""项目路径与基础配置。

所有运行时数据（令牌、设置、Cookie、下载文件、日志）都放在项目目录内部，
因此整个文件夹复制到另一台电脑即可带走全部资料。
"""
import base64
import json
import os
import secrets
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # PyInstaller 打包后的独立 exe：所有数据放在 exe 所在目录
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
DATA_DIR = BASE_DIR / "data"
DOWNLOADS_DIR = BASE_DIR / "downloads"
LOGS_DIR = BASE_DIR / "logs"

# 可用环境变量覆盖：BILI_HOST / BILI_PORT（或写入 .env 由脚本导出）
HOST = os.environ.get("BILI_HOST", "127.0.0.1")
PORT = int(os.environ.get("BILI_PORT", "8787"))

for _d in (DATA_DIR, DOWNLOADS_DIR, LOGS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = DATA_DIR / "settings.json"
TOKEN_FILE = DATA_DIR / "token.txt"


def get_token() -> str:
    """首次运行自动生成随机令牌；书签/扩展请求必须携带它，防止任意网页触发下载。"""
    if TOKEN_FILE.exists():
        t = TOKEN_FILE.read_text(encoding="utf-8").strip()
        if t:
            return t
    t = base64.urlsafe_b64encode(secrets.token_bytes(24)).decode().rstrip("=")
    TOKEN_FILE.write_text(t, encoding="utf-8")
    return t


TOKEN = get_token()

DEFAULT_SETTINGS = {
    "quality": "best",        # best/1080p/720p/480p/360p/audio
    "range": "all",           # all=全部分P或整个合集, first=仅第1P/当前视频
    "cookie_source": "none",  # none/chrome/edge/firefox/opera/brave/vivaldi/text
    "cookie_text": "",        # 手动粘贴的整串 Cookie
    "overwrite": False,       # True=同名文件也重新下载
    "series": "auto",         # auto=检测到合集自动下载整个合集, single=只下载当前视频
}


def load_settings() -> dict:
    s = dict(DEFAULT_SETTINGS)
    if SETTINGS_FILE.exists():
        try:
            s.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return s


def save_settings(data: dict) -> dict:
    s = load_settings()
    for k in ("quality", "range", "cookie_source", "series"):
        if data.get(k):
            s[k] = str(data[k])
    if isinstance(data.get("cookie_text"), str):
        s["cookie_text"] = data["cookie_text"].strip()
    if "overwrite" in data:
        s["overwrite"] = bool(data["overwrite"])
    SETTINGS_FILE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    return s
