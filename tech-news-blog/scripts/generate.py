#!/usr/bin/env python3
"""
Tech News Blog Generator - Main script for generating blog posts

Supports:
- Single-source (Hacker News) generation (default)
- Multi-source aggregation via fetch_news.py (use --sources)

Usage:
  python3 generate.py --date YYYY-MM-DD [--with-images] [--deploy]
  python3 generate.py --date YYYY-MM-DD --sources hackernews lobsters devto --count 10 --with-images
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin

# Config
BLOG_DIR = Path.home() / "projects/blog"
POSTS_DIR = BLOG_DIR / "source/_posts"
CATEGORIES = ["AI 与机器学习", "游戏与怀旧科技", "开发工具与开源", "基础设施与行业", "趣闻"]

FETCH_NEWS = Path(__file__).with_name("fetch_news.py")

def fetch_description(url, timeout=10):
    """Fetch page description from URL (og:description or meta description)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        # Try og:description first
        og_desc = re.search(r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']', html, re.I)
        if og_desc:
            return og_desc.group(1).strip()

        # Try regular description
        meta_desc = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html, re.I)
        if meta_desc:
            return meta_desc.group(1).strip()
    except Exception:
        pass
    return None

def fetch_hackernews(count=20):
    """Fetch top stories from Hacker News RSS."""
    url = f"https://hnrss.org/frontpage?points=50&count={count}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    with urllib.request.urlopen(req, timeout=30) as resp:
        xml = resp.read().decode("utf-8")

    # Parse RSS (simple regex approach)
    items = []
    item_pattern = re.compile(r'<item>(.*?)</item>', re.DOTALL)

    for item_match in item_pattern.findall(xml)[:count]:
        title = re.search(r'<title>(.*?)</title>', item_match)
        link = re.search(r'<link>(.*?)</link>', item_match)
        comments = re.search(r'<comments>(.*?)</comments>', item_match)
        pub_date = re.search(r'<pubDate>(.*?)</pubDate>', item_match)

        if title and link:
            link_url = link.group(1).strip()
            title_text = title.group(1).replace('<![CDATA[', '').replace(']]>', '').strip()

            # Try to fetch description from original link
            description = fetch_description(link_url)

            items.append({
                "title": title_text,
                "link": link_url,
                "description": description,
                "comments": comments.group(1).strip() if comments else None,
                "pub_date": pub_date.group(1).strip() if pub_date else None,
                "source": "hackernews",
                "source_name": "Hacker News",
            })

    return items


def fetch_multi_sources(sources, count=20):
    """Fetch news from multiple sources via fetch_news.py and return JSON list."""
    tmp = Path("/tmp/tech-news-blog.json")
    cmd = [sys.executable, str(FETCH_NEWS), "--sources", *sources, "--count", str(count), "--output", str(tmp)]
    subprocess.run(cmd, check=True)
    return json.loads(tmp.read_text(encoding="utf-8"))

def categorize(title):
    """Categorize article by title keywords"""
    t = title.lower()
    
    if any(k in t for k in ["ai", "llm", "model", "agent", "gpt", "claude", "grok", "ml ", "neural", "deep learning"]):
        return "AI 与机器学习"
    elif any(k in t for k in ["game", "gaming", "retro", "vintage", "nostalgia", "classic", "emulator", "amiga", "commodore"]):
        return "游戏与怀旧科技"
    elif any(k in t for k in ["rust", "python", "javascript", "github", "open source", "framework", "library", "tool", "compiler", "database", "sql"]):
        return "开发工具与开源"
    elif any(k in t for k in ["cloud", "aws", "gcp", "azure", "server", "datacenter", "infrastructure", "kubernetes", "docker", "devops", "security", "privacy", "encryption"]):
        return "基础设施与行业"
    else:
        return "趣闻"

# Translation now handled by llm_translate.py

def translate_with_llm(title, description, source_name=None):
    """Translate title + description to Chinese using LLM.

    Uses Minimax (Anthropic-compatible) or OpenAI if configured.
    Falls back to a simple template otherwise.
    """
    import os
    import sys as _sys

    # Try real translation if configured
    try:
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
        openai_key = os.environ.get('OPENAI_API_KEY', '').strip()
        has_api_key = bool(anthropic_key or openai_key)
        
        if has_api_key:
            # Add current script directory to path and import
            script_dir = str(Path(__file__).parent)
            if script_dir not in _sys.path:
                _sys.path.insert(0, script_dir)
            from llm_translate import translate_title_and_summary
            # 即使 description 为空也尝试翻译
            result = translate_title_and_summary(title, description=description or "", source=source_name)
            return result
        else:
            print(f"[DEBUG] No API key", file=_sys.stderr)
    except Exception as e:
        print(f"[DEBUG] Translation failed: {e}", file=_sys.stderr)

    # Fallback: simple template (keep English title if no LLM)
    zh_title = title
    src = source_name or "社区"
    zh_summary = f"来自 {src} 的热门话题。"

    zh_summary = zh_summary + "\n\n要点：\n- 细节待补充\n- 细节待补充\n- 细节待补充"
    return zh_title, zh_summary

