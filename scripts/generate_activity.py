import argparse
import calendar as cal
import datetime as dt
import html
import json
import os
from pathlib import Path
import subprocess
import urllib.request

def fetch(cli, year):
    query = '''query($from:DateTime!,$to:DateTime!) { user(login:"Pictus08") { contributionsCollection(from:$from,to:$to) { contributionCalendar { totalContributions weeks { contributionDays { contributionCount contributionLevel date } } } } } }'''
    variables = {"from": f"{year}-01-01T00:00:00Z", "to": f"{year}-12-31T23:59:59Z"}
    if cli:
        result = subprocess.run(["gh", "api", "graphql", "--input", "-"], input=json.dumps({"query": query, "variables": variables}), capture_output=True, text=True, encoding="utf-8", check=True)
        data = json.loads(result.stdout)
    else:
        request = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": query, "variables": variables}).encode(), headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"], "Content-Type": "application/json", "User-Agent": "Pictus08-profile"})
        with urllib.request.urlopen(request) as response:
            data = json.load(response)
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def render(data, year, lang):
    es = lang == "es"
    today = dt.datetime.now(dt.timezone.utc).date()
    days = {d["date"]: d for w in data["weeks"] for d in w["contributionDays"] if d["date"].startswith(str(year)) and d["date"] <= today.isoformat()}
    total = sum(d["contributionCount"] for d in days.values())
    active = sum(d["contributionCount"] > 0 for d in days.values())
    peak = max((d["contributionCount"] for d in days.values()), default=0)
    title = f'REGISTRO ANUAL · {year}' if es else f'ANNUAL ACTIVITY · {year}'
    subtitle = 'Ingeniería civil · Código · Automatización' if es else 'Civil engineering · Code · Automation'
    labels = ['contribuciones', 'días activos', 'máximo en un día'] if es else ['contributions', 'active days', 'most in one day']
    colors = {"NONE":"#1b2935", "FIRST_QUARTILE":"#174e52", "SECOND_QUARTILE":"#227c80", "THIRD_QUARTILE":"#31b6ae", "FOURTH_QUARTILE":"#81f4d0"}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="920" height="400" viewBox="0 0 920 400" role="img" aria-labelledby="title desc"><title id="title">{title}</title><desc id="desc">{total} {labels[0]}; {year}-01-01 — {year}-12-31</desc>', '<defs><pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#1b2b39" stroke-width="0.5"/></pattern></defs>', '<rect x="1" y="1" width="918" height="398" rx="18" fill="#0d1520" stroke="#29404f"/><rect x="1" y="1" width="918" height="398" rx="18" fill="url(#grid)"/><rect x="28" y="28" width="4" height="48" rx="2" fill="#81f4d0"/>']
    def text(x, y, value, size=12, color='#98afbf', weight=400):
        out.append(f'<text x="{x}" y="{y}" font-family="Segoe UI,Arial,sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}">{html.escape(str(value))}</text>')
    text(46,44,title,12,'#81f4d0',700)
    text(46,71,subtitle,21,'#e6edf3',600)
    text(778,43,'PICTUS08',13,'#81f4d0',700)
    for x, value, label in zip([46,346,646],[total,active,peak],labels):
        text(x,125,value,32,'#e6edf3',700)
        text(x,147,label,13)
    first = dt.date(year,1,1)
    origin = first - dt.timedelta(days=(first.weekday()+1)%7)
    months = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'] if es else list(cal.month_abbr)[1:]
    for month, label in enumerate(months,1):
        index = (dt.date(year,month,1)-origin).days//7
        text(58+index*15.2,180,label,11)
    for row,label in [(1,'L' if es else 'M'),(3,'X' if es else 'W'),(5,'V' if es else 'F')]:
        text(32,204+row*17,label,10)
    date=first
    while date.year==year:
        index=(date-origin).days//7
        row=(date.weekday()+1)%7
        day=days.get(date.isoformat(),{})
        future=date>today
        color='#101923' if future else colors[day.get('contributionLevel','NONE')]
        tip=f'{date}: ' + (('fecha futura' if es else 'future date') if future else f'{day.get("contributionCount",0)} {labels[0]}')
        out.append(f'<rect x="{58+index*15.2:.1f}" y="{193+row*17}" width="12" height="13" rx="3" fill="{color}" stroke="{"#26313e" if future else color}" stroke-width="0.5"><title>{html.escape(tip)}</title></rect>')
        date+=dt.timedelta(days=1)
    text(46,337,f'01/01/{year} — 31/12/{year}',12,'#e6edf3')
    text(46,359,('Datos consultados: ' if es else 'Data retrieved: ')+today.isoformat(),11)
    text(46,380,'Solo actividad disponible en la API de GitHub.' if es else 'Activity available through the GitHub API only.',11)
    text(640,342,'Menos' if es else 'Less',11)
    for i,color in enumerate(colors.values()):
        out.append(f'<rect x="{682+i*18}" y="330" width="13" height="13" rx="3" fill="{color}"/>')
    text(779,342,'Más' if es else 'More',11)
    text(640,370,'Contorno vacío: días futuros' if es else 'Empty outline: future dates',11)
    out.append('</svg>')
    return '\n'.join(out)+'\n'

