# Tech News Blog Examples

Common use cases and code snippets.

## Basic Examples

### Generate today's post

```bash
python3 ~/.clawdbot/skills/tech-news-blog/scripts/generate.py --date $(date +%F)
```

### Generate with images

```bash
python3 ~/.clawdbot/skills/tech-news-blog/scripts/generate.py \
  --date $(date +%F) \
  --with-images
```

### Generate and deploy

```bash
python3 ~/.clawdbot/skills/tech-news-blog/scripts/generate.py \
  --date $(date +%F) \
  --with-images \
  --deploy
```

## Advanced Examples

### Custom article count

```bash
# Get 25 articles instead of default 15
python3 scripts/generate.py --date 2026-02-04 --count 25
```

### Skip deduplication

```bash
# Include articles that appeared in previous days
python3 scripts/generate.py --date 2026-02-04 --no-dedupe
```

### Fetch news only

```bash
# Just fetch and display, don't create post
python3 scripts/fetch_news.py --count 20

# Save to JSON
python3 scripts/fetch_news.py --count 20 --output /tmp/hn-articles.json
```

## Integration Examples

### Custom blog generator

```python
#!/usr/bin/env python3
"""Custom generator with specific filters"""

import sys
sys.path.insert(0, '/root/.clawdbot/skills/tech-news-blog/scripts')

from fetch_news import fetch_hackernews, categorize_article
from translate import translate_title

def generate_ai_only_post():
    """Generate post with only AI-related articles"""
    
    # Fetch articles
    articles = fetch_hackernews(count=50)
    
    # Filter AI articles
    ai_articles = [
        a for a in articles 
        if categorize_article(a['title']) == 'AI 与机器学习'
    ][:10]  # Take top 10
    
    # Generate markdown
    lines = ['# AI News Roundup', '']
    for article in ai_articles:
        zh_title = translate_title(article['title'])
        lines.append(f'## {zh_title}')
        lines.append('')
        lines.append(f"[Read more]({article['link']})")
        lines.append('')
    
    return '\n'.join(lines)

# Save
content = generate_ai_only_post()
with open('/tmp/ai-news.md', 'w') as f:
    f.write(content)

print("Generated AI-focused post")
```

### Batch process historical posts

```python
#!/usr/bin/env python3
"""Add images to all posts from last week"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, '/root/.clawdbot/skills/tech-news-blog/scripts')
from process_images import process_post_images

sys.path.insert(0, '/root/.clawdbot/skills/r2-upload/scripts')
from upload import upload_file

blog_dir = Path.home() / 'projects/blog/source/_posts'

# Process last 7 days
for i in range(7):
    date = datetime.now() - timedelta(days=i)
    post_file = blog_dir / f"{date.strftime('%Y-%m-%d')}-科技圈新闻汇总.md"
    
    if post_file.exists():
        print(f"Processing {post_file.name}...")
        process_post_images(post_file, upload_file)
```

### Webhook integration

```python
#!/usr/bin/env python3
"""Generate post when webhook is triggered"""

import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, '/root/.clawdbot/skills/tech-news-blog/scripts')
from generate import create_blog_post

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            
            # Generate post
            post_path = create_blog_post(
                date=data.get('date'),
                count=data.get('count', 15),
                with_images=data.get('with_images', True)
            )
            
            # Send response
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'ok',
                'post': str(post_path)
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'error',
                'message': str(e)
            }).encode())
    
    def log_message(self, format, *args):
        pass  # Suppress logs

# Start server
server = HTTPServer(('localhost', 8080), WebhookHandler)
print("Webhook server on http://localhost:8080")
server.serve_forever()
```

## Image Processing Examples

### Add images to single post

```bash
python3 scripts/process_images.py \
  --post ~/projects/blog/source/_posts/2026-02-04-科技圈新闻汇总.md
```

### Fetch image URLs only (no upload)

```bash
python3 scripts/process_images.py \
  --post ~/projects/blog/source/_posts/2026-02-04-科技圈新闻汇总.md \
  --no-upload
```

### Custom image upload

```python
import sys
sys.path.insert(0, '/root/.clawdbot/skills/r2-upload/scripts')
from upload import fetch_and_upload

# Download from URL and upload
url = fetch_and_upload(
    image_url='https://example.com/image.jpg',
    key='images/2026/02/04/custom.jpg',
    make_public=True
)
print(f"Image uploaded: {url}")
```

## Translation Examples

### Translate single title

```bash
$ python3 scripts/translate.py "Show HN: My Rust Project"
Show HN：My Rust Project
```

### Batch translate from file

```bash
# titles.txt contains one title per line
$ cat titles.txt
Show HN: Cool Tool
Launch HN: Startup Name
Ask HN: Best Practices?

$ python3 scripts/translate.py --file titles.txt
Show HN: Cool Tool
-> Show HN：Cool Tool

Launch HN: Startup Name
-> Launch HN：Startup Name

Ask HN: Best Practices?
-> Ask HN：Best Practices？
```

### Pipe from other commands

```bash
# Translate article titles from fetch_news output
python3 scripts/fetch_news.py --count 5 | grep "^\d" | cut -d' ' -f2- | python3 scripts/translate.py
```

## Deployment Examples

### GitHub Actions workflow

```yaml
# .github/workflows/tech-news.yml
name: Daily Tech News

on:
  schedule:
    - cron: '0 9 * * *'  # 9 AM daily
  workflow_dispatch:

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install pyyaml
      
      - name: Generate post
        run: |
          python3 ~/.clawdbot/skills/tech-news-blog/scripts/generate.py \
            --date $(date +%F) \
            --with-images
        env:
          R2_UPLOAD_CONFIG: ${{ secrets.R2_CONFIG }}
      
      - name: Deploy
        run: |
          cd ~/projects/blog
          hexo clean && hexo g && hexo d
```

### Docker usage

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copy skills
COPY tech-news-blog/ /skills/tech-news-blog/
COPY r2-upload/ /skills/r2-upload/

# Install dependencies
RUN pip install pyyaml

# Set entrypoint
ENTRYPOINT ["python3", "/skills/tech-news-blog/scripts/generate.py"]
```

```bash
# Build and run
docker build -t tech-news-blog .
docker run -v ~/.r2-upload.yml:/root/.r2-upload.yml tech-news-blog --date $(date +%F)
```

## Error Handling Examples

### Graceful fallback

```python
#!/usr/bin/env python3
import sys

sys.path.insert(0, '/root/.clawdbot/skills/tech-news-blog/scripts')

try:
    from generate import create_blog_post
    post = create_blog_post(with_images=True)
    print(f"Created: {post}")
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install: pip install pyyaml")
except Exception as e:
    print(f"Error: {e}")
    # Fallback: create without images
    post = create_blog_post(with_images=False)
    print(f"Created (no images): {post}")
```

### Retry logic

```python
import time
from fetch_news import fetch_hackernews

# Retry up to 3 times
for attempt in range(3):
    try:
        articles = fetch_hackernews(count=20)
        break
    except Exception as e:
        if attempt == 2:
            raise
        print(f"Attempt {attempt + 1} failed, retrying...")
        time.sleep(5)
```
