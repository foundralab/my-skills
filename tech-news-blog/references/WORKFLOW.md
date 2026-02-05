# Tech News Blog Workflow

Complete workflow for generating tech news blog posts.

## Daily Workflow

### 1. Generate Today's Post

```bash
cd ~/.clawdbot/skills/tech-news-blog

# Basic generation
python3 scripts/generate.py --date $(date +%F)

# With images
python3 scripts/generate.py --date $(date +%F) --with-images

# Custom count and deploy
python3 scripts/generate.py --date $(date +%F) --count 20 --with-images --deploy
```

### 2. Manual Review

```bash
# Open generated file
cat ~/projects/blog/source/_posts/$(date +%F)-科技圈新闻汇总.md

# Edit if needed
vim ~/projects/blog/source/_%F)-科技圈新闻汇总.md
```

### 3. Deploy

```bash
cd ~/projects/blog
hexo clean && hexo g && hexo d
```

## Custom Workflows

### Fetch Specific Articles

```bash
# Get top 30 articles from HN
python3 scripts/fetch_news.py --count 30

# Save to file
python3 scripts/fetch_news.py --count 30 --output /tmp/articles.json
```

### Translate Titles

```bash
# Single title
python3 scripts/translate.py "Show HN: My New Project"
# Output: Show HN：My New Project

# Batch translate
cat titles.txt | python3 scripts/translate.py
```

### Process Images Only

```bash
# Add images to existing post
python3 scripts/process_images.py --post ~/projects/blog/source/_posts/2026-02-04-科技圈新闻汇总.md
```

## Category Assignment

Articles are automatically categorized based on keywords:

| Category | Keywords |
|----------|----------|
| AI 与机器学习 | ai, llm, model, agent, gpt, claude, ml, neural |
| 游戏与怀旧科技 | game, retro, vintage, emulator, amiga |
| 开发工具与开源 | rust, python, github, open source, framework |
| 基础设施与行业 | cloud, aws, server, security, devops |
| 趣闻 | (fallback) |

### Override Category

Edit the generated markdown to move articles between sections.

## Image Handling

### Automatic (Recommended)

```bash
python3 scripts/generate.py --date 2026-02-04 --with-images
```

This will:
1. Generate post with image placeholders
2. Fetch og:image from each article
3. Upload to R2 at `images/YYYY/MM/dd/article-XX.jpg`
4. Insert `<img>` tags into markdown

### Manual

```bash
# 1. Generate without images
python3 scripts/generate.py --date 2026-02-04

# 2. Download images manually
curl -o /tmp/image.jpg "https://example.com/og-image.jpg"

# 3. Upload via r2-upload
python3 ~/.clawdbot/skills/r2-upload/scripts/r2-upload.py \
  /tmp/image.jpg \
  --key images/2026/02/04/manual.jpg \
  --public

# 4. Insert into markdown
# Edit file to add: <img src="https://.../manual.jpg">
```

## Deduplication

By default, articles from the last 3 days are excluded to avoid repetition.

To disable:

```bash
python3 scripts/generate.py --date $(date +%F) --no-dedupe
```

## Integration with Other Skills

### Using r2-upload

```python
import sys
sys.path.insert(0, '/root/.clawdbot/skills/r2-upload/scripts')
from upload import upload_file, fetch_and_upload

# Upload local file
url = upload_file('/tmp/image.jpg', key='images/test.jpg', make_public=True)

# Fetch and upload
url = fetch_and_upload('https://example.com/image.jpg', key='images/test.jpg')
```

### Using tech-news-blog from other skills

```python
import sys
sys.path.insert(0, '/root/.clawdbot/skills/tech-news-blog/scripts')
from generate import create_blog_post
from fetch_news import fetch_hackernews, categorize_article
from translate import translate_title
```

## Cron/Automated Usage

```bash
#!/bin/bash
# /etc/cron.daily/tech-news-blog

cd ~/.clawdbot/skills/tech-news-blog

# Generate and deploy
python3 scripts/generate.py \
  --date $(date +%F) \
  --count 15 \
  --with-images \
  --deploy \
  >> /var/log/tech-news-blog.log 2>&1
```

## Troubleshooting

### No articles fetched

- Check HN RSS: `curl https://hnrss.org/frontpage`
- Verify network connectivity

### Images not uploading

- Verify r2-upload skill: `python3 ~/.clawdbot/skills/r2-upload/scripts/r2-upload.py --help`
- Check R2 credentials in `~/.r2-upload.yml`

### Hexo deploy fails

- Check hexo: `hexo --version`
- Verify blog config: `cat ~/projects/blog/_config.yml | grep deploy`
