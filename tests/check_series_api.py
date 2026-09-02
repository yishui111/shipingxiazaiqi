# -*- coding: utf-8 -*-
"""验证合集剧集的两种获取方式。"""
import json
import urllib.request

UA = {"User-Agent": "Mozilla/5.0"}
BVID = "BV1Z9gT61EnM"
SEASON_ID = 8042010


def get(url):
    return json.load(urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=20))


print("=== 方式1: seasons_archives_list 老接口 ===")
try:
    dd = get("https://api.bilibili.com/x/web-interface/view?bvid=" + BVID)
    mid = (dd.get("data") or {}).get("owner", {}).get("mid")
    print("up主 mid =", mid)
    rr = get(f"https://api.bilibili.com/x/polymer/web-space/seasons_archives_list?mid={mid}&season_id={SEASON_ID}&page_num=1&page_size=10")
    data = rr.get("data") or {}
    arcs = data.get("archives") or []
    print("接口code:", rr.get("code"), "msg:", rr.get("message"), "| total:", data.get("total"))
    print("前3集:", [(a.get("bvid"), (a.get("title") or "")[:12]) for a in arcs[:3]])
except Exception as e:
    print("方式1失败:", e)

print()
print("=== 方式2: yt-dlp 直接解析合集链接 /list/ ===")
import yt_dlp
url = f"https://www.bilibili.com/list/{BVID}?season_id={SEASON_ID}"
try:
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "extract_flat": "in_playlist", "playlist_items": "1-5"}) as ydl:
        info = ydl.extract_info(url, download=False)
    entries = info.get("entries") or []
    print("yt-dlp 解析成功! 合集标题:", info.get("title"), "| 条目数:", len(entries))
    print("前3条:", [(e.get("id"), (e.get("title") or "")[:12]) for e in entries[:3]])
except Exception as e:
    print("yt-dlp 方式2失败:", str(e)[:300])
