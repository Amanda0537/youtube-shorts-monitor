"""
飞书群 Webhook 推送模块
发送每日爆款 Shorts 日报摘要到飞书群
"""
import os
import json
import requests
from datetime import datetime


def send_daily_report(videos, report_url, webhook_url=None):
    """
    发送每日汇总到飞书群

    Args:
        videos: list of dict, 已分类的视频列表
        report_url: str, HTML 报告的公开 URL
        webhook_url: str, 飞书 Webhook 地址
    """
    url = webhook_url or os.environ.get("FEISHU_WEBHOOK_URL", "")
    if not url:
        print("[Feishu] No webhook URL configured, skipping")
        return False

    today = datetime.now().strftime("%Y-%m-%d")
    total = len(videos)

    # 找到推荐视频
    recommended = [v for v in videos if v.get("is_recommended")]
    recommended.sort(key=lambda x: x.get("virality_ratio", 0), reverse=True)
    top_recommended = recommended[:5]

    # 统计赛道分布
    niche_counts = {}
    for v in videos:
        n = v.get("niche_name", "其他")
        niche_counts[n] = niche_counts.get(n, 0) + 1
    top_niches = sorted(niche_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # 构建推荐视频卡片内容
    rec_text = ""
    for i, v in enumerate(top_recommended, 1):
        title = (v.get("title") or "")[:40]
        channel = v.get("channel_name", "")[:15]
        views_m = v.get("views", 0) / 1000000
        subs = v.get("subscribers", 0)
        subs_str = f"{subs//1000}K" if subs < 1000000 else f"{subs//1000000}M"
        virality = v.get("virality_ratio", 0)
        ai_score = v.get("ai_score", 0)
        vid = v.get("video_id", "")
        reasons = v.get("recommend_reasons", [])
        reason_str = "；".join(reasons[:2]) if reasons else ""

        rec_text += (
            f"\n**{i}. {title}**\n"
            f"  频道: {channel} ({subs_str}粉) | 播放: {views_m:.1f}M | "
            f"爆款系数: {virality}x | AI适配: {ai_score}分\n"
            f"  推荐理由: {reason_str}\n"
            f"  [观看视频](https://youtube.com/shorts/{vid})\n"
        )

    if not rec_text:
        rec_text = "\n今日暂无符合条件的推荐视频\n"

    # 赛道分布文本
    niche_text = " | ".join([f"{n}: {c}个" for n, c in top_niches])

    # 构建飞书消息 (使用 interactive 卡片格式)
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"📊 YouTube Shorts 爆款日报 | {today}"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": (
                            f"**今日监控概况**\n"
                            f"共 **{total}** 个 Shorts 上榜 | "
                            f"推荐关注 **{len(recommended)}** 个\n"
                            f"热门赛道: {niche_text}"
                        )
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**🔥 今日重点推荐 Top {len(top_recommended)}**{rec_text}"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "📋 查看完整报告"
                            },
                            "url": report_url,
                            "type": "primary"
                        }
                    ]
                }
            ]
        }
    }

    # 发送请求
    try:
        resp = requests.post(url, json=card, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                print(f"[Feishu] Message sent successfully")
                return True
            else:
                print(f"[Feishu] API error: {result}")
                return False
        else:
            print(f"[Feishu] HTTP error: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        print(f"[Feishu] Send error: {e}")
        return False


if __name__ == "__main__":
    # 测试
    test_videos = [
        {
            "title": "Test Video",
            "channel_name": "TestChannel",
            "views": 50000000,
            "subscribers": 1000,
            "virality_ratio": 50000,
            "ai_score": 90,
            "video_id": "test123",
            "is_recommended": True,
            "recommend_reasons": ["小频道爆款", "AI动画适配度高"],
            "niche_name": "猜谜/互动",
        }
    ]
    send_daily_report(test_videos, "https://example.com/report.html")
