"""Bark 推送 - 沿用项目统一规范"""
import os
import requests
from urllib.parse import quote
from datetime import datetime

BARK_KEY = os.environ["BARK_KEY"]  # 从 GitHub Secrets 注入，不设硬编码 fallback
ICON_URL = "https://www.qtxh.top/resources/icons/3.png"
PROJECT_NAME = "264tiexuejk"


def send_bark(title: str, content: str, sound: str = "minuet",
              level: str = "timeSensitive", group: str = "铁血监控"):
    """发送 Bark 通知"""
    time_str = datetime.now().strftime('%H:%M:%S')
    full_title = f"{PROJECT_NAME}_{title} {time_str}"

    url = f'https://api.day.app/{BARK_KEY}/{quote(full_title)}/{quote(content)}'
    try:
        r = requests.get(url, params={
            'sound': sound,
            'icon': ICON_URL,
            'badge': '1',
            'level': level,
            'group': group,
        }, timeout=10)
        print(f"Bark 推送 [{r.status_code}]: {full_title}")
    except Exception as e:
        print(f"Bark 推送失败: {e}")
