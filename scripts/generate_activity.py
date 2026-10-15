import argparse
import datetime as dt
import html
import json
import os
from pathlib import Path
import subprocess
import urllib.request

QUERY = '''query { user(login: "Pictus08") { contributionsCollection { contributionCalendar { totalContributions weeks { contributionDays { contributionCount contributionLevel date } } } } } }'''

def fetch(cli):
    if cli:
        response = subprocess.run(["gh", "api", "graphql", "-f", "query=" + QUERY], capture_output=True, text=True, encoding="utf-8", check=True)
        data = json.loads(response.stdout)
    else:
        request = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": QUERY}).encode(), headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"], "Content-Type": "application/json", "User-Agent": "Pictus08-profile"})
        with urllib.request.urlopen(request) as response:
            data = json.load(response)
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def render(calendar, lang):
    es = lang == "es"
    days = [d for week in calendar["weeks"] for d in week["contributionDays"]]
    active = sum(d["contributionCount"] > 0 for d in days)
    peak = max(d["contributionCount"] for d in days)
    colors = {"NONE": "#1b2935", "FIRST_QUARTILE": "#174e52", "SECOND_QUARTILE": "#227c80", "THIRD_QUARTILE": "#31b6ae", "FOURTH_QUARTILE": "#81f4d0"}
    title = "ACTIVIDAD EN GITHUB" if es else "GITHUB ACTIVITY"
    subtitle = "Ingeniería civil · Código · Automatización" if es else "Civil engineering · Code · Automation"
    labels = ["contribuciones", "días activos", "máximo en un día"] if es else ["contributions", "active days", "most in one day"]
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="920" height="366" viewBox="0 0 920 366" role="img" aria-labelledby="title desc">', f'<title id="title">{title} · Pictus08</title>', '<desc id="desc">' + html.escape(f'{calendar["totalContributions"]} {labels[0]}; {days[0]["date"]} — {days[-1]["date"]}') + '</desc>', '<defs><pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M 24 0 L 0 0 0 24" fill="none" stroke="#1b2b39" stroke-width="0.5"/></pattern></defs>', '<rect x="1" y="1" width="918" height="364" rx="18" fill="#0d1520" stroke="#29404f"/>', '<rect x="1" y="1" width="918" height="364" rx="18" fill="url(#grid)"/>', '<rect x="28" y="28" width="4" height="48" rx="2" fill="#81f4d0"/>']
    def text(x, y, value, size=13, color="#98afbf", weight=400):
        out.append(f'<text x="{x}" y="{y}" font-family="Segoe UI,Arial,sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}">{html.escape(str(value))}</text>')
    text(46, 44, title, 12, "#81f4d0", 700)
    text(46, 71, subtitle, 21, "#e6edf3", 600)
    text(778, 43, "PICTUS08", 13, "#81f4d0", 700)
    values = [calendar["totalContributions"], active, peak]
    for x, value, label in zip([46, 346, 646], values, labels):
        text(x, 125, value, 32, "#e6edf3", 700)
        text(x, 147, label)
    for i, week in enumerate(calendar["weeks"]):
        for day in week["contributionDays"]:
            date = dt.date.fromisoformat(day["date"])
            row = (date.weekday() + 1) % 7
            x, y = 46 + i * 15.6, 183 + row * 17
            color = colors[day["contributionLevel"]]
            tooltip = html.escape(f'{day["date"]}: {day["contributionCount"]} {labels[0]}')
            out.append(f'<rect x="{x:.1f}" y="{y}" width="12" height="13" rx="3" fill="{color}"><title>{tooltip}</title></rect>')
    text(46, 321, days[0]["date"] + " — " + days[-1]["date"], 12)
    text(46, 345, "Datos de GitHub · Actualización diaria" if es else "GitHub data · Updated daily", 11)
    text(680, 335, "Menos" if es else "Less", 11)
    for i, color in enumerate(colors.values()):
        out.append(f'<rect x="{722+i*18}" y="323" width="13" height="13" rx="3" fill="{color}"/>')
    text(819, 335, "Más" if es else "More", 11)
    out.append('</svg>')
    return '\n'.join(out) + '\n'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gh-cli", action="store_true")
    parser.add_argument("--output", default="assets")
    args = parser.parse_args()
    calendar = fetch(args.gh_cli)
    target = Path(args.output)
    target.mkdir(parents=True, exist_ok=True)
    for lang in ("es", "en"):
        path = target / f"activity-{lang}.svg"
        path.write_text(render(calendar, lang), encoding="utf-8")
        print(path)
