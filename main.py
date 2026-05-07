"""铁血科技日常扫描 - GitHub Actions 入口"""
import sys
import traceback
from datetime import datetime

import monitor
import state
from notify import send_bark


def format_summary(new_items: list) -> tuple[str, str]:
    """生成推送的标题和正文"""
    if not new_items:
        return "今日无新增", "四个数据源均无新内容"

    # 按来源排优先级
    priority = {"BJOTC": 0, "东方财富": 1, "雪球": 2, "百度新闻": 3}
    new_items.sort(key=lambda x: priority.get(x["source"], 9))

    title = f"新增{len(new_items)}条"
    lines = [f"[{it['source']}] {it['title'][:50]}" for it in new_items[:10]]
    body = "\n".join(lines)
    if len(new_items) > 10:
        body += f"\n…还有{len(new_items)-10}条"
    return title, body


def main():
    print(f"\n{'='*60}\n[scan] 启动 {datetime.now()}\n{'='*60}")

    try:
        # 抓数据
        all_items = monitor.fetch_all()
        print(f"[scan] 总抓取 {len(all_items)} 条")

        # 过滤相关性
        relevant = [x for x in all_items if monitor.is_relevant(x["title"])]
        print(f"[scan] 相关 {len(relevant)} 条")

        # 与历史比对去重
        seen = state.load_seen()
        new_items = []
        for item in relevant:
            h = state.item_hash(item)
            if h not in seen:
                seen.add(h)
                new_items.append(item)

        print(f"[scan] 新增 {len(new_items)} 条")

        # 只在有新增时推送
        if new_items:
            title, body = format_summary(new_items)
            send_bark(title, body)
        else:
            print("[scan] 无新增，跳过推送")

        # 保存状态
        state.save_seen(seen)

        print(f"[scan] 完成 -> {title}")

    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        print(f"[scan] 失败: {err}")
        traceback.print_exc()
        send_bark("扫描失败", err[:200], level="active")
        sys.exit(1)   # 失败让 Actions 标红


if __name__ == "__main__":
    main()
