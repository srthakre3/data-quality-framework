"""
Report Generator
Produces an HTML summary report + JSON output for all DQ check results.
"""

import json
import os
from datetime import datetime
from jinja2 import Template


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Data Quality Report — {{ run_date }}</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         background: #f5f7fa; margin: 0; padding: 2rem; color: #1a1a2e; }
  h1 { color: #2563EB; }
  .summary { display: flex; gap: 1rem; margin: 1rem 0 2rem; }
  .stat { background: white; padding: 1rem 1.5rem; border-radius: 8px;
          box-shadow: 0 1px 4px rgba(0,0,0,.08); text-align: center; }
  .stat .value { font-size: 2rem; font-weight: 700; }
  .pass { color: #16a34a; }
  .fail { color: #dc2626; }
  table { width: 100%; border-collapse: collapse; background: white;
          border-radius: 8px; overflow: hidden;
          box-shadow: 0 1px 4px rgba(0,0,0,.08); }
  th { background: #2563EB; color: white; padding: .75rem 1rem; text-align: left; }
  td { padding: .65rem 1rem; border-bottom: 1px solid #e5e7eb; }
  tr:last-child td { border-bottom: none; }
  .badge { display: inline-block; padding: .2rem .6rem; border-radius: 99px;
           font-size: .75rem; font-weight: 700; }
  .badge-pass { background: #dcfce7; color: #15803d; }
  .badge-fail { background: #fee2e2; color: #b91c1c; }
  .issues { font-size: .8rem; color: #dc2626; margin-top: .25rem; }
</style>
</head>
<body>
<h1>Data Quality Report</h1>
<p>Run: {{ run_date }} | Tables checked: {{ total_tables }}</p>
<div class="summary">
  <div class="stat"><div class="value pass">{{ passed }}</div><div>Passed</div></div>
  <div class="stat"><div class="value fail">{{ failed }}</div><div>Failed</div></div>
</div>
<table>
  <thead>
    <tr><th>Table</th><th>Check</th><th>Status</th><th>Issues</th></tr>
  </thead>
  <tbody>
    {% for r in results %}
    <tr>
      <td>{{ r.table }}</td>
      <td>{{ r.check }}</td>
      <td><span class="badge {{ 'badge-pass' if r.passed else 'badge-fail' }}">
          {{ '✅ PASS' if r.passed else '❌ FAIL' }}</span></td>
      <td>
        {% if r.issues %}
          {% for issue in r.issues %}
            <div class="issues">• {{ issue }}</div>
          {% endfor %}
        {% else %}
          —
        {% endif %}
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>
</body>
</html>
"""


def generate_report(all_results: list, output_dir: str = "reports/output") -> dict:
    """
    all_results: flat list of check result dicts
    Returns dict with paths to generated HTML and JSON files.
    """
    os.makedirs(output_dir, exist_ok=True)
    run_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    date_slug = datetime.utcnow().strftime("%Y-%m-%d")

    passed = sum(1 for r in all_results if r.get("passed"))
    failed = len(all_results) - passed
    total_tables = len({r["table"] for r in all_results})

    # HTML
    html = Template(HTML_TEMPLATE).render(
        run_date=run_date,
        total_tables=total_tables,
        passed=passed,
        failed=failed,
        results=all_results,
    )
    html_path = os.path.join(output_dir, f"dq_report_{date_slug}.html")
    with open(html_path, "w") as f:
        f.write(html)

    # JSON
    json_path = os.path.join(output_dir, f"dq_report_{date_slug}.json")
    with open(json_path, "w") as f:
        json.dump({"run_date": run_date, "results": all_results}, f, indent=2, default=str)

    print(f"📄 Report saved: {html_path}")
    print(f"📄 JSON saved:   {json_path}")
    return {"html": html_path, "json": json_path}
