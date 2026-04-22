# YouTube Shorts 爆款监控系统

每日自动监控 YouTube Top 100 Shorts，分析爆款模式，生成可视化报告，推送到飞书群。

## 快速部署（3步完成）

### 第一步：创建 GitHub 仓库

1. 打开 https://github.com/new
2. 仓库名输入: `youtube-shorts-monitor`
3. 选择 **Public**（GitHub Pages 需要公开仓库，免费版）
4. 点击 **Create repository**
5. 把本项目的所有文件推送到这个仓库

```bash
cd youtube-shorts-monitor
git init
git add -A
git commit -m "init: YouTube Shorts monitoring system"
git branch -M main
git remote add origin https://github.com/Amanda0537/youtube-shorts-monitor.git
git push -u origin main
```

### 第二步：配置 Secrets

打开仓库 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

添加以下两个 Secret：

| Name | Value |
|------|-------|
| `YOUTUBE_API_KEY` | 你的 YouTube Data API v3 Key |
| `FEISHU_WEBHOOK_URL` | 飞书群 Webhook 地址 |

### 第三步：启用 GitHub Pages

1. 打开仓库 → **Settings** → **Pages**
2. Source 选择: **Deploy from a branch**
3. Branch 选择: **gh-pages** → **/ (root)**
4. 点击 **Save**

### 首次运行

1. 打开仓库 → **Actions** → **Daily YouTube Shorts Monitor**
2. 点击 **Run workflow** → **Run workflow**
3. 等待几分钟完成
4. 访问 https://Amanda0537.github.io/youtube-shorts-monitor/ 查看报告

之后每天北京时间上午 9 点自动运行。

## 功能说明

- **数据采集**: 从 Viewstats 获取 Top 100 Shorts 排名
- **数据补充**: 通过 YouTube API 获取频道粉丝数、视频详情
- **自动分类**: 赛道、钩子类型、人设角色、语言、制作方式
- **AI适配度**: 自动评估每个视频对 AI/动画内容的参考价值
- **重点推荐**: 自动标记小频道大爆款+高AI适配的视频
- **可视化报告**: 带封面图、可播放、可筛选的 HTML 报告
- **飞书推送**: 每日摘要自动发送到飞书群
