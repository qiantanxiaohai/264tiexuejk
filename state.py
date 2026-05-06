"""扫描状态 - 用 JSON 文件存储,GitHub 自动持久化"""
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Set, Dict

STATE_FILE = Path("data/state.json")
MAX_KEEP = 2000   # 防止 state.json 无限膨胀


def item_hash(item: Dict) -> str:
    """生成条目唯一标识"""
    key = item.get("url") or item["title"]
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def load_seen() -> Set[str]:
    """加载历史已读集合"""
    if not STATE_FILE.exists():
        return set()
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return set(data.get("seen", []))
    except Exception as e:
        print(f"读取 state 失败: {e}")
        return set()


def save_seen(seen: Set[str]):
    """保存到 state.json,只保留最近 MAX_KEEP 条防膨胀"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "last_run": datetime.utcnow().isoformat() + "Z",
        "seen": list(seen)[-MAX_KEEP:],
    }
    STATE_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