def create_post_content(date, articles, with_images=False):
    """Generate blog post markdown content."""
    lines = []

    # Frontmatter
    now = datetime.now()
    lines.append("---")
    lines.append(f"title: {date} 科技圈新闻汇总")
    lines.append(f"date: {date} {now.hour:02d}:{now.minute:02d}:00")
    lines.append("tags: [AI, 游戏, 开发工具, 科技新闻]")
    lines.append("categories: [技术新闻]")
    lines.append("---")
    lines.append("")

    # Generate dynamic summary based on actual content
    categories_present = set()
    topics_mentioned = []
    for article in articles:
        cat = categorize(article.get("title", ""))
        categories_present.add(cat)
        # Extract key topics from title
        title_lower = article.get("title", "").lower()
        if any(k in title_lower for k in ["ai", "llm", "gpt", "claude"]):
            topics_mentioned.append("AI")
        elif any(k in title_lower for k in ["cloud", "aws", "kubernetes", "docker"]):
            topics_mentioned.append("云原生")
        elif any(k in title_lower for k in ["rust", "python", "javascript"]):
            topics_mentioned.append("编程语言")
        elif any(k in title_lower for k in ["game", "gaming"]):
            topics_mentioned.append("游戏")

    unique_topics = list(set(topics_mentioned))[:3]
    unique_cats = [c for c in ["AI 与机器学习", "开发工具与开源", "基础设施与行业", "游戏与怀旧科技"] if c in categories_present]

    # Build dynamic summary
    summary_parts = [f"精选 {len(articles)} 条来自 Hacker News 的热门话题"]
    if unique_topics:
        summary_parts.append(f"，涵盖 {'/'.join(unique_topics)} 等主题")
    if unique_cats:
        summary_parts.append(f"，内容涉及 {unique_cats[0]}")
        if len(unique_cats) > 1:
            summary_parts.append(f"及 {unique_cats[1]}")

    lines.append(f"> 📰 **{''.join(summary_parts)}**")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Group articles by category
    grouped = {cat: [] for cat in CATEGORIES}
    for article in articles:
        cat = categorize(article["title"])
        grouped[cat].append(article)

    # Generate content by category
    for category in CATEGORIES:
        items = grouped[category]
        if not items:
            continue

        lines.append(f"## {category}")
        lines.append("")

        for item in items:
            zh_title = item.get("zh_title") or item["title"]
            zh_summary = item.get("zh_summary") or generate_summary(
                item["title"],
                item["link"],
                source_name=item.get("source_name"),
                description=item.get("description"),
            )

            lines.append(f"### {zh_title}")
            lines.append("")

            if with_images:
                lines.append(f"<!-- IMAGE: {item['link']} -->")
                lines.append("")

            lines.append(zh_summary)
            lines.append("")

            if item.get("comments"):
                lines.append(f"📎 [讨论区]({item['comments']})")
                lines.append("")
            lines.append(f"📎 [原文链接]({item['link']})")
            lines.append("")
            lines.append("---")
            lines.append("")

    lines.append("*本文汇总自多个社区信息源，每日更新，涵盖 AI 应用、游戏技术、开发工具及科技行业动态。*")
    lines.append("")

    return "\n".join(lines)

def pick_articles_balanced(articles, limit=10, per_source=2, source_order=None):
    """Pick a balanced set of articles across sources.

    Strategy:
    - Keep source order stable and configurable.
    - Take up to per_source from each source, then fill remaining slots round-robin.
    """
    buckets = {}
    for a in articles:
        buckets.setdefault(a.get('source', 'unknown'), []).append(a)

    order = source_order or sorted(buckets.keys())

    picked = []

    for src in order:
        if src in buckets:
            picked.extend(buckets[src][:per_source])
        if len(picked) >= limit:
            return picked[:limit]

    i = per_source
    while len(picked) < limit:
        progressed = False
        for src in order:
            if src in buckets and i < len(buckets[src]):
                picked.append(buckets[src][i])
                progressed = True
                if len(picked) >= limit:
                    return picked[:limit]
        if not progressed:
            break
        i += 1

    return picked[:limit]


