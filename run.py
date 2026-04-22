#!/usr/bin/env python3
"""
YouTube Shorts 爆款监控系统 - 主入口
每日自动运行：采集 → 补充 → 分类 → 生成报告 → 推送飞书
"""
import os
import sys
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from src.scraper import scrape_viewstats
from src.youtube_api import enrich_videos
from src.classifier import classify_all
from src.report_generator import generate_report
from src.feishu_notifier import send_daily_report


def main():
    print("=" * 60)
    print(f"YouTube Shorts Monitor | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # ---- 配置 ----
    youtube_api_key = os.environ.get("YOUTUBE_API_KEY", "")
    feishu_webhook = os.environ.get("FEISHU_WEBHOOK_URL", "")
    github_user = os.environ.get("GITHUB_USER", "Amanda0537")
    github_repo = os.environ.get("GITHUB_REPO", "youtube-shorts-monitor")
    report_base_url = f"https://{github_user}.github.io/{github_repo}"

    if not youtube_api_key:
        print("[ERROR] YOUTUBE_API_KEY not set!")
        sys.exit(1)

    # ---- Step 1: 采集数据 ----
    print("\n[Step 1] Scraping Viewstats...")
    videos = scrape_viewstats("weekly")

    if not videos:
        print("[WARN] No videos scraped, trying yesterday...")
        videos = scrape_viewstats("yesterday")

    if not videos:
        print("[ERROR] No data available, exiting")
        sys.exit(1)

    print(f"  Scraped {len(videos)} videos")

    # ---- Step 2: YouTube API 补充数据 ----
    print("\n[Step 2] Enriching with YouTube API...")
    videos = enrich_videos(videos, api_key=youtube_api_key)
    print(f"  Enriched {len(videos)} videos with channel/video details")

    # ---- Step 3: 自动分类 ----
    print("\n[Step 3] Auto-classifying...")
    videos = classify_all(videos)

    # 统计分类结果
    niches = {}
    recommended = 0
    for v in videos:
        n = v.get("niche_name", "其他")
        niches[n] = niches.get(n, 0) + 1
        if v.get("is_recommended"):
            recommended += 1

    print(f"  Classified into {len(niches)} niches")
    print(f"  Recommended videos: {recommended}")

    # ---- Step 4: 生成 HTML 报告 ----
    print("\n[Step 4] Generating HTML report...")
    report_path = generate_report(videos, output_dir="reports")
    print(f"  Report saved: {report_path}")

    # 保存原始数据 JSON（供后续分析）
    today = datetime.now().strftime("%Y-%m-%d")
    data_path = os.path.join("reports", f"data-{today}.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=2, default=str)
    print(f"  Data saved: {data_path}")

    # ---- Step 5: 推送飞书 ----
    report_url = f"{report_base_url}/report-{today}.html"
    print(f"\n[Step 5] Sending to Feishu...")
    print(f"  Report URL: {report_url}")

    if feishu_webhook:
        success = send_daily_report(videos, report_url, feishu_webhook)
        if success:
            print("  Feishu notification sent!")
        else:
            print("  Feishu notification failed (will continue)")
    else:
        print("  No Feishu webhook configured, skipping")

    # ---- 完成 ----
    print("\n" + "=" * 60)
    print(f"Done! {len(videos)} videos analyzed, {recommended} recommended")
    print(f"Report: {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
