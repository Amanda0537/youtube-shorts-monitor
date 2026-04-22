"""
HTML 报告生成器
生成精美的每日爆款 Shorts 分析报告
"""
import os
from datetime import datetime


def generate_report(videos, output_dir="reports"):
    """
    生成 HTML 报告

    Args:
        videos: list of dict, 已分类和补充数据的视频列表
        output_dir: str, 输出目录

    Returns:
        str, 生成的 HTML 文件路径
    """
    os.makedirs(output_dir, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = os.path.join(output_dir, f"report-{today}.html")
    index_path = os.path.join(output_dir, "index.html")

    # 统计数据
    total = len(videos)
    recommended = [v for v in videos if v.get("is_recommended")]
    avg_views = sum(v.get("views", 0) for v in videos) // max(total, 1)

    # 赛道分布
    niche_dist = {}
    for v in videos:
        n = v.get("niche_name", "其他")
        niche_dist[n] = niche_dist.get(n, 0) + 1
    niche_sorted = sorted(niche_dist.items(), key=lambda x: x[1], reverse=True)

    # 语言分布
    lang_dist = {}
    for v in videos:
        l = v.get("language", "N/A")
        lang_dist[l] = lang_dist.get(l, 0) + 1

    # 钩子分布
    hook_dist = {}
    for v in videos:
        h = v.get("title_hook_name", "无")
        hook_dist[h] = hook_dist.get(h, 0) + 1
    hook_sorted = sorted(hook_dist.items(), key=lambda x: x[1], reverse=True)

    # 生成视频卡片 HTML
    cards_html = ""
    for v in videos:
        cards_html += build_video_card(v)

    # 生成赛道统计
    niche_bars = ""
    max_count = max((c for _, c in niche_sorted), default=1)
    for name, count in niche_sorted[:10]:
        pct = count / max_count * 100
        niche_bars += f'<div class="stat-bar"><span class="stat-label">{name}</span><div class="bar-bg"><div class="bar-fill" style="width:{pct}%"></div></div><span class="stat-count">{count}</span></div>\n'

    # 生成钩子统计
    hook_bars = ""
    max_hook = max((c for _, c in hook_sorted), default=1)
    for name, count in hook_sorted[:8]:
        pct = count / max_hook * 100
        hook_bars += f'<div class="stat-bar"><span class="stat-label">{name}</span><div class="bar-bg"><div class="bar-fill hook-fill" style="width:{pct}%"></div></div><span class="stat-count">{count}</span></div>\n'

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YouTube Shorts 爆款日报 | {today}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0f0f0f; color: #e8e8e8; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
.header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 30px 20px; text-align: center; }}
.header h1 {{ font-size: 28px; color: #fff; margin-bottom: 8px; }}
.header .date {{ color: #8b95a5; font-size: 16px; }}
.summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; padding: 20px; max-width: 1400px; margin: 0 auto; }}
.summary-card {{ background: #1a1a1a; border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #2a2a2a; }}
.summary-card .num {{ font-size: 32px; font-weight: 700; color: #ff4444; }}
.summary-card .label {{ color: #888; font-size: 14px; margin-top: 5px; }}
.section {{ max-width: 1400px; margin: 20px auto; padding: 0 20px; }}
.section-title {{ font-size: 20px; font-weight: 600; margin-bottom: 15px; display: flex; align-items: center; gap: 8px; }}
.stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
.stats-box {{ background: #1a1a1a; border-radius: 12px; padding: 20px; border: 1px solid #2a2a2a; }}
.stat-bar {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
.stat-label {{ min-width: 100px; font-size: 13px; color: #aaa; text-align: right; }}
.bar-bg {{ flex: 1; background: #2a2a2a; border-radius: 4px; height: 20px; overflow: hidden; }}
.bar-fill {{ height: 100%; background: linear-gradient(90deg, #ff4444, #ff6b6b); border-radius: 4px; transition: width 0.5s; }}
.hook-fill {{ background: linear-gradient(90deg, #4ecdc4, #44bd9e) !important; }}
.stat-count {{ min-width: 30px; font-size: 13px; color: #fff; font-weight: 600; }}
.filters {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }}
.filter-btn {{ background: #2a2a2a; border: 1px solid #3a3a3a; color: #ccc; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 13px; transition: all 0.2s; }}
.filter-btn:hover, .filter-btn.active {{ background: #ff4444; color: #fff; border-color: #ff4444; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 20px; }}
.card {{ background: #1a1a1a; border-radius: 12px; overflow: hidden; border: 1px solid #2a2a2a; transition: transform 0.2s, box-shadow 0.2s; }}
.card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 25px rgba(0,0,0,0.5); }}
.card.recommended {{ border: 2px solid #ff4444; position: relative; }}
.card.recommended::before {{ content: "⭐ 重点推荐"; position: absolute; top: 10px; left: 10px; background: #ff4444; color: #fff; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; z-index: 10; }}
.thumb-wrap {{ position: relative; cursor: pointer; }}
.thumb-wrap img {{ width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; }}
.play-btn {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 60px; height: 60px; background: rgba(0,0,0,0.7); border-radius: 50%; display: flex; align-items: center; justify-content: center; transition: background 0.2s; }}
.play-btn::after {{ content: ""; border-left: 20px solid #fff; border-top: 12px solid transparent; border-bottom: 12px solid transparent; margin-left: 4px; }}
.thumb-wrap:hover .play-btn {{ background: rgba(255,68,68,0.9); }}
.rank-badge {{ position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.8); color: #fff; padding: 4px 10px; border-radius: 4px; font-weight: 700; font-size: 14px; }}
.card-body {{ padding: 15px; }}
.card-title {{ font-size: 14px; font-weight: 600; line-height: 1.4; margin-bottom: 8px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
.card-title a {{ color: #e8e8e8; text-decoration: none; }}
.card-title a:hover {{ color: #ff4444; }}
.channel {{ display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }}
.channel img {{ width: 24px; height: 24px; border-radius: 50%; }}
.channel-name {{ color: #888; font-size: 13px; }}
.metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-bottom: 10px; }}
.metric {{ font-size: 12px; color: #888; }}
.metric .val {{ color: #fff; font-weight: 600; }}
.metric.hot .val {{ color: #ff4444; }}
.tags {{ display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }}
.tag {{ font-size: 11px; padding: 3px 8px; border-radius: 10px; }}
.tag-niche {{ background: #1e3a5f; color: #5dade2; }}
.tag-hook {{ background: #1a3d2e; color: #4ecdc4; }}
.tag-char {{ background: #3d1a3d; color: #c39bd3; }}
.tag-lang {{ background: #3d3d1a; color: #f0e68c; }}
.tag-prod {{ background: #3d2a1a; color: #e8a87c; }}
.tag-ai {{ background: #2d1a1a; color: #ff6b6b; }}
.reasons {{ font-size: 11px; color: #ff6b6b; line-height: 1.5; padding: 8px; background: rgba(255,68,68,0.1); border-radius: 6px; margin-top: 8px; }}
.links {{ display: flex; gap: 8px; margin-top: 10px; }}
.link-btn {{ font-size: 12px; color: #5dade2; text-decoration: none; padding: 4px 10px; border: 1px solid #5dade2; border-radius: 4px; transition: all 0.2s; }}
.link-btn:hover {{ background: #5dade2; color: #000; }}
.footer {{ text-align: center; padding: 30px; color: #555; font-size: 13px; margin-top: 30px; }}
@media (max-width: 768px) {{
  .grid {{ grid-template-columns: 1fr; }}
  .stats-grid {{ grid-template-columns: 1fr; }}
  .summary {{ grid-template-columns: repeat(2, 1fr); }}
}}
</style>
</head>
<body>
<div class="header">
  <h1>📊 YouTube Shorts 爆款日报</h1>
  <div class="date">{today} | Top {total} Shorts 分析</div>
</div>

<div class="summary">
  <div class="summary-card"><div class="num">{total}</div><div class="label">上榜视频</div></div>
  <div class="summary-card"><div class="num">{len(recommended)}</div><div class="label">重点推荐</div></div>
  <div class="summary-card"><div class="num">{avg_views//1000000}M</div><div class="label">平均播放量</div></div>
  <div class="summary-card"><div class="num">{len(niche_dist)}</div><div class="label">涉及赛道</div></div>
</div>

<div class="section">
  <div class="section-title">📈 数据分布</div>
  <div class="stats-grid">
    <div class="stats-box">
      <h3 style="margin-bottom:12px;font-size:15px;color:#ff6b6b;">赛道分布</h3>
      {niche_bars}
    </div>
    <div class="stats-box">
      <h3 style="margin-bottom:12px;font-size:15px;color:#4ecdc4;">钩子类型分布</h3>
      {hook_bars}
    </div>
  </div>
</div>

<div class="section">
  <div class="section-title">🎬 完整排行榜</div>
  <div class="filters">
    <button class="filter-btn active" onclick="filterCards('all')">全部</button>
    <button class="filter-btn" onclick="filterCards('recommended')">⭐ 仅推荐</button>
    <button class="filter-btn" onclick="filterCards('high-ai')">🤖 AI适配≥80</button>
    <button class="filter-btn" onclick="filterCards('en')">🌍 英文/全球</button>
    <button class="filter-btn" onclick="filterCards('small')">🚀 小频道爆款</button>
  </div>
  <div class="grid" id="videoGrid">
    {cards_html}
  </div>
</div>

<div class="footer">
  Generated by YouTube Shorts Monitor | {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}
</div>

<script>
function filterCards(type) {{
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  document.querySelectorAll('.card').forEach(card => {{
    let show = true;
    if (type === 'recommended') show = card.classList.contains('recommended');
    else if (type === 'high-ai') show = parseInt(card.dataset.aiScore || 0) >= 80;
    else if (type === 'en') show = ['EN','NO-LANG'].includes(card.dataset.lang);
    else if (type === 'small') show = parseInt(card.dataset.subs || 0) < 100000 && parseInt(card.dataset.virality || 0) > 50;
    card.style.display = show ? '' : 'none';
  }});
}}
</script>
</body>
</html>"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    # 同时写 index.html（GitHub Pages 入口）
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[Report] Generated: {filepath}")
    return filepath


def build_video_card(v):
    """构建单个视频卡片 HTML"""
    vid = v.get("video_id", "")
    title = v.get("title", "Unknown")[:80]
    channel = v.get("channel_name", "")[:25]
    rank = v.get("rank", 0)
    views = v.get("views", 0)
    subs = v.get("subscribers", 0)
    virality = v.get("virality_ratio", 0)
    ai_score = v.get("ai_score", 50)
    likes = v.get("likes", 0)
    comments = v.get("comments", 0)
    engagement = v.get("engagement_rate", 0)
    days = v.get("days_since_upload", 0)
    daily_avg = v.get("daily_avg_views", 0)
    thumb = v.get("thumbnail", f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg")
    ch_thumb = v.get("channel_thumbnail", "")
    is_rec = v.get("is_recommended", False)
    reasons = v.get("recommend_reasons", [])
    niche_name = v.get("niche_name", "其他")
    niche = v.get("niche", "OTH")
    hook_name = v.get("title_hook_name", "")
    content_hook = v.get("content_hook_name", "")
    character = v.get("character", "")
    char_source = v.get("character_source", "")
    lang = v.get("language", "")
    production = v.get("production", "")

    # 格式化数字
    def fmt(n):
        if n >= 1000000:
            return f"{n/1000000:.1f}M"
        elif n >= 1000:
            return f"{n/1000:.1f}K"
        return str(n)

    rec_class = " recommended" if is_rec else ""
    yt_url = f"https://youtube.com/shorts/{vid}"

    # 标签
    tags_html = ""
    tags_html += f'<span class="tag tag-niche">{niche_name}</span>\n'
    if hook_name and hook_name != "无明显钩子":
        tags_html += f'<span class="tag tag-hook">钩子:{hook_name}</span>\n'
    if content_hook and content_hook != "无明显钩子" and content_hook != hook_name:
        tags_html += f'<span class="tag tag-hook">内容:{content_hook}</span>\n'
    if character and character != "未识别":
        tags_html += f'<span class="tag tag-char">{character}({char_source})</span>\n'
    if lang:
        tags_html += f'<span class="tag tag-lang">{lang}</span>\n'
    if production and production != "UNKNOWN":
        tags_html += f'<span class="tag tag-prod">{production}</span>\n'
    tags_html += f'<span class="tag tag-ai">AI适配:{ai_score}</span>\n'

    # 推荐理由
    reasons_html = ""
    if reasons:
        reasons_html = f'<div class="reasons">💡 {"；".join(reasons)}</div>'

    # 频道图标
    ch_img = f'<img src="{ch_thumb}" alt="">' if ch_thumb else '<div style="width:24px;height:24px;background:#333;border-radius:50%;"></div>'

    return f"""
<div class="card{rec_class}" data-niche="{niche}" data-lang="{lang}" data-ai-score="{ai_score}" data-subs="{subs}" data-virality="{virality}">
  <div class="thumb-wrap" onclick="window.open('{yt_url}','_blank')">
    <img src="{thumb}" alt="{title}" loading="lazy" onerror="this.src='https://i.ytimg.com/vi/{vid}/hqdefault.jpg'">
    <div class="play-btn"></div>
    <div class="rank-badge">#{rank}</div>
  </div>
  <div class="card-body">
    <div class="card-title"><a href="{yt_url}" target="_blank">{title}</a></div>
    <div class="channel">{ch_img}<span class="channel-name">{channel}</span></div>
    <div class="metrics">
      <div class="metric"><span class="val">{fmt(views)}</span> 播放</div>
      <div class="metric"><span class="val">{fmt(subs)}</span> 粉丝</div>
      <div class="metric hot"><span class="val">{virality}x</span> 爆款系数</div>
      <div class="metric"><span class="val">{engagement}%</span> 互动率</div>
      <div class="metric"><span class="val">{fmt(likes)}</span> 点赞</div>
      <div class="metric"><span class="val">{days}天</span> 已上传</div>
    </div>
    <div class="tags">{tags_html}</div>
    {reasons_html}
    <div class="links">
      <a class="link-btn" href="{yt_url}" target="_blank">▶ YouTube</a>
      <a class="link-btn" href="https://www.viewstats.com/@{v.get('channel_handle','')}/videos/{vid}" target="_blank">📊 Viewstats</a>
    </div>
  </div>
</div>
"""


if __name__ == "__main__":
    test_videos = [
        {
            "rank": 1, "video_id": "HBLxRb_4oDs", "title": "Test Video #1",
            "channel_name": "TestCh", "views": 100000000, "subscribers": 5000,
            "virality_ratio": 20000, "ai_score": 92, "is_recommended": True,
            "recommend_reasons": ["小频道爆款", "AI适配度高"],
            "niche": "QIZ", "niche_name": "猜谜/互动",
            "title_hook_name": "猜谜互动", "content_hook_name": "提问式",
            "character": "猫咪人设", "character_source": "动物",
            "language": "EN", "production": "ANIM",
            "likes": 500000, "comments": 20000, "engagement_rate": 0.52,
            "days_since_upload": 5, "daily_avg_views": 20000000,
        },
    ]
    generate_report(test_videos)
