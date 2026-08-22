#!/usr/bin/env python3
"""
Build the OA Docket dashboard HTML from data/dashboard_status.json.

This is the "dynamic" half of the dashboard: all company status, findings,
and dates live in dashboard_status.json (data), not in this script
(presentation). To update the dashboard, edit the JSON and re-run this
script - never hand-edit the generated HTML.

Reads:
  data/dashboard_status.json  - per-company status data (source of truth)
  scripts/dashboard_template.html - page shell with {{PLACEHOLDER}} markers
  scripts/fonts_inline.css    - embedded @font-face data URIs

Writes:
  dashboard/oa_dashboard.html - the finished, publishable page

After running this, publish dashboard/oa_dashboard.html as a Claude
Artifact using the SAME artifact URL each time (see README) so the
dashboard's public link never changes.
"""
import json

STATUS_COLOR_VARS = {
    "failed": "var(--status-failed)",
    "pending": "var(--status-pending)",
    "momentum": "var(--status-momentum)",
    "none": "var(--status-none)",
}
STATUS_BG_VARS = {
    "failed": "var(--status-failed-bg)",
    "pending": "var(--status-pending-bg)",
    "momentum": "var(--status-momentum-bg)",
    "none": "var(--status-none-bg)",
}


def card_html(c, status_labels):
    color = STATUS_COLOR_VARS[c["status"]]
    bg = STATUS_BG_VARS[c["status"]]
    label = status_labels[c["status"]].upper()
    depth_html = '<span class="depth-tag">Deep dive</span>' if c.get("deep_dive") else '<span></span>'
    also_html = f'<div class="also-note">{c["also_note"]}</div>' if c.get("also_note") else ''
    new_html = '<span class="new-badge">New</span>' if c.get("new") else ''
    return f'''<div class="card" style="--stripe:{color};">
      <div class="card-top">
        <h3>{c["name"]}</h3>
        <div style="display:flex; flex-direction:column; align-items:flex-end; gap:0.3rem;">
          <span class="chip" style="color:{color}; background:{bg}; border-color:{color}44;">{label}</span>
          {new_html}
        </div>
      </div>
      <div class="asset-row"><span class="asset-code">{c["asset"]}</span>{c["mechanism"]}</div>
      <div class="finding">{c["finding"]}</div>
      {also_html}
      <div class="card-foot">
        <span class="event-date">{c["date_label"]}</span>
        {depth_html}
      </div>
    </div>'''


def section_html(status_key, data):
    companies = [c for c in data["companies"] if c["status"] == status_key]
    if not companies:
        return ""
    color = STATUS_COLOR_VARS[status_key]
    label = data["status_labels"][status_key]
    subtext = data["section_subtext"].get(status_key, "")
    total = len(data["companies"])
    cards = "\n".join(card_html(c, data["status_labels"]) for c in companies)
    return f'''<div class="section">
    <div class="section-head">
      <div class="section-stripe" style="background:{color};"></div>
      <h2>{label}</h2>
      <span class="count">{len(companies)} of {total}</span>
    </div>
    <p class="subtext">{subtext}</p>
    <div class="grid">
      {cards}
    </div>
  </div>'''


def new_candidates_html(data):
    items = data.get("new_candidates", [])
    if not items:
        return ""
    rows = "\n".join(
        f'''<div class="card" style="--stripe:var(--accent);">
      <div class="card-top">
        <h3>{it["name"]}</h3>
        <span class="new-badge">New — not yet tracked</span>
      </div>
      <div class="asset-row"><span class="asset-code">{it.get("asset","—")}</span>{it.get("note","")}</div>
      <div class="card-foot"><span class="event-date">{it.get("found_date","")}</span></div>
    </div>''' for it in items
    )
    return f'''<div class="section">
    <div class="section-head">
      <div class="section-stripe" style="background:var(--accent);"></div>
      <h2>New Candidates — Not Yet Tracked</h2>
      <span class="count">{len(items)} found</span>
    </div>
    <p class="subtext">Surfaced by the weekly ClinicalTrials.gov pull but not yet added to the tracked shortlist above. Review and promote manually — new entries are never auto-added.</p>
    <div class="grid">
      {rows}
    </div>
  </div>'''


def main():
    with open("data/dashboard_status.json") as f:
        data = json.load(f)
    with open("scripts/dashboard_template.html") as f:
        template = f.read()
    with open("scripts/fonts_inline.css") as f:
        fonts_css = f.read()

    total = len(data["companies"])
    counts = {k: len([c for c in data["companies"] if c["status"] == k]) for k in data["status_order"]}
    positive_active = counts.get("momentum", 0) + counts.get("pending", 0)
    positive_pct = round(positive_active / total * 100) if total else 0
    seg_html = "\n".join(
        f'<div class="dist-seg" style="width:{(counts[k]/total*100) if total else 0:.1f}%; background:{STATUS_COLOR_VARS[k]};"></div>'
        for k in data["status_order"] if counts[k] > 0
    )
    legend_html = "\n".join(
        f'<span class="item"><span class="dot" style="background:{STATUS_COLOR_VARS[k]};"></span>'
        f'{data["status_labels"][k]} &nbsp;<b>{counts[k]}</b></span>'
        for k in data["status_order"] if counts[k] > 0
    )

    sections_html = "\n\n".join(section_html(k, data) for k in data["status_order"])

    html = template
    html = html.replace("/* FONTS_PLACEHOLDER */", fonts_css)
    html = html.replace("{{TOTAL_COMPANIES}}", str(total))
    html = html.replace("{{LAST_REFRESHED}}", data["last_refreshed"])
    html = html.replace("{{HERO_NUM}}", str(positive_pct))
    html = html.replace(
        "{{HERO_CAP}}",
        f"of tracked programs ({positive_active} of {total}) are active or showing positive data"
    )
    html = html.replace("{{DIST_SEGMENTS}}", seg_html)
    html = html.replace("{{DIST_LEGEND}}", legend_html)
    html = html.replace("{{SECTIONS}}", sections_html)
    html = html.replace("{{NEW_CANDIDATES_SECTION}}", new_candidates_html(data))

    import os
    os.makedirs("dashboard", exist_ok=True)
    with open("dashboard/oa_dashboard.html", "w") as f:
        f.write(html)

    print(f"Wrote dashboard/oa_dashboard.html ({len(html)} chars, {total} companies, "
          f"{len(data.get('new_candidates', []))} new candidates)")


if __name__ == "__main__":
    main()
