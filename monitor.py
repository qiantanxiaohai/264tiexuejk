"""数据源抓取"""
import json
import re
import time
from collections import defaultdict
from typing import List, Dict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"}
KEYWORDS = ["铁血科技", "铁血"]
BLACKLIST = ["铁血战士", "铁血丹心", "铁血将军", "铁血宰相", "铁血真汉子"]


# ===== 域名限速器 =====
class RateLimiter:
    INTERVALS = {'baidu': 5, 'eastmoney': 5, 'xueqiu': 5, 'bjotc': 3}

    def __init__(self):
        self.last = defaultdict(float)

    def wait(self, url: str):
        host = urlparse(url).hostname or ""
        for key, interval in self.INTERVALS.items():
            if key in host:
                elapsed = time.time() - self.last[key]
                if elapsed < interval:
                    time.sleep(interval - elapsed)
                self.last[key] = time.time()
                return


limiter = RateLimiter()


def _get(url: str, **kwargs) -> requests.Response:
    limiter.wait(url)
    return requests.get(url, headers=HEADERS, timeout=20, **kwargs)


# ===== 4 个数据源 =====
def fetch_bjotc() -> List[Dict]:
    items = []
    try:
        r = _get("https://www.bjotc.cn/information/notice.html")
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, "lxml")
        for a in soup.select("a[href*='/content/details']"):
            title = a.get_text(strip=True)
            if any(k in title for k in KEYWORDS):
                href = a["href"]
                if not href.startswith("http"):
                    href = "https://www.bjotc.cn" + href
                items.append({"source": "BJOTC", "title": title, "url": href})
    except Exception as e:
        print(f"[BJOTC] {e}")
    return items


def fetch_xueqiu() -> List[Dict]:
    items = []
    try:
        r = _get("https://xueqiu.com/query/v1/search/status.json?count=20&q=铁血科技")
        for x in r.json().get("list", []):
            title = re.sub(r"<[^>]+>", "",
                           x.get("title") or x.get("description", "")[:80])
            target = x.get("target", "")
            url = ("https://xueqiu.com" + target) if target else ""
            if title:
                items.append({"source": "雪球", "title": title, "url": url})
    except Exception as e:
        print(f"[雪球] {e}")
    return items


def fetch_baidu_news() -> List[Dict]:
    items = []
    try:
        r = _get("https://www.baidu.com/s?tn=news&word=铁血科技")
        soup = BeautifulSoup(r.text, "lxml")
        for el in soup.select("div.result, div.result-op")[:20]:
            a = el.select_one("h3 a")
            if a and a.get_text(strip=True):
                items.append({"source": "百度新闻",
                              "title": a.get_text(strip=True),
                              "url": a.get("href", "")})
    except Exception as e:
        print(f"[百度] {e}")
    return items


def fetch_eastmoney() -> List[Dict]:
    items = []
    try:
        url = "https://search-api-web.eastmoney.com/search/jsonp"
        params = {"param": '{"uid":"","keyword":"铁血科技",'
                           '"type":["cmsArticleWebOld"],'
                           '"pageIndex":1,"pageSize":20}'}
        r = _get(url, params=params)
        m = re.search(r"\((.*)\)", r.text)
        if m:
            data = (json.loads(m.group(1))
                    .get("result", {}).get("cmsArticleWebOld", []))
            for x in data:
                if x.get("title"):
                    items.append({"source": "东方财富",
                                  "title": x["title"],
                                  "url": x.get("url", "")})
    except Exception as e:
        print(f"[东方财富] {e}")
    return items


def fetch_all() -> List[Dict]:
    return (fetch_bjotc() + fetch_xueqiu() +
            fetch_baidu_news() + fetch_eastmoney())


def is_relevant(title: str) -> bool:
    """简单相关性过滤"""
    if not any(k in title for k in KEYWORDS):
        return False
    if any(b in title for b in BLACKLIST):
        return False
    return True
