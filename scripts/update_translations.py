#!/usr/bin/env python3
"""Keep paragraph-level English translations in sync with Quarto posts.

The script scans posts that reference ``translations-en.json`` in their YAML
front matter. Existing translations are reused by exact source-text match.
Only a changed title or new/changed paragraphs are sent to an
OpenAI-compatible API.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "posts"
TRANSLATION_FILENAME = "translations-en.json"


@dataclass
class Post:
    path: Path
    title: str
    sources: list[str]
    translation_path: Path


def normalize(text: str) -> str:
    return " ".join(text.split())


def split_front_matter(text: str) -> tuple[str, str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing YAML front matter")

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "".join(lines[1:index]), "".join(lines[index + 1 :])
    raise ValueError("unterminated YAML front matter")


def parse_title(front_matter: str) -> str:
    match = re.search(r'^title:\s*(.+?)\s*$', front_matter, re.MULTILINE)
    if not match:
        raise ValueError("missing title in YAML front matter")

    value = match.group(1).strip()
    if value.startswith(('"', "'")):
        try:
            return json.loads(value) if value.startswith('"') else value[1:-1]
        except json.JSONDecodeError:
            pass
    return value


def plain_markdown(text: str) -> str:
    text = re.sub(r"^>\s*", "", text)
    text = re.sub(r"^\d+\.\s+", "", text)
    text = re.sub(r"^[-*+]\s+", "", text)
    text = re.sub(r"!\[[^]]*]\([^)]*\)(?:\{[^}]*\})?", "", text)
    text = re.sub(r"\[([^]]+)]\([^)]*\)", r"\1", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    return normalize(text)


def extract_sources(body: str) -> list[str]:
    sources: list[str] = []
    for raw_block in re.split(r"\n\s*\n", body.strip()):
        block = raw_block.strip()
        if not block or block == "---" or block.startswith("!["):
            continue
        if block.startswith("#") or block.startswith(":::"):
            continue

        lines = block.splitlines()
        ordered = len(lines) > 1 and all(re.match(r"^\d+\.\s+", line) for line in lines)
        unordered = len(lines) > 1 and all(re.match(r"^[-*+]\s+", line) for line in lines)
        candidates = lines if ordered or unordered else [block]

        for candidate in candidates:
            source = plain_markdown(candidate)
            if source:
                sources.append(source)
    return sources


def discover_posts() -> list[Post]:
    posts: list[Post] = []
    for path in sorted(POSTS_DIR.rglob("*.qmd")):
        text = path.read_text(encoding="utf-8")
        try:
            front_matter, body = split_front_matter(text)
        except ValueError as error:
            raise SystemExit(f"{path.relative_to(ROOT)}: {error}") from error

        if TRANSLATION_FILENAME not in front_matter:
            continue

        try:
            title = parse_title(front_matter)
        except ValueError as error:
            raise SystemExit(f"{path.relative_to(ROOT)}: {error}") from error

        posts.append(
            Post(
                path=path,
                title=title,
                sources=extract_sources(body),
                translation_path=path.parent / TRANSLATION_FILENAME,
            )
        )
    return posts


def read_payload(path: Path) -> dict:
    if not path.exists():
        return {"language": "en", "label": "AI-assisted English translation", "items": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise SystemExit(f"Cannot read {path.relative_to(ROOT)}: {error}") from error


def api_settings() -> tuple[str, str, str] | None:
    explicit_key = os.getenv("TRANSLATION_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    key = explicit_key or deepseek_key or openai_key
    if not key:
        return None

    if openai_key and not explicit_key and not deepseek_key:
        default_base = "https://api.openai.com/v1"
        default_model = "gpt-4o-mini"
    else:
        default_base = "https://api.deepseek.com"
        default_model = "deepseek-chat"

    base = os.getenv("TRANSLATION_API_BASE", default_base).rstrip("/")
    model = os.getenv("TRANSLATION_MODEL", default_model)
    return key, base, model


def chunks(texts: list[str], max_items: int = 8, max_chars: int = 6000) -> Iterable[list[str]]:
    chunk: list[str] = []
    chars = 0
    for text in texts:
        if chunk and (len(chunk) >= max_items or chars + len(text) > max_chars):
            yield chunk
            chunk, chars = [], 0
        chunk.append(text)
        chars += len(text)
    if chunk:
        yield chunk


def request_translations(texts: list[str], settings: tuple[str, str, str]) -> list[str]:
    key, base, model = settings
    results: list[str] = []

    for batch in chunks(texts):
        prompt = {
            "target_language": "English",
            "texts": batch,
            "requirements": [
                "Translate each item accurately and naturally for an academic technical blog.",
                "Preserve technical terms and capitalization such as DSH, Cordis, LIFO, VSC, Plugin, and self-evolving.",
                "Preserve the author's informal tone and analogies without adding explanations.",
                "Return exactly one translation for each source item in the same order.",
            ],
        }
        request_body = {
            "model": model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": "Return only a JSON object with a 'translations' array of strings.",
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
        }
        request = urllib.request.Request(
            f"{base}/chat/completions",
            data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                response_body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace")[:1000]
            raise SystemExit(f"Translation API returned HTTP {error.code}: {detail}") from error
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            raise SystemExit(f"Translation API request failed: {error}") from error

        try:
            content = response_body["choices"][0]["message"]["content"].strip()
            content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE)
            translated = json.loads(content)["translations"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
            raise SystemExit("Translation API returned an unexpected response") from error

        if len(translated) != len(batch) or not all(isinstance(item, str) and item.strip() for item in translated):
            raise SystemExit("Translation API returned the wrong number of translations")
        results.extend(item.strip() for item in translated)

    return results


def write_payload(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(path)


def sync_post(post: Post, *, check: bool, force: bool, settings: tuple[str, str, str] | None) -> bool:
    payload = read_payload(post.translation_path)
    existing = {
        normalize(item.get("source", "")): item.get("translation", "")
        for item in payload.get("items", [])
        if item.get("source") and item.get("translation")
    }

    title_changed = force or payload.get("titleSource") != post.title or not payload.get("titleTranslation")
    missing_sources = post.sources if force else [source for source in post.sources if source not in existing]
    stale_sources = set(existing) - set(post.sources)
    changed = title_changed or bool(missing_sources) or bool(stale_sources)
    relative = post.path.relative_to(ROOT)

    if not changed:
        print(f"Translations up to date: {relative}")
        return False

    print(
        f"Translation changes: {relative} "
        f"(title={int(title_changed)}, new={len(missing_sources)}, stale={len(stale_sources)})"
    )
    if check:
        return True
    if settings is None:
        raise SystemExit(
            "Translations are stale, but no API key is configured. Set DEEPSEEK_API_KEY, "
            "OPENAI_API_KEY, or TRANSLATION_API_KEY before rendering."
        )

    requested: list[str] = []
    if title_changed:
        requested.append(post.title)
    requested.extend(missing_sources)
    generated = iter(request_translations(requested, settings))

    title_translation = next(generated) if title_changed else payload["titleTranslation"]
    replacements = {source: next(generated) for source in missing_sources}
    items = [
        {
            "source": source,
            "translation": replacements.get(source, existing.get(source, "")),
        }
        for source in post.sources
    ]

    updated = {
        "language": "en",
        "label": payload.get("label", "AI-assisted English translation"),
        "titleSource": post.title,
        "titleTranslation": title_translation,
        "items": items,
    }
    write_payload(post.translation_path, updated)
    print(f"Updated: {post.translation_path.relative_to(ROOT)}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report stale translations without calling an API")
    parser.add_argument("--force", action="store_true", help="regenerate every title and paragraph")
    args = parser.parse_args()

    posts = discover_posts()
    if not posts:
        print("No translated posts found.")
        return 0

    settings = None if args.check else api_settings()
    changed = False
    for post in posts:
        changed = sync_post(post, check=args.check, force=args.force, settings=settings) or changed
    if args.check and changed:
        print("Translations need updating.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
