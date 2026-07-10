#!/usr/bin/env python3
"""Generate the terminal-style SVG used by the evgyur GitHub profile."""

from __future__ import annotations

import argparse
import calendar
import json
import os
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
USERNAME = "evgyur"
API = "https://api.github.com"


def request_json(path: str, token: str | None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "evgyur-profile-readme",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{API}{path}", headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def load_live_data(token: str | None) -> dict[str, Any]:
    user = request_json(f"/users/{USERNAME}", token)
    repos: list[dict[str, Any]] = []
    page = 1
    while True:
        batch = request_json(
            f"/users/{USERNAME}/repos?type=owner&sort=updated&per_page=100&page={page}", token
        )
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return {"user": user, "repos": repos, "generated_at": datetime.now(timezone.utc).isoformat()}


def whole_months_between(start: datetime, end: datetime) -> tuple[int, int, int]:
    months = (end.year - start.year) * 12 + end.month - start.month
    if end.day < start.day:
        months -= 1
    anchor_year = start.year + (start.month - 1 + months) // 12
    anchor_month = (start.month - 1 + months) % 12 + 1
    anchor_day = min(start.day, calendar.monthrange(anchor_year, anchor_month)[1])
    anchor = datetime(anchor_year, anchor_month, anchor_day, tzinfo=timezone.utc)
    days = (end - anchor).days
    return months // 12, months % 12, days


def summarize(data: dict[str, Any]) -> dict[str, str]:
    user = data["user"]
    repos = [repo for repo in data["repos"] if not repo.get("private")]
    originals = [repo for repo in repos if not repo.get("fork")]
    languages = Counter(repo.get("language") for repo in originals if repo.get("language"))
    top_languages = " · ".join(language for language, _ in languages.most_common(4)) or "Python · Shell"
    stars = sum(int(repo.get("stargazers_count") or 0) for repo in originals)
    latest = max((repo.get("updated_at") or "" for repo in repos), default="")
    latest_text = latest[:10] if latest else "—"
    created = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
    generated = datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))
    years, months, days = whole_months_between(created, generated)
    return {
        "uptime": f"{years}y {months}m {days}d on GitHub",
        "public_repos": str(user.get("public_repos", len(repos))),
        "original_repos": str(len(originals)),
        "followers": str(user.get("followers", 0)),
        "stars": str(stars),
        "top_languages": top_languages,
        "latest_update": latest_text,
    }


def text(x: int, y: int, value: str, css_class: str, anchor: str = "start") -> str:
    return (
        f'<text x="{x}" y="{y}" class="{css_class}" text-anchor="{anchor}">'
        f"{escape(value)}</text>"
    )


def row(y: int, label: str, value: str, value_class: str = "value") -> str:
    return "\n".join(
        [
            text(488, y, label, "key"),
            text(700, y, "········", "dots"),
            text(786, y, value, value_class),
        ]
    )


def render_portrait(portrait: dict[str, Any]) -> str:
    cols = int(portrait["cols"])
    rows = int(portrait["rows"])
    cells = portrait["cells"]
    if cols <= 0 or rows <= 0 or not isinstance(cells, list):
        raise ValueError("invalid portrait glyph payload")
    x_step = 364 / cols
    y_step = 400 / rows
    font_size = y_step * 0.94
    glyphs = []
    for cell in cells:
        if not isinstance(cell, list) or len(cell) not in (4, 5):
            raise ValueError("invalid portrait glyph cell")
        x, y, char, opacity = cell[:4]
        color = str(cell[4]) if len(cell) == 5 else "#7effdc"
        if len(color) != 7 or not color.startswith("#"):
            raise ValueError("invalid portrait glyph color")
        try:
            int(color[1:], 16)
        except ValueError as error:
            raise ValueError("invalid portrait glyph color") from error
        if not (0 <= int(x) < cols and 0 <= int(y) < rows):
            raise ValueError("portrait glyph outside grid")
        glyphs.append(
            f'<text x="{42 + int(x) * x_step:.3f}" '
            f'y="{112 + (int(y) + 0.82) * y_step:.3f}" '
            f'font-size="{font_size:.3f}" opacity="{float(opacity):.3f}" '
            f'fill="{escape(color)}" class="portraitGlyph">{escape(str(char))}</text>'
        )
    return "".join(glyphs)


