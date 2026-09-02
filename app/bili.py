# -*- coding: utf-8 -*-
"""B站视频下载核心。

基于 yt-dlp 实现；ffmpeg 由 imageio-ffmpeg 包内置提供（无需系统安装 ffmpeg）。
支持：单P视频、多P（分P）视频、合集（系列）、收藏夹链接；可选浏览器登录态 Cookie 解锁更高画质。

注意：B站对 yt-dlp 直接解析 /list/ 合集链接会风控（"视频列表加载失败"），
所以合集下载统一走 B站官方接口 seasons_archives_list 拉剧集列表，再逐集下载。
"""
import json
import logging
import os
import re
import threading
import time
import urllib.parse
import urllib.request
import uuid

import imageio_ffmpeg
import yt_dlp

from . import config

log = logging.getLogger("bili-dl")

# 合集批量下载的最大并发数（避免一次开太多线程把网络/磁盘打满）
SERIES_MAX_CONCURRENCY = 3
# 一次合集下载允许的最大集数（防止误触发超大合集）
SERIES_MAX_EPISODES = 500

# 简单 UA：B站对"过于完整"的 UA 反而会风控（-352），简单 UA 更稳
_UA = {"User-Agent": "Mozilla/5.0"}

# 画质选项 -> yt-dlp 的 format 选择规则
FORMATS = {
    "best":  "bv*+ba/b",            # 最高可用（登录后一般到 1080P，大会员可更高）
    "1080p": "bv*[height<=1080]+ba/b",
    "720p":  "bv*[height<=720]+ba/b",
    "480p":  "bv*[height<=480]+ba/b",  # 未登录时的常见上限
    "360p":  "bv*[height<=360]+ba/b",
    "audio": "ba/b",                # 仅音频
}

BROWSERS = ("chrome", "edge", "firefox", "opera", "brave", "vivaldi")


class DownloadCancelled(Exception):
    """用于在 yt-dlp 进度回调里中断下载。"""


def raw_cookie_to_netscape(raw: str) -> str:
    """把浏览器里复制的一整串 Cookie（k=v; k2=v2; ...）转成 Netscape 格式文本。"""
    lines = [
        "# Netscape HTTP Cookie File",
        "# 由 B站下载器 自动生成，仅用于获取更高画质",
    ]
    seen = set()
    for part in raw.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        k, v = part.split("=", 1)
        k, v = k.strip(), v.strip()
        if not k or (k, v) in seen:
            continue
        seen.add((k, v))
        lines.append(f".bilibili.com\tTRUE\t/\tFALSE\t0\t{k}\t{v}")
    return "\n".join(lines) + "\n"


def cookies_opts(settings: dict) -> dict:
    """根据设置返回 yt-dlp 的 Cookie 相关选项。"""
    src = (settings or {}).get("cookie_source", "none")
    if src in BROWSERS:
        return {"cookiesfrombrowser": (src,)}
    if src == "text" and (settings.get("cookie_text") or "").strip():
        path = config.DATA_DIR / "cookies_netscape.txt"
        path.write_text(raw_cookie_to_netscape(settings["cookie_text"]), encoding="utf-8")
        return {"cookiefile": str(path)}
    return {}


