"""Build a static GitHub Pages site for the skills registry."""

from __future__ import annotations

from html import escape
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
        payload["skill_body"] = _load_skill_body(skill_dir / "skill.md")
        payload["tool_label"] = str(payload.get("tool") or payload["skill_id"])
        entries.append(payload)
    return entries


def _load_skill_body(path: Path) -> str:
    raw_text = path.read_text(encoding="utf-8")
    stripped = raw_text.strip()
    if stripped.startswith("---"):
        parts = stripped.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return stripped


def _render_guidance_html(markdown_text: str) -> str:
    rows: list[str] = []
    in_list = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            rows.append("</ul>")
            in_list = False

    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            close_list()
            continue
        if line.startswith("### "):
            close_list()
            rows.append(f"<h3>{escape(line[4:])}</h3>")
            continue
        if line.startswith("## "):
            close_list()
            rows.append(f"<h2>{escape(line[3:])}</h2>")
            continue
        if line.startswith("- "):
            if not in_list:
                rows.append("<ul>")
                in_list = True
            rows.append(f"<li>{escape(line[2:])}</li>")
            continue
        close_list()
        rows.append(f"<p>{escape(line)}</p>")

    close_list()
    return "".join(rows)


def _render_index(entries: list[dict]) -> str:
    tool_options = "".join(
        f"<option value=\"{tool}\">{tool.replace('-', ' ').title()}</option>"
        for tool in sorted({str(entry.get("tool") or entry["skill_id"]) for entry in entries})
    )
    catalog_json = json.dumps(entries, sort_keys=True)
    rows = []
    for entry in entries:
        tool_label = str(entry.get("tool") or entry["skill_id"])
        rows.append(
            "<article class='skill-row' "
            f"data-skill-title=\"{entry['skill_id'].replace('-', ' ').title()}\" "
            f"data-skill-search=\"{entry['skill_id']} {entry['author']} {entry['description']} {' '.join(entry.get('tags', []))}\" "
            f"data-skill-tool=\"{tool_label}\" "
            f"data-skill-scenarios=\"{entry['scenario_count']}\">"
            "<div class='skill-main'>"
            "<div class='skill-kicker-row'>"
            f"<div class='skill-kicker'>{tool_label.replace('-', ' ').title()}</div>"
            "<div class='skill-badges'>"
            + (
                "<span class='badge badge-official'>Official</span>"
                if entry["author"] == "DeployWhisper"
                else "<span class='badge'>Community</span>"
            )
            + f"<span class='badge'>v{entry['version']}</span></div></div>"
            f"<h2><a href='skills/{entry['skill_id']}/'>{entry['skill_id'].replace('-', ' ').title()}</a></h2>"
            f"<p>{entry['description']}</p>"
            f"<div class='meta'>{entry['author']} · v{entry['version']} · {entry['scenario_count']} scenarios</div>"
            "<div class='chips'>"
            + "".join(f"<span>{tag}</span>" for tag in entry.get("tags", [])[:4])
            + "</div></div>"
            "<div class='skill-side'>"
            f"<div class='metric'><strong>{entry['scenario_count']}</strong><span>Scenarios</span></div>"
            f"<div class='metric'><strong>{entry.get('license') or 'Unknown'}</strong><span>License</span></div>"
            "<button class='copy-button' "
            f"data-command='deploywhisper skill install {entry['skill_id']}'>Copy install</button>"
            f"<a class='install-link' href='skills/{entry['skill_id']}/'>View skill</a></div>"
            "</article>"
        )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>DeployWhisper Skills Registry</title>
    <link rel="canonical" href="https://deploywhisper.github.io/skills-registry/" />
    <style>
      :root {{
        --bg: #f5efe8;
        --panel: rgba(255,255,255,0.93);
        --line: rgba(77, 89, 107, 0.12);
        --text: #1f2530;
        --muted: #4d596b;
        --muted-soft: #7a8598;
        --accent: #d96b3d;
        --accent-soft: rgba(217, 107, 61, 0.12);
      }}
      body {{
        margin: 0;
        background:
          radial-gradient(circle at top right, rgba(217, 107, 61, 0.18), transparent 26%),
          linear-gradient(180deg, #fbf7f1 0%, var(--bg) 48%, #eee6d9 100%);
        color: var(--text);
        font-family: ui-sans-serif, system-ui, sans-serif;
      }}
      main {{ max-width: 1180px; margin: 0 auto; padding: 48px 24px 72px; }}
      h1 {{ font-size: clamp(3rem, 8vw, 5.5rem); line-height: 0.9; margin: 10px 0 16px; letter-spacing: -0.05em; }}
      p {{ line-height: 1.7; color: var(--muted); }}
      .hero, .skill-row, .controls {{ background: var(--panel); border: 1px solid var(--line); border-radius: 24px; box-shadow: 0 18px 44px rgba(28, 34, 44, 0.08); }}
      .hero {{ padding: 32px; margin-bottom: 20px; }}
      .hero-grid {{ display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.8fr); gap: 24px; align-items: end; }}
      .hero-stats {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
      .hero-stat {{ border: 1px solid var(--line); border-radius: 18px; padding: 16px; background: rgba(255,255,255,0.72); }}
      .hero-stat strong {{ display: block; font-size: 28px; }}
      .hero-stat span {{ display: block; margin-top: 4px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted-soft); }}
      .catalog {{ display: grid; gap: 14px; }}
      .skill-row {{ display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(200px, auto); gap: 16px; padding: 22px; transition: transform 160ms ease, border-color 160ms ease; }}
      .skill-row:hover {{ transform: translateY(-2px); border-color: rgba(217, 107, 61, 0.24); }}
      .skill-kicker {{ font-size: 12px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted-soft); }}
      .skill-kicker-row {{ display: flex; gap: 10px; align-items: center; justify-content: space-between; flex-wrap: wrap; }}
      .skill-row h2 {{ margin: 10px 0 8px; font-size: 1.45rem; letter-spacing: -0.03em; }}
      .skill-row a {{ color: var(--text); text-decoration: none; }}
      .meta {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted-soft); }}
      .chips {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: start; margin-top: 14px; }}
      .chips span {{ display: inline-flex; border: 1px solid var(--line); border-radius: 999px; padding: 6px 10px; font-size: 12px; color: var(--muted); background: rgba(255,255,255,0.78); }}
      .skill-badges {{ display: flex; gap: 8px; flex-wrap: wrap; }}
      .badge {{ display: inline-flex; border-radius: 999px; padding: 6px 10px; font-size: 11px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; background: rgba(255,255,255,0.76); border: 1px solid var(--line); color: var(--muted); }}
      .badge-official {{ background: var(--accent-soft); border-color: rgba(217,107,61,0.22); color: var(--accent); }}
      .skill-side {{ display: grid; align-content: start; gap: 12px; }}
      .metric {{ border: 1px solid var(--line); border-radius: 18px; padding: 14px; background: rgba(255,255,255,0.74); }}
      .metric strong {{ display: block; font-size: 22px; color: var(--text); }}
      .metric span {{ display: block; margin-top: 4px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted-soft); }}
      .eyebrow {{ font-size: 12px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted-soft); }}
      .links {{ margin-top: 18px; display: flex; gap: 12px; flex-wrap: wrap; }}
      .links a, .install-link {{ color: var(--accent); text-decoration: none; font-weight: 700; }}
      .copy-button {{
        border: 1px solid rgba(217,107,61,0.24);
        border-radius: 14px;
        padding: 10px 12px;
        font: inherit;
        font-weight: 700;
        color: var(--accent);
        background: rgba(255,255,255,0.92);
        cursor: pointer;
      }}
      .copy-button.copied {{ color: #0f7d52; border-color: rgba(15,125,82,0.24); }}
      .controls {{ display: grid; grid-template-columns: minmax(0, 2fr) minmax(220px, 1fr); gap: 14px; padding: 18px; margin-bottom: 18px; }}
      .controls label {{ display: grid; gap: 6px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted-soft); }}
      .controls input, .controls select {{
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 12px 14px;
        font: inherit;
        color: var(--text);
        background: rgba(255,255,255,0.9);
      }}
      .controls-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
      .empty {{ padding: 22px; border: 1px dashed var(--line); border-radius: 18px; background: rgba(255,255,255,0.58); }}
      .summary {{ margin-top: 12px; color: var(--muted-soft); font-size: 13px; }}
      @media (max-width: 860px) {{
        .hero-grid, .controls, .controls-row, .skill-row {{ grid-template-columns: 1fr; }}
        .hero-stats {{ grid-template-columns: 1fr 1fr; }}
      }}
      @media (max-width: 640px) {{
        .hero, .controls, .skill-row {{ padding: 20px; }}
        .hero-stats {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <div class="hero-grid">
          <div>
            <div class="eyebrow">DeployWhisper</div>
            <h1>Skills registry</h1>
            <p>Published skill manifests, scenarios, and install-ready catalog metadata generated from the main DeployWhisper app repository.</p>
            <div class="links">
              <a href="index.json">JSON index</a>
              <a href="contributing/">Contributor guide</a>
            </div>
            <div class="summary">Use the search and tool filter below to scan the catalog quickly before you install.</div>
          </div>
          <div class="hero-stats">
            <div class="hero-stat"><strong>{len(entries)}</strong><span>Published skills</span></div>
            <div class="hero-stat"><strong>{sum(entry['scenario_count'] for entry in entries)}</strong><span>Total scenarios</span></div>
            <div class="hero-stat"><strong>{len(sorted({entry['author'] for entry in entries}))}</strong><span>Authors</span></div>
            <div class="hero-stat"><strong>{len(sorted({str(entry.get('tool') or entry['skill_id']) for entry in entries}))}</strong><span>Tool families</span></div>
          </div>
        </div>
      </section>
      <section class="controls">
        <label>Search
          <input id="catalog-search" type="search" placeholder="Search skills, authors, or tags" />
        </label>
        <div class="controls-row">
          <label>Tool
            <select id="catalog-tool">
              <option value="">All tools</option>
              {tool_options}
            </select>
          </label>
          <label>Sort
            <select id="catalog-sort">
              <option value="title">Name</option>
              <option value="scenarios">Scenario count</option>
            </select>
          </label>
        </div>
      </section>
      <section class="catalog">
        {''.join(rows)}
      </section>
      <template id="catalog-empty">
        <div class="empty">No skills match the current search and filter combination.</div>
      </template>
    </main>
    <script type="application/json" id="catalog-data">{catalog_json}</script>
    <script>
      (() => {{
        if (window.location.pathname.endsWith('/index.html')) {{
          const cleanPath = window.location.pathname.replace(/index\\.html$/, '');
          window.history.replaceState(null, '', cleanPath + window.location.search + window.location.hash);
        }}
        const rows = Array.from(document.querySelectorAll('.skill-row'));
        const searchInput = document.getElementById('catalog-search');
        const toolSelect = document.getElementById('catalog-tool');
        const sortSelect = document.getElementById('catalog-sort');
        const catalog = document.querySelector('.catalog');
        const emptyTemplate = document.getElementById('catalog-empty');
        const copyButtons = Array.from(document.querySelectorAll('.copy-button'));

        const render = () => {{
          const search = (searchInput.value || '').trim().toLowerCase();
          const tool = (toolSelect.value || '').trim().toLowerCase();
          const filtered = rows.filter((row) => {{
            const haystack = (row.dataset.skillSearch || '').toLowerCase();
            const rowTool = (row.dataset.skillTool || '').toLowerCase();
            const matchesSearch = !search || haystack.includes(search);
            const matchesTool = !tool || rowTool === tool;
            row.style.display = matchesSearch && matchesTool ? '' : 'none';
            return matchesSearch && matchesTool;
          }});

          filtered.sort((left, right) => {{
            if (sortSelect.value === 'scenarios') {{
              return Number(right.dataset.skillScenarios || '0') - Number(left.dataset.skillScenarios || '0');
            }}
            return (left.dataset.skillTitle || '').localeCompare(right.dataset.skillTitle || '');
          }});

          filtered.forEach((row) => catalog.appendChild(row));
          const currentEmpty = catalog.querySelector('.empty');
          if (currentEmpty) currentEmpty.remove();
          if (filtered.length === 0) {{
            catalog.appendChild(emptyTemplate.content.cloneNode(true));
          }}
        }};

        searchInput.addEventListener('input', render);
        toolSelect.addEventListener('change', render);
        sortSelect.addEventListener('change', render);
        copyButtons.forEach((button) => {{
          button.addEventListener('click', async () => {{
            const command = button.dataset.command || '';
            try {{
              await navigator.clipboard.writeText(command);
              button.textContent = 'Copied';
              button.classList.add('copied');
              window.setTimeout(() => {{
                button.textContent = 'Copy install';
                button.classList.remove('copied');
              }}, 1400);
            }} catch (error) {{
              button.textContent = 'Copy failed';
              window.setTimeout(() => {{
                button.textContent = 'Copy install';
              }}, 1400);
            }}
          }});
        }});
        render();
      }})();
    </script>
  </body>
</html>"""


def _render_detail(entry: dict) -> str:
    tags = "".join(f"<span>{tag}</span>" for tag in entry.get("tags", []))
    triggers = "".join(f"<li>{trigger}</li>" for trigger in entry.get("triggers", []))
    content_patterns = "".join(
        f"<li>{pattern}</li>" for pattern in entry.get("trigger_content_patterns", [])
    )
    guidance_html = _render_guidance_html(str(entry.get("skill_body") or ""))
    author_badge = (
        "<span class='badge badge-official'>Official</span>"
        if entry["author"] == "DeployWhisper"
        else "<span class='badge'>Community</span>"
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{entry['skill_id']} | DeployWhisper Skills Registry</title>
    <link rel="canonical" href="https://deploywhisper.github.io/skills-registry/skills/{entry['skill_id']}/" />
    <style>
      :root {{
        --bg: #f5efe8;
        --panel: rgba(255,255,255,0.93);
        --line: rgba(77, 89, 107, 0.12);
        --text: #1f2530;
        --muted: #4d596b;
        --muted-soft: #7a8598;
        --accent: #d96b3d;
        --accent-soft: rgba(217,107,61,0.12);
      }}
      body {{
        margin: 0;
        background:
          radial-gradient(circle at top right, rgba(217,107,61,0.18), transparent 26%),
          linear-gradient(180deg, #fbf7f1 0%, var(--bg) 48%, #eee6d9 100%);
        color: var(--text);
        font-family: ui-sans-serif, system-ui, sans-serif;
      }}
      main {{ max-width: 1040px; margin: 0 auto; padding: 48px 24px 72px; }}
      .panel {{ background: var(--panel); border: 1px solid var(--line); border-radius: 22px; padding: 24px; margin-bottom: 18px; box-shadow: 0 18px 44px rgba(28,34,44,0.08); }}
      h1 {{ font-size: clamp(2.7rem, 6vw, 4rem); margin: 8px 0 14px; letter-spacing: -0.05em; }}
      h2 {{ font-size: 1rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted-soft); }}
      h3 {{ font-size: 1.1rem; margin-top: 18px; }}
      p, li {{ line-height: 1.7; color: var(--muted); }}
      code {{ display: inline-flex; padding: 10px 12px; border-radius: 12px; background: #121823; color: #edf0f8; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
      .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; }}
      .meta {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted-soft); }}
      .tags {{ display: flex; gap: 8px; flex-wrap: wrap; }}
      .tags span, .badge {{ display: inline-flex; border: 1px solid var(--line); border-radius: 999px; padding: 6px 10px; font-size: 12px; color: var(--muted); background: rgba(255,255,255,0.78); }}
      .badge-official {{ background: var(--accent-soft); border-color: rgba(217,107,61,0.24); color: var(--accent); font-weight: 700; }}
      a {{ color: var(--accent); text-decoration: none; font-weight: 700; }}
      .command-row {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
      .copy-button {{
        border: 1px solid rgba(217,107,61,0.24);
        border-radius: 14px;
        padding: 10px 12px;
        font: inherit;
        font-weight: 700;
        color: var(--accent);
        background: rgba(255,255,255,0.92);
        cursor: pointer;
      }}
      .copy-button.copied {{ color: #0f7d52; border-color: rgba(15,125,82,0.24); }}
      .hero-badges {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }}
      .help-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }}
      .help-grid ol {{ margin: 0; padding-left: 18px; }}
      .guidance h2 {{ margin-top: 24px; }}
      .guidance ul {{ padding-left: 20px; }}
    </style>
  </head>
  <body>
    <main>
      <section class="panel">
        <div class="meta">{entry.get('tool') or entry['skill_id']}</div>
        <div class="hero-badges">{author_badge}<span class="badge">v{entry['version']}</span><span class="badge">{entry['scenario_count']} scenarios</span></div>
        <h1>{entry['skill_id'].replace('-', ' ').title()}</h1>
        <p>{entry['description']}</p>
        <div class="command-row">
          <code id="install-command">deploywhisper skill install {entry['skill_id']}</code>
          <button class="copy-button" id="copy-install">Copy install command</button>
        </div>
        <p><a href="../../index.html">Back to catalog</a></p>
      </section>
      <section class="panel">
        <h2>How to use this skill</h2>
        <div class="help-grid">
          <div>
            <strong>1. Install it locally</strong>
            <p>Use the install command above from any DeployWhisper app checkout that has the installer enabled.</p>
          </div>
          <div>
            <strong>2. Run analysis on matching artifacts</strong>
            <p>This skill activates when files or content patterns below are detected during analysis.</p>
          </div>
          <div>
            <strong>3. Verify behavior</strong>
            <p>Published registry data currently includes <strong>{entry['scenario_count']}</strong> deterministic scenario{'' if entry['scenario_count'] == 1 else 's'} for this skill.</p>
          </div>
        </div>
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
      <section class="panel">
        <h2>Content patterns</h2>
        <ul>{content_patterns or '<li>No content pattern hints declared.</li>'}</ul>
      </section>
      <section class="panel guidance">
        <h2>Guidance excerpt</h2>
        {guidance_html}
      </section>
    </main>
    <script>
      (() => {{
        if (window.location.pathname.endsWith('/index.html')) {{
          const cleanPath = window.location.pathname.replace(/index\\.html$/, '');
          window.history.replaceState(null, '', cleanPath + window.location.search + window.location.hash);
        }}
        const button = document.getElementById('copy-install');
        const command = document.getElementById('install-command');
        if (button && command) {{
          button.addEventListener('click', async () => {{
            try {{
              await navigator.clipboard.writeText(command.textContent || '');
              button.textContent = 'Copied';
              button.classList.add('copied');
            }} catch (error) {{
              button.textContent = 'Copy failed';
            }}
            window.setTimeout(() => {{
              button.textContent = 'Copy install command';
              button.classList.remove('copied');
            }}, 1500);
          }});
        }}
      }})();
    </script>
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
