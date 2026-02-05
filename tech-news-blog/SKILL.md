---
name: tech-news-blog
description: Generate daily tech news roundup and publish to Hexo blog. Automatically fetches Hacker News, translates to Chinese with AI, adds images, and deploys. Just say "生成今日科技新闻" or "generate tech news".
compatibility: Requires Python 3.8+, Node.js with Hexo CLI, and r2-upload skill.
metadata:
  author: foundra
  version: "3.0"
---

# Tech News Blog

自动生成科技新闻汇总并发布到 Hexo 博客。

## When to use

用户说"生成今日科技新闻"、"科技新闻"、"tech news"、"发布博客"等 → 直接运行脚本

## Usage

**最简单（推荐）：**
```bash
./run.sh
# 或指定日期
./run.sh 2026-02-05
```

**手动方式：**
```bash
cd scripts
python3 generate.py --date 2026-02-05 --source hackernews --with-images --deploy
```

## What it does

1. ✅ 获取 Hacker News 热门新闻
2. ✅ AI 翻译成中文 + 生成摘要
3. ✅ 抓取文章配图并上传到 R2
4. ✅ 自动部署到博客

## Options

| Option | Description |
|--------|-------------|
| `./run.sh` | 今天，自动配图+部署 |
| `./run.sh 2026-02-05` | 指定日期 |
| `./run.sh --no-deploy` | 不部署 |
| `./run.sh --no-images` | 不处理图片 |

## Troubleshooting

| 问题 | 解决 |
|-----|------|
| 翻译失败 | 检查 ANTHROPIC_API_KEY |
| 图片上传失败 | 检查 r2-upload skill |
| 部署失败 | 手动运行 `hexo d` |