class DownloadManager:
    """任务管理：每个下载任务一个后台线程，进度通过 yt-dlp 回调写回任务字典。

    合集批量下载时用信号量限制同时进行的下载数（SERIES_MAX_CONCURRENCY）。
    """

    def __init__(self):
        self.tasks = {}
        self._lock = threading.Lock()
        self._sem = threading.Semaphore(SERIES_MAX_CONCURRENCY)

    # ---------- 基础操作 ----------
    def get(self, tid):
        with self._lock:
            return self.tasks.get(tid)

    def all(self):
        with self._lock:
            return [dict(t) for t in self.tasks.values()]

    def delete(self, tid):
        with self._lock:
            return self.tasks.pop(tid, None)

    # ---------- 新建任务 ----------
    def start(self, url: str, quality: str, range_mode: str, settings: dict, title: str = "") -> str:
        tid = uuid.uuid4().hex[:12]
        task = {
            "id": tid,
            "url": url,
            "quality": quality if quality in FORMATS else "best",
            "range": range_mode if range_mode in ("all", "first") else "all",
            "status": "queued",          # queued/working/done/error/cancelled
            "title": title,              # 合集下载时预填剧集标题，下载开始后由真实标题覆盖
            "thumbnail": "",
            "parts_total": 1,
            "parts_done": 0,
            "progress": 0.0,
            "speed": "",
            "eta": "",
            "files": [],                 # 本次任务产出的文件（basename 列表）
            "filename": "",              # 第一个产出的文件，用于展示
            "note": "",                  # 附加提示（如同名文件已存在）
            "error": "",
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "cancel": False,
            "settings": settings,
            "_last_progress": 0.0,  # 用于保证进度条只增不减
        }
        with self._lock:
            self.tasks[tid] = task
        threading.Thread(target=self._run, args=(tid,), daemon=True).start()
        return tid

    def cancel(self, tid) -> bool:
        t = self.get(tid)
        if not t or t["status"] not in ("queued", "working"):
            return False
        t["cancel"] = True
        return True

    # ---------- 下载主流程 ----------
    def _run(self, tid):
        t = self.get(tid)
        if not t:
            return
        # 并发名额：排队等待；若在排队期间被取消则直接退出
        self._sem.acquire()
        try:
            if t.get("cancel"):
                t["status"] = "cancelled"
                return
            t["status"] = "working"
            started = time.time()
            ydl_opts = {
                "outtmpl": str(config.DOWNLOADS_DIR / "%(title)s_%(id)s%(playlist_index&_P{0:02d}|)s.%(ext)s"),
                "format": FORMATS.get(t["quality"], FORMATS["best"]),
                "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
                "merge_output_format": "mp4",
                "noplaylist": t["range"] == "first",
                "playlist_items": "1" if t["range"] == "first" else None,
                "progress_hooks": [lambda d: self._hook(tid, d)],
                "retries": 5,
                "fragment_retries": 5,
                "concurrent_fragment_downloads": 4,
                "windowsfilenames": True,
                "noprogress": True,
                "quiet": True,
                "no_warnings": True,
            }
            ydl_opts.update(cookies_opts(t.get("settings") or config.load_settings()))
            settings = t.get("settings") or config.load_settings()
            ydl_opts["overwrites"] = bool(settings.get("overwrite"))
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(t["url"], download=True)
                if t["cancel"]:
                    t["status"] = "cancelled"
                else:
                    t["status"] = "done"
                    t["progress"] = 100.0
            except DownloadCancelled:
                t["status"] = "cancelled"
            except Exception as e:  # noqa: BLE001 —— 错误信息展示给用户
                t["status"] = "error"
                t["error"] = str(e)[:600]
            finally:
                # 收集本次任务真正产出的文件：只认包含本视频 ID 的文件，且排除未完成的 .part 临时文件
                try:
                    m = re.search(r"(BV[0-9A-Za-z]{10}|av\d+)", t["url"], re.IGNORECASE)
                    vid = m.group(1).upper() if m else None
                    names = []
                    for f in config.DOWNLOADS_DIR.iterdir():
                        if not f.is_file() or f.suffix == ".part":
                            continue
                        try:
                            mtime_ok = f.stat().st_mtime >= started
                        except OSError:
                            mtime_ok = False
                        if mtime_ok and (vid is None or vid in f.name.upper()):
                            names.append(f.name)
                    names.sort()
                    t["files"] = names
                    t["filename"] = names[0] if names else (t.get("filename") or "")
                    if t["status"] == "done" and not names:
                        t["note"] = "同名文件已存在，本次未重复下载（如需重下请勾选“覆盖已有文件”）"
                    else:
                        t["note"] = ""
                except Exception as e:  # noqa: BLE001
                    log.exception("收集任务文件失败: %s", e)
        finally:
            self._sem.release()

    # ---------- 进度回调 ----------
    def _hook(self, tid, d):
        t = self.get(tid)
        if not t:
            return
        if t.get("cancel"):
            raise DownloadCancelled()
        info = d.get("info_dict") or {}
        if info.get("title"):
            t["title"] = info["title"]
        if info.get("thumbnail"):
            t["thumbnail"] = info["thumbnail"]
        if info.get("playlist_count"):
            t["parts_total"] = info["playlist_count"]
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            got = d.get("downloaded_bytes") or 0
            frac = (got / total) if total else 0.0
            base = (info.get("playlist_index") or 1) - 1
            overall = (base + frac) / max(1, t["parts_total"])
            # 进度只增不减，避免分P切换时跳动
            if overall >= t.get("_last_progress", 0.0):
                t["_last_progress"] = overall
            t["progress"] = round(min(t["_last_progress"] * 100, 99.9), 1)
            t["parts_done"] = base
            t["speed"] = d.get("_speed_str") or ""
            t["eta"] = d.get("_eta_str") or ""
        elif d.get("status") == "finished":
            base = info.get("playlist_index") or 1
            t["parts_done"] = base
            p = base / max(1, t["parts_total"]) * 100
            if p >= t.get("_last_progress", 0.0) * 100:
                t["_last_progress"] = p / 100
            t["progress"] = round(min(p, 99.9), 1)


