#!/usr/bin/env python3
"""LLM translation client supporting OpenAI and Minimax (Anthropic-compatible).

Env:
  # Option 1: OpenAI
  OPENAI_API_KEY (required)
  OPENAI_BASE_URL (optional, default: https://api.openai.com)
  OPENAI_MODEL (optional, default: gpt-4o-mini)

  # Option 2: Minimax (Anthropic-compatible)
  ANTHROPIC_API_KEY (required)
  ANTHROPIC_BASE_URL (optional, default: https://api.minimaxi.com/anthropic)
  ANTHROPIC_MODEL (optional, default: MiniMax-M2.1)

Priority: Minimax > OpenAI
"""

from __future__ import annotations

import json
import os
import urllib.request


def _post_json(url: str, payload: dict, headers: dict, timeout: int = 60) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def translate_title_and_summary(
    title: str,
    description: str | None = None,
    source: str | None = None,
) -> tuple[str, str]:
    """Translate title + description to Chinese (title + summary + bullets)."""

    src = source or ""
    desc = (description or "").strip()

    system = """Output ONLY:
标题：<Chinese title>
摘要：<2-3 Chinese sentences>
要点：
- <bullet 1>
- <bullet 2>
- <bullet 3>"""

    user_text = f"来源：{src}\n标题：{title}\n描述：{desc}"

    # Try Minimax first (Anthropic-compatible)
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if anthropic_key:
        base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.minimaxi.com/anthropic").rstrip("/")
        model = os.environ.get("ANTHROPIC_MODEL", "MiniMax-M2.1")

        payload = {
            "model": model,
            "max_tokens": 1500,
            "system": system,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": user_text}]}
            ],
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {anthropic_key}",
        }
        try:
            # Minimax Anthropic-compatible uses /v1/messages
            out = _post_json(f"{base_url}/v1/messages", payload, headers, timeout=90)
            # Response format: content is a list of blocks (thinking + text)
            content = out.get("content", [])
            # Find the text block (skip thinking)
            text_block = ""
            for block in content:
                if block.get("type") == "text":
                    text_block = block.get("text", "")
                    break

            if not text_block:
                raise ValueError("No text block in response")

            # Parse the simpler format:
            # 标题：<title>
            # 摘要：<sentences>
            # 要点：
            # - <bullet 1>
            # - <bullet 2>
            # - <bullet 3>
            text = text_block.strip()
            lines = text.split('\n')
            zh_title = ""
            zh_summary = ""

            current_section = ""
            summary_parts = []
            bullet_parts = []

            for line in lines:
                line = line.strip()
                if line.startswith('标题：'):
                    zh_title = line[3:].strip()
                elif line.startswith('摘要：'):
                    current_section = "summary"
                    summary_parts = [line[3:].strip()]
                elif line.startswith('要点：'):
                    current_section = "bullets"
                elif line.startswith('- '):
                    if current_section == "bullets":
                        bullet_parts.append(line[2:].strip())
                    elif current_section == "summary":
                        summary_parts.append(line[2:].strip())
                elif line and current_section == "summary":
                    summary_parts.append(line)

            # If no bullets found, add placeholder
            while len(bullet_parts) < 3:
                bullet_parts.append("细节待补充")

            # Combine summary and bullets
            if summary_parts:
                zh_summary = "\n\n".join(summary_parts)
            else:
                zh_summary = ""

            if bullet_parts:
                zh_summary = zh_summary + "\n\n要点：\n" + "\n".join(f"- {b}" for b in bullet_parts)

            return zh_title, zh_summary
        except Exception as e:
            # Minimax failed - raise error so caller knows
            raise RuntimeError(f"Minimax translation failed: {e}")

    # Fallback to OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not openai_key:
        raise RuntimeError("No translation API configured (neither ANTHROPIC_API_KEY nor OPENAI_API_KEY)")

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.2,
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {openai_key}"}

    out = _post_json(f"{base_url}/v1/chat/completions", payload, headers, timeout=60)
    text = out["choices"][0]["message"]["content"].strip()
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    zh_title = parts[0].splitlines()[0].strip()
    zh_summary = "\n\n".join(parts[1:]).strip() if len(parts) > 1 else ""
    return zh_title, zh_summary
