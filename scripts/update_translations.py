#!/usr/bin/env python3
"""Keep paragraph-level bilingual translations in sync with Quarto posts.

The script detects whether each post is primarily Chinese or English, then
creates English translations for Chinese originals and Simplified Chinese
translations for English originals. Existing translations are reused by exact
source-text match; only changed content is sent to the selected translator.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
import tempfile
import urllib.error
import urllib.request
from urllib.parse import urlparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "posts"
DEFAULT_DLX_URL = "http://127.0.0.1:1188/translate"
LANGUAGE_NAMES = {"en": "English", "zh": "Simplified Chinese"}
DLX_LANGUAGE_CODES = {"en": "EN", "zh": "ZH"}


@dataclass
class Post:
    path: Path
    title: str
    sources: list[str]
    source_language: str
    target_language: str
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


def detect_source_language(front_matter: str, title: str, sources: list[str]) -> str:
    override = re.search(
        r"^translation-source:\s*(en|zh)\s*$", front_matter, re.MULTILINE | re.IGNORECASE
    )
    if override:
        return override.group(1).lower()

    sample = " ".join([title, *sources])
    cjk_count = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", sample))
    latin_count = len(re.findall(r"[A-Za-z]", sample))
    return "zh" if cjk_count / max(cjk_count + latin_count, 1) >= 0.2 else "en"


def discover_posts() -> list[Post]:
    posts: list[Post] = []
    for path in sorted(POSTS_DIR.rglob("*.qmd")):
        text = path.read_text(encoding="utf-8")
        try:
            front_matter, body = split_front_matter(text)
        except ValueError as error:
            raise SystemExit(f"{path.relative_to(ROOT)}: {error}") from error

        if re.search(r"^translation:\s*false\s*$", front_matter, re.MULTILINE | re.IGNORECASE):
            continue

        try:
            title = parse_title(front_matter)
        except ValueError as error:
            raise SystemExit(f"{path.relative_to(ROOT)}: {error}") from error

        sources = extract_sources(body)
        if not sources:
            continue
        source_language = detect_source_language(front_matter, title, sources)
        target_language = "en" if source_language == "zh" else "zh"
        posts.append(
            Post(
                path=path,
                title=title,
                sources=sources,
                source_language=source_language,
                target_language=target_language,
                translation_path=path.parent / f"translations-{target_language}.json",
            )
        )
    return posts


def read_payload(path: Path, target_language: str) -> dict:
    if not path.exists():
        return {
            "language": target_language,
            "label": f"{LANGUAGE_NAMES[target_language]} translation",
            "items": [],
        }
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


def dlx_url() -> str:
    return os.getenv("DLX_URL", os.getenv("DEEPLX_URL", DEFAULT_DLX_URL))


def dlx_available(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def request_dlx_translations(
    texts: list[str], url: str, source_language: str, target_language: str
) -> list[str]:
    results: list[str] = []
    for index, text in enumerate(texts, start=1):
        request = urllib.request.Request(
            url,
            data=json.dumps(
                {
                    "text": text,
                    "source_lang": DLX_LANGUAGE_CODES[source_language],
                    "target_lang": DLX_LANGUAGE_CODES[target_language],
                },
                ensure_ascii=False,
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace")[:1000]
            raise SystemExit(f"DLX returned HTTP {error.code}: {detail}") from error
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            raise SystemExit(f"DLX request failed: {error}") from error

        translated = payload.get("data")
        if payload.get("code", 200) != 200 or not isinstance(translated, str) or not translated.strip():
            raise SystemExit(f"DLX returned an unexpected response for item {index}")
        results.append(translated.strip())
    return results


def request_api_translations(
    texts: list[str],
    settings: tuple[str, str, str],
    source_language: str,
    target_language: str,
) -> list[str]:
    key, base, model = settings
    results: list[str] = []

    for batch in chunks(texts):
        prompt = {
            "source_language": LANGUAGE_NAMES[source_language],
            "target_language": LANGUAGE_NAMES[target_language],
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


def generate_translations(
    texts: list[str],
    api: tuple[str, str, str] | None,
    source_language: str,
    target_language: str,
) -> list[str]:
    provider = os.getenv("TRANSLATION_PROVIDER", "auto").lower()
    if provider not in {"auto", "dlx", "api"}:
        raise SystemExit("TRANSLATION_PROVIDER must be one of: auto, dlx, api")

    local_url = dlx_url()
    if provider != "api" and dlx_available(local_url):
        print(f"Using local DLX: {local_url}")
        return request_dlx_translations(texts, local_url, source_language, target_language)
    if provider == "dlx":
        raise SystemExit(f"Local DLX is not reachable at {local_url}")

    if api is not None:
        _, base, model = api
        print(f"Using translation API: {base} ({model})")
        return request_api_translations(texts, api, source_language, target_language)

    raise SystemExit(
        f"Translations are stale and local DLX is not reachable at {local_url}. "
        "Start DLX, or set DEEPSEEK_API_KEY, OPENAI_API_KEY, or TRANSLATION_API_KEY."
    )


def write_payload(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(path)


def sync_post(post: Post, *, check: bool, force: bool, settings: tuple[str, str, str] | None) -> bool:
    payload = read_payload(post.translation_path, post.target_language)
    obsolete_target = "zh" if post.target_language == "en" else "en"
    obsolete_path = post.path.parent / f"translations-{obsolete_target}.json"
    obsolete_exists = obsolete_path.exists()
    existing = {
        normalize(item.get("source", "")): item.get("translation", "")
        for item in payload.get("items", [])
        if item.get("source") and item.get("translation")
    }

    language_changed = (
        payload.get("language") != post.target_language
        or payload.get("sourceLanguage") not in {None, post.source_language}
    )
    regenerate = force or language_changed
    metadata_changed = payload.get("sourceLanguage") != post.source_language
    title_changed = (
        regenerate
        or payload.get("titleSource") != post.title
        or not payload.get("titleTranslation")
    )
    missing_sources = (
        post.sources
        if regenerate
        else [source for source in post.sources if source not in existing]
    )
    stale_sources = set(existing) - set(post.sources)
    changed = (
        metadata_changed
        or title_changed
        or bool(missing_sources)
        or bool(stale_sources)
        or obsolete_exists
    )
    relative = post.path.relative_to(ROOT)

    if not changed:
        print(
            f"Translations up to date: {relative} "
            f"({post.source_language} → {post.target_language})"
        )
        return False

    print(
        f"Translation changes: {relative} "
        f"({post.source_language} → {post.target_language}, title={int(title_changed)}, "
        f"new={len(missing_sources)}, stale={len(stale_sources)}, "
        f"obsolete={int(obsolete_exists)})"
    )
    if check:
        return True

    requested: list[str] = []
    if title_changed:
        requested.append(post.title)
    requested.extend(missing_sources)
    generated = iter(
        generate_translations(
            requested, settings, post.source_language, post.target_language
        )
        if requested
        else []
    )

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
        "sourceLanguage": post.source_language,
        "language": post.target_language,
        "label": f"{LANGUAGE_NAMES[post.target_language]} translation",
        "titleSource": post.title,
        "titleTranslation": title_translation,
        "items": items,
    }
    write_payload(post.translation_path, updated)
    if obsolete_exists:
        obsolete_path.unlink()
        print(f"Removed: {obsolete_path.relative_to(ROOT)}")
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