def fetch_info(url: str) -> dict:
    """只解析不下载，返回标题/封面/分P等信息，用于下载前预览。"""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "in_playlist",
        "noplaylist": False,
        "playlist_items": "1-100",
        "socket_timeout": 15,
    }
    opts.update(cookies_opts(config.load_settings()))
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise ValueError("未能解析该链接")
    title = info.get("title") or "未知标题"
    entries = info.get("entries")
    if isinstance(entries, list) and entries:
        parts = len(entries)
        parts_titles = [(e.get("title") or "") for e in entries[:100]]
    else:
        parts = 1
        parts_titles = [title]
    return {
        "title": title,
        "thumbnail": info.get("thumbnail") or "",
        "uploader": info.get("uploader") or "",
        "parts": parts,
        "parts_titles": parts_titles,
    }


# ============================================================
#  合集（系列）识别与剧集拉取 —— 走 B站官方接口
# ============================================================

def _http_get_json(url: str, timeout: int = 15) -> dict:
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def video_id_from_url(url: str):
    """从链接提取视频 ID，返回 (类型, 值)，类型为 bvid / aid / (None, None)。

    注意：BV 号大小写敏感，必须保留原始大小写，否则 B站 API 查不到。
    """
    m = re.search(r"(BV[0-9A-Za-z]{10})", url)
    if m:
        return ("bvid", m.group(1))
    m = re.search(r"(?:av|/video/av)(\d+)", url, re.IGNORECASE)
    if m:
        return ("aid", m.group(1))
    return (None, None)


def is_series_url(url: str) -> bool:
    """是否是合集/系列链接（新版 /list/ 或旧版 /video/part/）。"""
    low = url.lower()
    return "/list/" in low or "/video/part/" in low


def _fetch_series_episodes(season_id, mid, max_pages=20):
    """分页拉取合集全部剧集，返回 [{bvid, title}, ...]。"""
    out, seen = [], set()
    for page in range(1, max_pages + 1):
        url = (f"https://api.bilibili.com/x/polymer/web-space/seasons_archives_list"
               f"?mid={mid}&season_id={season_id}&page_num={page}&page_size=30")
        try:
            d = _http_get_json(url)
        except Exception as e:  # noqa: BLE001
            log.warning("拉取合集剧集失败 page=%s: %s", page, e)
            break
        arcs = (d.get("data") or {}).get("archives") or []
        if not arcs:
            break
        for a in arcs:
            bvid = a.get("bvid")
            if bvid and bvid not in seen:
                seen.add(bvid)
                out.append({"bvid": bvid, "title": a.get("title") or ""})
            if len(out) >= SERIES_MAX_EPISODES:
                return out
    return out


def get_series_info(url: str):
    """返回合集信息，非合集返回 None。

    返回: {season_id, title, count, episodes: [{bvid, title}, ...]}
    """
    kind, vid = video_id_from_url(url)
    if not vid:
        return None
    try:
        d = _http_get_json(f"https://api.bilibili.com/x/web-interface/view?{kind}={vid}")
    except Exception as e:  # noqa: BLE001
        log.warning("查询合集信息失败 %s: %s", url, e)
        return None
    data = d.get("data") or {}
    season = data.get("ugc_season")
    if not season:
        return None
    mid = (data.get("owner") or {}).get("mid")
    season_id = season.get("id")
    title = season.get("title") or "未命名合集"
    count = int(season.get("ep_count") or 0)
    episodes = _fetch_series_episodes(season_id, mid)
    if episodes and not count:
        count = len(episodes)
    return {
        "season_id": season_id,
        "title": title,
        "count": count,
        "episodes": episodes,
    }