def render_compact(data, year, lang):
    es = lang == 'es'
    today = dt.datetime.now(dt.timezone.utc).date()
    days = {d['date']: d for w in data['weeks'] for d in w['contributionDays']}
    colors = {'NONE':'#161b22','FIRST_QUARTILE':'#0e4429','SECOND_QUARTILE':'#006d32','THIRD_QUARTILE':'#26a641','FOURTH_QUARTILE':'#39d353'}
    first = dt.date(year,1,1)
    origin = first-dt.timedelta(days=(first.weekday()+1)%7)
    title = f'Actividad anual {year}' if es else f'Annual activity {year}'
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="920" height="190" viewBox="0 0 920 190" role="img" aria-labelledby="title"><title id="title">{title}</title>', '<rect x="1" y="1" width="918" height="188" rx="7" fill="#0d1117" stroke="#30363d"/>']
    def text(x,y,value,size=12,color='#9198a1'):
        out.append(f'<text x="{x}" y="{y}" font-family="Segoe UI,Arial,sans-serif" font-size="{size}" fill="{color}">{html.escape(str(value))}</text>')
    months = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'] if es else list(cal.month_abbr)[1:]
    for month,label in enumerate(months,1):
        week=(dt.date(year,month,1)-origin).days//7
        text(60+week*15.4,30,label,12,'#c9d1d9')
    for row,label in [(1,'Lun' if es else 'Mon'),(3,'Mié' if es else 'Wed'),(5,'Vie' if es else 'Fri')]:
        text(16,51+row*15,label,11,'#c9d1d9')
    date=first
    while date.year==year:
        week=(date-origin).days//7
        row=(date.weekday()+1)%7
        d=days.get(date.isoformat(),{})
        future=date>today
        color='#0d1117' if future else colors[d.get('contributionLevel','NONE')]
        tip=f'{date}: '+(('fecha futura' if es else 'future date') if future else f'{d.get("contributionCount",0)} '+('contribuciones' if es else 'contributions'))
        out.append(f'<rect x="{60+week*15.4:.1f}" y="{41+row*15}" width="12" height="12" rx="2" fill="{color}" stroke="{"#21262d" if future else color}" stroke-width="0.5"><title>{html.escape(tip)}</title></rect>')
        date+=dt.timedelta(days=1)
    text(60,169,f'{year} · '+('Enero — diciembre' if es else 'January — December'),11)
    text(660,169,'Menos' if es else 'Less',11)
    for i,color in enumerate(colors.values()):
        out.append(f'<rect x="{701+i*17}" y="158" width="12" height="12" rx="2" fill="{color}"/>')
    text(794,169,'Más' if es else 'More',11)
    out.append('</svg>')
    return '\n'.join(out)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--gh-cli',action='store_true')
    p.add_argument('--output',default='assets')
    p.add_argument('--year',type=int,default=dt.datetime.now(dt.timezone.utc).year)
    args=p.parse_args()
    data=fetch(args.gh_cli,args.year)
    target=Path(args.output)
    target.mkdir(parents=True,exist_ok=True)
    for lang in ('es','en'):
        file=target/f'activity-{lang}.svg'
        file.write_text(render_compact(data,args.year,lang),encoding='utf-8')
        print(file)
    print('Annual contributions:',data['totalContributions'])
