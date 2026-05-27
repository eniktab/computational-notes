from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"
INDEX_FILE = ROOT / "index.qmd"
SITE_TITLE = "Computational Notes"
SITE_AUTHOR = "Eli Niktab"
MAX_POSTS = 3


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
      return {}, text

    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
      return {}, text

    raw_meta = parts[0].splitlines()[1:]
    body = parts[1]
    meta: dict[str, str] = {}
    pattern = re.compile(r'^([A-Za-z0-9_-]+):\s*"?(.+?)"?\s*$')
    for line in raw_meta:
        match = pattern.match(line.strip())
        if match:
            meta[match.group(1)] = match.group(2)
    return meta, body.lstrip()


def sort_key(post: dict[str, object]) -> tuple[int, str]:
    date = post.get("date")
    if isinstance(date, str):
        try:
            parsed = datetime.fromisoformat(date)
            return (int(parsed.timestamp()), str(post["path"]))
        except ValueError:
            pass

    path = ROOT / str(post["path"])
    return (int(path.stat().st_mtime), str(post["path"]))


def load_posts() -> list[dict[str, object]]:
    posts: list[dict[str, object]] = []
    for path in POSTS_DIR.glob("**/index.qmd"):
        text = path.read_text()
        meta, body = parse_front_matter(text)
        posts.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "title": meta.get("title", path.parent.name.replace("-", " ").title()),
                "date": meta.get("date", ""),
                "body": body.strip(),
            }
        )
    posts.sort(key=sort_key, reverse=True)
    return posts[:MAX_POSTS]


def render_home(posts: list[dict[str, object]]) -> str:
    lines = [
        "---",
        f'title: "{SITE_TITLE}"',
        f'subtitle: "{SITE_AUTHOR}"',
        "toc: false",
        "---",
        "",
    ]

    # Right-rail "Recent posts" sidebar — Quarto column directive that
    # places content in the margin column on wide screens and inline on
    # narrow ones.
    lines.append("::: {.column-margin .recent-posts}")
    lines.append("**Recent posts**")
    lines.append("")
    for post in posts:
        date_suffix = f" — *{post['date']}*" if post["date"] else ""
        lines.append(f"- [{post['title']}]({post['path']}){date_suffix}")
    lines.append(":::")
    lines.append("")

    for index, post in enumerate(posts):
        lines.append(f'## [{post["title"]}]({post["path"]})')
        meta_bits = []
        if post["date"]:
            meta_bits.append(str(post["date"]))
        if meta_bits:
            lines.append("")
            lines.append(f'*{" · ".join(meta_bits)}*')
        lines.append("")
        lines.append(str(post["body"]))
        lines.append("")
        if index != len(posts) - 1:
            lines.append("---")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    posts = load_posts()
    INDEX_FILE.write_text(render_home(posts))


if __name__ == "__main__":
    main()