def render_svg(stats: dict[str, str], portrait: dict[str, Any]) -> str:
    sections = [
        text(488, 60, "PROFILE / SYSTEM OVERVIEW", "eyebrow"),
        text(488, 92, "chip@human20.app", "hero"),
        row(136, "OS", "Human + AI agent stack"),
        row(170, "Uptime", stats["uptime"], "accent"),
        row(204, "Host", "human20.app", "accent"),
        row(238, "Kernel", "AI systems · education · crypto"),
        row(272, "Runtime", "Hermes Agent · OpenClaw · Codex"),
        text(488, 316, "— BUILD SURFACE", "section"),
        row(354, "Languages.Code", stats["top_languages"], "accent"),
        row(388, "Languages.Real", "Russian · English"),
        row(422, "Focus", "agents · automation · products"),
        row(456, "Building", "Human20 · trading infra · OSS skills"),
        text(488, 500, "— CONTACT", "section"),
        row(538, "Telegram", "@chipda", "accent"),
        row(572, "X", "@chip1cr"),
        row(606, "Web", "evgyur.pro", "accent"),
        text(488, 652, "— GITHUB SIGNAL", "section"),
    ]

    stat_items = [
        (488, "PUBLIC REPOS", stats["public_repos"]),
        (650, "ORIGINAL", stats["original_repos"]),
        (812, "STARS", stats["stars"]),
        (974, "FOLLOWERS", stats["followers"]),
    ]
    stat_svg = []
    for x, label, value in stat_items:
        stat_svg.extend(
            [
                f'<rect x="{x}" y="672" width="148" height="56" rx="12" class="statBox"/>',
                text(x + 14, 692, label, "statLabel"),
                text(x + 14, 716, value, "statValue"),
            ]
        )

    portrait_svg = render_portrait(portrait)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760" role="img" aria-labelledby="title desc">
  <title id="title">Evgeny Yurchenko — terminal profile</title>
  <desc id="desc">Terminal-style GitHub profile with an ASCII portrait, public focus areas, contact links and live GitHub statistics.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#05070b"/>
      <stop offset="0.52" stop-color="#0a0f17"/>
      <stop offset="1" stop-color="#080b12"/>
    </linearGradient>
    <radialGradient id="cyanGlow" cx="0.18" cy="0.58" r="0.54">
      <stop offset="0" stop-color="#1dd3b0" stop-opacity="0.16"/>
      <stop offset="1" stop-color="#1dd3b0" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="violetGlow" cx="0.92" cy="0.02" r="0.62">
      <stop offset="0" stop-color="#7c5cff" stop-opacity="0.14"/>
      <stop offset="1" stop-color="#7c5cff" stop-opacity="0"/>
    </radialGradient>

    <clipPath id="portraitClip">
      <rect x="42" y="112" width="364" height="400" rx="20"/>
    </clipPath>
    <filter id="softGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="18"/>
    </filter>
    <style>
      text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; }}
      .eyebrow {{ font-size: 12px; fill: #8793a8; letter-spacing: 2.0px; font-weight: 700; }}
      .hero {{ font-size: 25px; fill: #f4f7fb; font-weight: 700; letter-spacing: -0.5px; }}
      .key {{ font-size: 14px; fill: #ffb454; font-weight: 700; }}
      .dots {{ font-size: 14px; fill: #263143; letter-spacing: 1.5px; }}
      .value {{ font-size: 14px; fill: #c9d4e5; }}
      .accent {{ font-size: 14px; fill: #61e7c6; }}
      .section {{ font-size: 12px; fill: #8c98ad; letter-spacing: 1.6px; font-weight: 700; }}
      .statBox {{ fill: #0d141f; stroke: #253146; stroke-opacity: 0.8; }}
      .statLabel {{ font-size: 10px; fill: #8290a7; letter-spacing: 1.0px; font-weight: 700; }}
      .statValue {{ font-size: 18px; fill: #eef4ff; font-weight: 700; }}
      .micro {{ font-size: 10px; fill: #76849a; letter-spacing: 0.7px; }}
      .portraitGlyph {{ fill: #7effdc; font-weight: 600; }}
    </style>
  </defs>

  <rect width="1200" height="760" rx="26" fill="#020409"/>
  <rect x="5" y="5" width="1190" height="750" rx="22" fill="url(#bg)" stroke="#202a39"/>
  <rect x="6" y="6" width="1188" height="748" rx="21" fill="url(#cyanGlow)"/>
  <rect x="6" y="6" width="1188" height="748" rx="21" fill="url(#violetGlow)"/>
  <circle cx="176" cy="362" r="214" fill="#28d7b2" opacity="0.055" filter="url(#softGlow)"/>

  <text x="54" y="60" class="eyebrow">IDENTITY / ASCII SIGNAL</text>
  <text x="54" y="91" class="hero">Evgeny &quot;Chip&quot; Yurchenko</text>
  <line x1="448" y1="42" x2="448" y2="724" stroke="#263143" stroke-opacity="0.82"/>
  <rect x="42" y="112" width="364" height="400" rx="20" fill="#04100f" fill-opacity="0.74"/>
  <g clip-path="url(#portraitClip)">{portrait_svg}</g>
  <rect x="42" y="112" width="364" height="400" rx="20" fill="none" stroke="#3de1c0" stroke-opacity="0.30"/>
  <text x="54" y="536" class="micro">ASCII PORTRAIT · SOURCE: PUBLIC GITHUB AVATAR</text>
  <text x="54" y="638" class="section">— OPERATOR SIGNAL</text>
  <text x="54" y="670" class="micro">MODE  BUILD / OPERATE / TEACH</text>
  <text x="54" y="694" class="micro">LINK  EVGYUR.PRO</text>
  <text x="54" y="722" class="micro">PUBLIC PROFILE · NO PRIVATE RUNTIME DATA</text>

  {''.join(sections)}
  {''.join(stat_svg)}
  <text x="1138" y="740" class="micro" text-anchor="end">UPDATED {escape(stats['latest_update'])}</text>
</svg>
'''


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, help="Use deterministic JSON instead of GitHub API")
    parser.add_argument("--output", type=Path, default=ROOT / "assets" / "profile.svg")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.fixture:
        data = json.loads(args.fixture.read_text(encoding="utf-8"))
    else:
        data = load_live_data(os.environ.get("GITHUB_TOKEN"))
    stats = summarize(data)
    portrait = json.loads((ROOT / "assets" / "portrait-glyphs.json").read_text(encoding="utf-8"))
    output = render_svg(stats, portrait)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    sys.stdout.write(json.dumps({"output": str(args.output), "stats": stats}, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
