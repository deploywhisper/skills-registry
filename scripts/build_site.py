"""Build a static GitHub Pages site for the skills registry."""

from __future__ import annotations

import json
from pathlib import Path
import shutil


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
DOCS_DIR = REPO_ROOT / "docs"
SITE_DIR = REPO_ROOT / "site"


def _load_entries() -> list[dict]:
    entries: list[dict] = []
    for manifest_path in sorted(SKILLS_DIR.glob("*/manifest.json")):
        skill_dir = manifest_path.parent
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        scenarios_dir = skill_dir / "tests" / "scenarios"
        scenario_count = len(list(scenarios_dir.glob("*.json"))) if scenarios_dir.exists() else 0
        payload["skill_id"] = str(payload["name"])
        payload["path"] = str(skill_dir.relative_to(REPO_ROOT))
        payload["scenario_count"] = scenario_count
        entries.append(payload)
    return entries


def _render_index(entries: list[dict]) -> str:
    rows = []
    for entry in entries:
        rows.append(
            "<article class='skill-row'>"
            f"<div><h2><a href='skills/{entry['skill_id']}/'>{entry['skill_id'].replace('-', ' ').title()}</a></h2>"
            f"<p>{entry['description']}</p>"
            f"<div class='meta'>{entry['author']} · v{entry['version']} · {entry['scenario_count']} scenarios</div></div>"
            f"<div class='chips'><span>{entry.get('tool') or entry['skill_id']}</span>"
            f"<span>{entry.get('license') or 'Unknown license'}</span></div>"
            "</article>"
        )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>DeployWhisper Skills Registry</title>
    <style>
      body {{ margin: 0; background: #f5efe8; color: #1f2530; font-family: ui-sans-serif, system-ui, sans-serif; }}
      main {{ max-width: 1120px; margin: 0 auto; padding: 48px 24px 72px; }}
      h1 {{ font-size: clamp(2.8rem, 7vw, 4.8rem); line-height: 0.94; margin: 10px 0 16px; }}
      p {{ line-height: 1.7; color: #4d596b; }}
      .hero, .skill-row {{ background: rgba(255,255,255,0.92); border: 1px solid rgba(77, 89, 107, 0.12); border-radius: 22px; }}
      .hero {{ padding: 28px; margin-bottom: 22px; }}
      .catalog {{ display: grid; gap: 14px; }}
      .skill-row {{ display: grid; grid-template-columns: 1fr auto; gap: 16px; padding: 22px; }}
      .skill-row h2 {{ margin: 0 0 8px; font-size: 1.4rem; }}
      .skill-row a {{ color: #1f2530; text-decoration: none; }}
      .meta {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: #7a8598; }}
      .chips {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: start; }}
      .chips span {{ display: inline-flex; border: 1px solid rgba(77, 89, 107, 0.12); border-radius: 999px; padding: 6px 10px; font-size: 12px; color: #4d596b; }}
      .eyebrow {{ font-size: 12px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #7a8598; }}
      code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
      .links {{ margin-top: 18px; display: flex; gap: 12px; flex-wrap: wrap; }}
      .links a {{ color: #d96b3d; text-decoration: none; font-weight: 700; }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <div class="eyebrow">DeployWhisper</div>
        <h1>Skills registry</h1>
        <p>Published skill manifests, scenarios, and install-ready catalog metadata generated from the main DeployWhisper app repository.</p>
        <div class="links">
          <a href="index.json">JSON index</a>
          <a href="contributing/">Contributor guide</a>
        </div>
      </section>
      <section class="catalog">
        {''.join(rows)}
      </section>
    </main>
  </body>
</html>"""


def _render_detail(entry: dict) -> str:
    tags = "".join(f"<span>{tag}</span>" for tag in entry.get("tags", []))
    triggers = "".join(f"<li>{trigger}</li>" for trigger in entry.get("triggers", []))
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{entry['skill_id']} | DeployWhisper Skills Registry</title>
    <style>
      body {{ margin: 0; background: #f5efe8; color: #1f2530; font-family: ui-sans-serif, system-ui, sans-serif; }}
      main {{ max-width: 980px; margin: 0 auto; padding: 48px 24px 72px; }}
      .panel {{ background: rgba(255,255,255,0.92); border: 1px solid rgba(77, 89, 107, 0.12); border-radius: 22px; padding: 24px; margin-bottom: 18px; }}
      h1 {{ font-size: 2.8rem; margin: 8px 0 14px; }}
      h2 {{ font-size: 1rem; text-transform: uppercase; letter-spacing: 0.08em; color: #7a8598; }}
      p, li {{ line-height: 1.7; color: #4d596b; }}
      code {{ display: inline-flex; padding: 10px 12px; border-radius: 12px; background: #121823; color: #edf0f8; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
      .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; }}
      .meta {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: #7a8598; }}
      .tags {{ display: flex; gap: 8px; flex-wrap: wrap; }}
      .tags span {{ display: inline-flex; border: 1px solid rgba(77, 89, 107, 0.12); border-radius: 999px; padding: 6px 10px; font-size: 12px; color: #4d596b; }}
      a {{ color: #d96b3d; text-decoration: none; font-weight: 700; }}
    </style>
  </head>
  <body>
    <main>
      <section class="panel">
        <div class="meta">{entry.get('tool') or entry['skill_id']}</div>
        <h1>{entry['skill_id'].replace('-', ' ').title()}</h1>
        <p>{entry['description']}</p>
        <p><code>deploywhisper skill install {entry['skill_id']}</code></p>
        <p><a href="../../index.html">Back to catalog</a></p>
      </section>
      <section class="panel">
        <h2>Metadata</h2>
        <div class="grid">
          <div><strong>Author</strong><p>{entry['author']}</p></div>
          <div><strong>Version</strong><p>{entry['version']}</p></div>
          <div><strong>License</strong><p>{entry.get('license') or 'Unknown'}</p></div>
          <div><strong>Scenarios</strong><p>{entry['scenario_count']}</p></div>
        </div>
      </section>
      <section class="panel">
        <h2>Tags</h2>
        <div class="tags">{tags or '<span>No tags</span>'}</div>
      </section>
      <section class="panel">
        <h2>Triggers</h2>
        <ul>{triggers or '<li>No triggers declared.</li>'}</ul>
      </section>
    </main>
  </body>
</html>"""


def build_site() -> None:
    entries = _load_entries()
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / ".nojekyll").write_text("", encoding="utf-8")
    (SITE_DIR / "index.json").write_text(
        json.dumps({"skills": entries}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (SITE_DIR / "index.html").write_text(_render_index(entries), encoding="utf-8")

    for entry in entries:
        detail_dir = SITE_DIR / "skills" / entry["skill_id"]
        detail_dir.mkdir(parents=True, exist_ok=True)
        (detail_dir / "index.html").write_text(
            _render_detail(entry),
            encoding="utf-8",
        )

    contributing_dir = SITE_DIR / "contributing"
    contributing_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DOCS_DIR / "contributing" / "index.html", contributing_dir / "index.html")


if __name__ == "__main__":
    build_site()
