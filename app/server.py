# -*- coding: utf-8 -*-
"""B站视频下载器 —— 本地 Web 服务入口。

用法：
    python -m app.server            # 启动服务并自动打开浏览器
"""
import logging
import os
import re
import threading
import webbrowser

from flask import Flask, abort, jsonify, render_template, request, send_from_directory

from . import config
from .bili import (
    DownloadManager,
    fetch_info,
    get_series_info,
    is_series_url,
)

logging.basicConfig(
    filename=config.LOGS_DIR / "server.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("bili-dl")

app = Flask(__name__)
manager = DownloadManager()

# 记录 PID，供 stop.bat 停止服务
try:
    (config.DATA_DIR / "server.pid").write_text(str(os.getpid()), encoding="utf-8")
except Exception:
    pass


def _token_ok() -> bool:
    """校验令牌：GET 看 query，POST 看 query 或 JSON body。"""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        if data.get("token") == config.TOKEN:
            return True
    return request.values.get("token") == config.TOKEN


@app.after_request
def _cors(resp):
    # 允许浏览器书签/扩展跨域调用本机服务；安全由令牌保证
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.before_request
def _guard_write():
    if request.method in ("POST", "PUT", "DELETE") and not _token_ok():
        return jsonify({"ok": False, "error": "token 无效"}), 403


@app.route("/")
def index():
    return render_template(
        "index.html", token=config.TOKEN, host=config.HOST, port=config.PORT
    )


def _start_series(episodes, quality: str, settings: dict):
    """为合集每一集添加任务，返回任务 id 列表。"""
    ids = []
    for ep in episodes:
        bvid = ep.get("bvid")
        if not bvid:
            continue
        url = f"https://www.bilibili.com/video/{bvid}"
        ids.append(manager.start(url, quality, "all", settings, title=ep.get("title") or ""))
    return ids


@app.route("/api/add", methods=["GET", "POST"])
def api_add():
    if not _token_ok():
        return jsonify({"ok": False, "error": "token 无效"}), 403
    if request.method == "GET":
        url = (request.args.get("url") or "").strip()
        quality = request.args.get("quality") or ""
        range_mode = request.args.get("range") or ""
        series_mode = request.args.get("series") or ""
    else:
        data = request.get_json(silent=True) or {}
        url = str(data.get("url") or "").strip()
        quality = str(data.get("quality") or "")
        range_mode = str(data.get("range") or "")
        series_mode = str(data.get("series") or "")
    if not url:
        return jsonify({"ok": False, "error": "缺少视频链接"})
    if not url.lower().startswith(("http://", "https://")):
        return jsonify({"ok": False, "error": "链接必须以 http(s):// 开头"})
    settings = config.load_settings()
    quality = quality or settings["quality"]
    range_mode = range_mode or settings["range"]
    series_mode = series_mode or settings.get("series", "auto")

    # 合集链接（/list/ 或 /video/part/）：直接下载整个合集
    if is_series_url(url):
        info = get_series_info(url)
        if not info or not info.get("episodes"):
            return jsonify({"ok": False, "error": "未能解析该合集链接，请直接粘贴视频页链接试试"})
        ids = _start_series(info["episodes"], quality, settings)
        log.info("合集下载 %s：%s 集，任务 %s", info["title"], len(ids), ids)
        return jsonify({
            "ok": True,
            "task_ids": ids,
            "series": {"title": info["title"], "count": info["count"]},
            "gui_url": f"http://{config.HOST}:{config.PORT}/?tasks={','.join(ids)}",
        })

    # 普通视频链接：按设置决定是否自动展开合集
    if series_mode == "auto":
        info = get_series_info(url)
        if info and info.get("episodes"):
            ids = _start_series(info["episodes"], quality, settings)
            log.info("自动合集下载 %s：%s 集，任务 %s", info["title"], len(ids), ids)
            return jsonify({
                "ok": True,
                "task_ids": ids,
                "series": {"title": info["title"], "count": info["count"]},
                "gui_url": f"http://{config.HOST}:{config.PORT}/?tasks={','.join(ids)}",
            })

    tid = manager.start(url, quality, range_mode, settings)
    log.info("新增下载任务 %s <- %s", tid, url)
    return jsonify({
        "ok": True,
        "task_ids": [tid],
        "gui_url": f"http://{config.HOST}:{config.PORT}/?task={tid}",
    })


@app.route("/api/add_series", methods=["GET", "POST"])
def api_add_series():
    """显式下载整个合集：参数 url（任意含 bvid 的链接）或直接给 bvid。"""
    if not _token_ok():
        return jsonify({"ok": False, "error": "token 无效"}), 403
    if request.method == "GET":
        url = (request.args.get("url") or "").strip()
        quality = request.args.get("quality") or ""
    else:
        data = request.get_json(silent=True) or {}
        url = str(data.get("url") or "").strip()
        quality = str(data.get("quality") or "")
    if not url:
        return jsonify({"ok": False, "error": "缺少链接"})
    if not re.match(r"^(BV[0-9A-Za-z]{10}|https?://)", url):
        return jsonify({"ok": False, "error": "链接格式不正确"})
    if not url.lower().startswith("http"):
        url = f"https://www.bilibili.com/video/{url}"
    settings = config.load_settings()
    quality = quality or settings["quality"]
    info = get_series_info(url)
    if not info or not info.get("episodes"):
        return jsonify({"ok": False, "error": "该视频不属于任何合集，或合集解析失败"})
    ids = _start_series(info["episodes"], quality, settings)
    log.info("合集批量下载 %s：%s 集，任务 %s", info["title"], len(ids), ids)
    return jsonify({
        "ok": True,
        "task_ids": ids,
        "series": {"title": info["title"], "count": info["count"]},
        "gui_url": f"http://{config.HOST}:{config.PORT}/?tasks={','.join(ids)}",
    })


@app.route("/api/parse")
def api_parse():
    if not _token_ok():
        return jsonify({"ok": False, "error": "token 无效"}), 403
    url = (request.args.get("url") or "").strip()
    if not url:
        return jsonify({"ok": False, "error": "缺少视频链接"})
    try:
        # 合集链接不走 yt-dlp（会被B站风控），直接用官方接口
        if is_series_url(url):
            info = get_series_info(url)
            if not info:
                return jsonify({"ok": False, "error": "未能解析该合集链接"})
            return jsonify({
                "ok": True,
                "title": info["title"],
                "thumbnail": "",
                "uploader": "",
                "parts": info["count"],
                "parts_titles": [e["title"] for e in info["episodes"]],
                "series": info,
            })
        info = fetch_info(url)
        series = get_series_info(url)
        return jsonify({"ok": True, **info, "series": series})
    except Exception as e:  # noqa: BLE001
        log.warning("解析失败 %s: %s", url, e)
        return jsonify({"ok": False, "error": f"解析失败：{str(e)[:240]}"})


@app.route("/api/tasks")
def api_tasks():
    if not _token_ok():
        return jsonify({"ok": False, "error": "token 无效"}), 403
    return jsonify({"ok": True, "tasks": manager.all()})


@app.route("/api/cancel", methods=["POST"])
def api_cancel():
    if not _token_ok():
        return jsonify({"ok": False, "error": "token 无效"}), 403
    data = request.get_json(silent=True) or {}
    tid = data.get("id") or request.args.get("id") or ""
    return jsonify({"ok": manager.cancel(tid)})


@app.route("/api/remove", methods=["POST"])
def api_remove():
    if not _token_ok():
        return jsonify({"ok": False, "error": "token 无效"}), 403
    data = request.get_json(silent=True) or {}
    tid = data.get("id") or request.args.get("id") or ""
    return jsonify({"ok": bool(manager.delete(tid))})


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    if request.method == "POST":
        if not _token_ok():
            return jsonify({"ok": False, "error": "token 无效"}), 403
        data = request.get_json(silent=True) or {}
        s = config.save_settings(data)
        return jsonify({"ok": True, "settings": _public_settings(s)})
    return jsonify({"ok": True, "settings": _public_settings(config.load_settings())})


@app.route("/api/openfolder")
def api_openfolder():
    if not _token_ok():
        return jsonify({"ok": False, "error": "token 无效"}), 403
    try:
        os.startfile(config.DOWNLOADS_DIR)  # Windows 专用
    except Exception as e:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(e)})
    return jsonify({"ok": True})


@app.route("/files/<path:name>")
def files(name):
    """本地播放已下载的视频（支持进度条拖拽）。"""
    root = config.DOWNLOADS_DIR.resolve()
    p = (root / name).resolve()
    if not str(p).startswith(str(root)):
        abort(404)
    return send_from_directory(config.DOWNLOADS_DIR, name, conditional=True)


def _public_settings(s: dict) -> dict:
    p = dict(s)
    p["cookie_text"] = "已保存" if (s.get("cookie_text") or "").strip() else ""
    return p


def main():
    url = f"http://{config.HOST}:{config.PORT}"
    log.info("服务启动: %s", url)
    print(f"B站视频下载器已启动: {url}")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    app.run(host=config.HOST, port=config.PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
