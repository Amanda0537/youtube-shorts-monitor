"""
Viewstats Top Shorts 数据采集模块
使用 Playwright 加载页面并拦截 API 响应，获取完整的 Top 100 数据
"""
import json
import time
import re
from playwright.sync_api import sync_playwright


VIEWSTATS_URL_WEEKLY = (
    "https://www.viewstats.com/top-list?filterBy=views&interval=ms_weekly"
    "&madeForKids=true&movies=true&musicChannels=true&tab=videos&videoType=shorts"
)
VIEWSTATS_URL_YESTERDAY = (
    "https://www.viewstats.com/top-list?filterBy=views&interval=ms_yesterday"
    "&madeForKids=true&movies=true&musicChannels=true&tab=videos&videoType=shorts"
)


def scrape_viewstats(interval="weekly", timeout=30000):
    """
    使用 Playwright 抓取 Viewstats 页面，提取视频数据。

    Strategy:
    1. 拦截 api.viewstats.com/rankings/videos 的响应
    2. 如果 API 拦截失败，回退到 DOM 解析
    3. 如果 yesterday 没有数据，自动回退到 weekly

    Returns: list of dict, 每个 dict 包含 video_id, title, channel, views 等
    """
    url = VIEWSTATS_URL_YESTERDAY if interval == "yesterday" else VIEWSTATS_URL_WEEKLY

    api_response_data = []
    dom_videos = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # 拦截 API 响应
        def handle_response(response):
            if "rankings/videos" in response.url and response.status == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        api_response_data.extend(data)
                    elif isinstance(data, dict):
                        for key, val in data.items():
                            if isinstance(val, list):
                                api_response_data.extend(val)
                except Exception:
                    pass

        page.on("response", handle_response)

        try:
            page.goto(url, wait_until="networkidle", timeout=timeout)
            page.wait_for_timeout(5000)
        except Exception as e:
            print(f"[Scraper] Page load warning: {e}")

        if api_response_data:
            print(f"[Scraper] API intercepted: {len(api_response_data)} items")
            videos = parse_api_response(api_response_data)
        else:
            print("[Scraper] API intercept failed, falling back to DOM parsing")
            videos = parse_dom(page)

        if not videos and interval == "yesterday":
            print("[Scraper] Yesterday data empty, falling back to weekly")
            page.goto(VIEWSTATS_URL_WEEKLY, wait_until="networkidle", timeout=timeout)
            page.wait_for_timeout(5000)
            if api_response_data:
                videos = parse_api_response(api_response_data)
            else:
                videos = parse_dom(page)

        browser.close()

    print(f"[Scraper] Total videos scraped: {len(videos)}")
    return videos


def parse_api_response(data):
    videos = []
    for i, item in enumerate(data):
        if isinstance(item, dict):
            video = {
                "rank": i + 1,
                "video_id": item.get("videoId", item.get("id", "")),
                "title": item.get("title", item.get("videoTitle", "")),
                "channel_name": item.get("channelTitle", item.get("channelName", "")),
                "channel_id": item.get("channelId", ""),
                "channel_handle": item.get("channelHandle", item.get("handle", "")),
                "views": item.get("viewCount", item.get("views", 0)),
                "upload_date": item.get("publishedAt", item.get("uploadDate", "")),
                "thumbnail": item.get("thumbnail", ""),
                "duration": item.get("duration", 0),
            }
            if not video["video_id"] and "url" in item:
                match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', item["url"])
                if match:
                    video["video_id"] = match.group(1)
            if video["video_id"]:
                if not video["thumbnail"]:
                    video["thumbnail"] = f"https://i.ytimg.com/vi/{video['video_id']}/hqdefault.jpg"
                videos.append(video)
    return videos


def parse_dom(page):
    videos = []
    try:
        links = page.query_selector_all('a[href*="/videos/"]')
        for i, link in enumerate(links):
            href = link.get_attribute("href") or ""
            parts = href.split("/")
            channel_handle = ""
            video_id = ""
            for j, part in enumerate(parts):
                if part.startswith("@"):
                    channel_handle = part.replace("@", "")
                if part == "videos" and j + 1 < len(parts):
                    video_id = parts[j + 1]
            if not video_id:
                continue
            row = link.evaluate("el => { let p = el; for(let i=0;i<10;i++){p=p.parentElement;if(!p)break;if(p.textContent.length>20)return p.textContent.trim().substring(0,500);}return '';}")
            views = 0
            view_match = re.search(r'([\\d,]+(?:,\\d{3})+)', str(row))
            if view_match:
                views = int(view_match.group(1).replace(",", ""))
            video = {
                "rank": i + 1,
                "video_id": video_id,
                "title": "",
                "channel_name": "",
                "channel_id": "",
                "channel_handle": channel_handle,
                "views": views,
                "upload_date": "",
                "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                "duration": 0,
            }
            videos.append(video)
    except Exception as e:
        print(f"[Scraper] DOM parsing error: {e}")
    return videos


if __name__ == "__main__":
    videos = scrape_viewstats("weekly")
    for v in videos[:5]:
        print(f"#{v['rank']} | {v['video_id']} | {v['channel_handle']} | {v['views']:,}")