def create_blog_post(date=None, count=15, with_images=False, dedupe=True, sources=None, max_images=25, limit=10):
    """Main function to create a blog post."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    if sources:
        print(f"Fetching {count} articles per source from: {', '.join(sources)}...")
        articles = fetch_multi_sources(sources, count)
    else:
        print(f"Fetching {count} articles from Hacker News...")
        articles = fetch_hackernews(count)

    print(f"Fetched {len(articles)} articles")

    if dedupe:
        articles = dedupe_articles(articles, date)
        print(f"After dedupe: {len(articles)} articles")

    # Final selection: balanced across sources (follow the provided source order)
    source_order = sources or []
    articles = pick_articles_balanced(articles, limit=limit, per_source=2, source_order=source_order)
    print(f"Selected: {len(articles)} articles")

    # Translate only selected items (cached)
    cache_path = Path(__file__).parent.parent / "cache" / "translations.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        cache = {}

    for a in articles:
        key = a.get("link") or a.get("title")
        if not key:
            continue
        if key in cache:
            a["zh_title"] = cache[key].get("zh_title")
            a["zh_summary"] = cache[key].get("zh_summary")
            continue

        zh_title, zh_summary = translate_with_llm(a.get("title", ""), a.get("description"), source_name=a.get("source_name"))
        a["zh_title"] = zh_title
        a["zh_summary"] = zh_summary
        cache[key] = {"zh_title": zh_title, "zh_summary": zh_summary}

    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Generating blog post...")
    content = create_post_content(date, articles, with_images)

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    post_path = POSTS_DIR / f"{date}-科技圈新闻汇总.md"
    post_path.write_text(content, encoding="utf-8")

    print(f"Created: {post_path}")

    if with_images:
        print(f"Processing images (max {max_images})...")
        process_images(post_path, max_images=max_images)

    return post_path

def dedupe_articles(articles, current_date, days=3):
    """Remove articles already present in previous posts."""
    # Get links from previous posts (last N days)
    seen_links = set()

    base = datetime.strptime(current_date, "%Y-%m-%d")
    for i in range(1, days + 1):
        prev_date = base - timedelta(days=i)
        prev_file = POSTS_DIR / f"{prev_date.strftime('%Y-%m-%d')}-科技圈新闻汇总.md"

        if prev_file.exists():
            content = prev_file.read_text(encoding="utf-8")
            links = re.findall(r'\[原文链接\]\(([^)]+)\)', content)
            seen_links.update(links)

    return [a for a in articles if a.get("link") not in seen_links]

def process_images(post_path, max_images=25, per_page_timeout=5, total_timeout=90):
    """Fetch og:image for each article and upload to R2.

    Rules:
    - If no og:image (or fetch fails), remove placeholder.
    - Cap uploads to avoid long runs/timeouts.
    - Hard-stop after total_timeout seconds.
    """
    import time

    try:
        sys.path.insert(0, '/root/.clawdbot/skills/r2-upload/scripts')
        from upload import fetch_and_upload
    except ImportError:
        print("Warning: r2-upload skill not available, skipping images")
        return

    start = time.time()

    content = post_path.read_text(encoding="utf-8")
    placeholders = re.findall(r'<!-- IMAGE: (.*?) -->', content)

    uploaded = 0
    for article_url in placeholders:
        # Enforce global time budget
        if time.time() - start > total_timeout:
            content = content.replace(f"<!-- IMAGE: {article_url} -->", "")
            continue

        if uploaded >= max_images:
            content = content.replace(f"<!-- IMAGE: {article_url} -->", "")
            continue

        try:
            req = urllib.request.Request(article_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=per_page_timeout) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            og_match = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', html, re.I)
            if not og_match:
                og_match = re.search(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', html, re.I)

            if not og_match:
                content = content.replace(f"<!-- IMAGE: {article_url} -->", "")
                continue

            image_url = urljoin(article_url, og_match.group(1))

            date = post_path.stem[:10]
            key = f"images/{date.replace('-', '/')}/article-{uploaded:02d}.jpg"
            public_url = fetch_and_upload(image_url, key=key, make_public=True)

            img_tag = f'<img src="{public_url}" alt="配图" style="max-width:100%;height:auto;margin:10px 0;">'
            content = content.replace(f"<!-- IMAGE: {article_url} -->", img_tag)

            uploaded += 1

        except Exception:
            # Any failure: no image.
            content = content.replace(f"<!-- IMAGE: {article_url} -->", "")

    post_path.write_text(content, encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description="Generate tech news blog post")
    parser.add_argument("--date", help="Date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--count", type=int, default=15, help="Number of articles to fetch (per source if --sources is used)")
    parser.add_argument("--sources", nargs="+", help="Multiple sources (e.g. hackernews lobsters devto arxiv-ai)")
    parser.add_argument("--with-images", action="store_true", default=True, help="Include article images (only if og:image is available)")
    parser.add_argument("--no-images", action="store_true", help="Disable images (for faster generation)")
    parser.add_argument("--no-dedupe", action="store_true", help="Don't dedupe with previous posts")
    parser.add_argument("--deploy", action="store_true", default=True, help="Deploy after generation")
    parser.add_argument("--no-deploy", action="store_true", help="Skip deployment")
    parser.add_argument("--max-images", type=int, default=15, help="Max images to upload and embed (default: 15)")
    parser.add_argument("--limit", type=int, default=10, help="Final number of articles in the post (default: 10)")

    args = parser.parse_args()

    # Default: enable images and deploy (unless explicitly disabled)
    with_images = args.with_images and not args.no_images
    deploy = args.deploy and not args.no_deploy

    post_path = create_blog_post(
        date=args.date,
        count=args.count,
        with_images=with_images,
        dedupe=not args.no_dedupe,
        sources=args.sources,
        max_images=args.max_images,
        limit=args.limit,
    )

    if args.deploy:
        subprocess.run(["hexo", "clean"], cwd=BLOG_DIR, check=True)
        subprocess.run(["hexo", "g"], cwd=BLOG_DIR, check=True)
        subprocess.run(["hexo", "d"], cwd=BLOG_DIR, check=True)
        print("Deployed!")

if __name__ == "__main__":
    main()
