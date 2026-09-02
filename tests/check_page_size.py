# -*- coding: utf-8 -*-
"""对比不同 page_size 的 seasons_archives_list 返回。"""
import json
import urllib.request

ua = {"User-Agent": "Mozilla/5.0"}
for ps in (10, 30, 50):
    url = (f"https://api.bilibili.com/x/polymer/web-space/seasons_archives_list"
           f"?mid=672035&season_id=8042010&page_num=1&page_size={ps}")
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=ua), timeout=15))
        data = d.get("data") or {}
        arcs = data.get("archives") or []
        print(f"page_size={ps}: code={d.get('code')} msg={d.get('message')} "
              f"total={data.get('total')} has_more={data.get('has_more')} archives={len(arcs)}")
        if arcs:
            print("   首条:", arcs[0].get("bvid"), arcs[0].get("title", "")[:15])
    except Exception as e:
        print(f"page_size={ps}: 异常 {e}")
