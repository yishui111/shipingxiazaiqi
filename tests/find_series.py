# -*- coding: utf-8 -*-
"""临时脚本：从B站热门榜找带合集(ugc_season)的视频。"""
import json
import time
import urllib.request

UA = {"User-Agent": "Mozilla/5.0"}


def get(url):
    return json.load(urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=15))


popular = get("https://api.bilibili.com/x/web-interface/popular?pn=1&ps=50")
vids = popular.get("data", {}).get("list", [])
found = []
for v in vids[:30]:
    try:
        dd = get(f"https://api.bilibili.com/x/web-interface/view?bvid={v['bvid']}")
        s = (dd.get("data") or {}).get("ugc_season")
        if s:
            eps = s.get("episodes") or []
            found.append({
                "bvid": v["bvid"],
                "title": (dd.get("data") or {}).get("title", "")[:25],
                "season": s.get("title"),
                "season_id": s.get("id"),
                "count": s.get("ep_count"),
                "sample": [(e.get("bvid"), (e.get("title") or "")[:12]) for e in eps[:3]],
            })
    except Exception:
        pass
    time.sleep(0.3)

print("找到带合集视频数:", len(found))
for f in found[:3]:
    print(json.dumps(f, ensure_ascii=False, indent=1))
