#!/usr/bin/env python3
"""Sinh HTML report UAT từ testcase .md (title/steps/expected/actual) + evidence (ảnh/api/mapping/count).
Usage: python3 scripts/gen_report.py <testcase.md> <evidence_root> <out.html> [feature_title]
Chỉ render API trong evidence (ApiMonitor đã lọc fetch/xhr + bỏ bootstrap)."""
import sys, os, re, json, glob, base64, html

TC_MD, EV_ROOT, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
TITLE = sys.argv[4] if len(sys.argv) > 4 else 'UAT Report'
esc = html.escape

# ---------- parse testcase .md ----------
def parse_tc(md):
    txt = open(md, encoding='utf-8').read()
    blocks = re.split(r'(?m)^#### ', txt)
    tcs = {}
    for b in blocks[1:]:
        head = b.splitlines()[0]
        m = re.match(r'(TC-[A-Z0-9]+-\d+):\s*(.*)', head)
        if not m: continue
        tcid = m.group(1)
        rest = m.group(2)
        status = 'PASS' if '✅ PASS' in rest else 'FAIL' if '❌ FAIL' in rest else 'SKIP' if '⏭️ SKIP' in rest else '—'
        title = re.split(r'\s+—\s+\*\*', rest)[0].strip()
        actual = ''
        am = re.search(r'\*\*(?:✅ PASS|❌ FAIL|⏭️ SKIP)\*\*\s*(?:—\s*)?(.*)', rest)
        if am: actual = am.group(1).strip()
        def section(name):
            mm = re.search(r'\*\*'+name+r':\*\*\s*(.*?)(?=\n\*\*[^*]+:\*\*|\Z)', b, re.S)
            return mm.group(1).strip() if mm else ''
        tcs[tcid] = {'title': title, 'status': status, 'actual': actual,
                     'steps': section('Các bước'), 'expected': section('Kết quả mong muốn')}
    return tcs

# ---------- evidence lookup ----------
def find(tc, suffix):
    for d in glob.glob(f'{EV_ROOT}/*'):
        p = f'{d}/{tc}{suffix}'
        if os.path.exists(p): return p
    return None
def imgs(tc):
    out = []
    for d in glob.glob(f'{EV_ROOT}/*'):
        out += sorted(glob.glob(f'{d}/[[]{tc}[]]*.png'))
    return out

def md_to_html(s):
    return '<br>'.join(esc(l) for l in s.splitlines() if l.strip())

def imgs_html(tc):
    h = ''
    for p in imgs(tc):
        b = base64.b64encode(open(p, 'rb').read()).decode()
        h += f'<figure><img src="data:image/png;base64,{b}"><figcaption>{esc(os.path.basename(p))}</figcaption></figure>'
    return f'<div class=shots>{h}</div>' if h else '<div class=muted>(không có ảnh)</div>'

def api_html(tc):
    f = find(tc, '_api-calls.json')
    if not f: return ''
    d = json.load(open(f)); rows = bodies = ''
    for e in d:
        u = e['url'].replace('https://admin-1sme.tpcloud.com.vn', '')
        has = e.get('responseBody') is not None
        rows += f'<tr class="{"main" if has else ""}"><td>{e["method"]}</td><td>{esc(u[:90])}{" <span class=mb>MAIN</span>" if has else ""}</td><td>{e["status"]}</td></tr>'
        if has:
            bodies += f'<details><summary>Full response — {e["method"]} {esc(u.split("?")[0])}</summary><pre>{esc(json.dumps(e["responseBody"], ensure_ascii=False, indent=2)[:6000])}</pre></details>'
    return f'<h4>API Calls (Fetch/XHR — hành động chính)</h4><table class=api><tr><th>Method</th><th>URL</th><th>Status</th></tr>{rows}</table>{bodies}'

def map_html(tc):
    f = find(tc, '_data-mapping.json')
    if not f: return ''
    d = json.load(open(f)); rows = ''
    for fl in d.get('fields', []):
        rows += f'<tr><td>{esc(str(fl.get("field","")))}</td><td>{esc(str(fl.get("apiValue","")))}</td><td>{esc(str(fl.get("uiDisplay","")))}</td><td>{"✅" if fl.get("match") else "❌"}</td></tr>'
    return f'<h4>Data Mapping (API ↔ UI — mọi cột)</h4><table class=api><tr><th>Field</th><th>API</th><th>UI</th><th>Khớp</th></tr>{rows}</table>'

def extra_json(tc):
    out = ''
    # Message EN đã verify (i18n) — render dạng danh sách
    fm = find(tc, '_messages.json')
    if fm:
        d = json.load(open(fm)); msgs = d.get('messages', [])
        items = ''.join(f'<li>{esc(m)}</li>' for m in msgs)
        out += f'<h4>Message English đã verify (không còn tiếng Việt)</h4><ul class=msgs>{items or "<li class=muted>(không có message)</li>"}</ul>'
    for kind, label in [('_search-count.json', 'Search count'), ('_filter-count.json', 'Filter count'), ('_pagination.json', 'Pagination'), ('_maxlength.json', 'Maxlength (đếm lại độ dài)'), ('_vi-leaks.json', 'i18n no-leak'), ('_api-response.json', 'API response (chi tiết)')]:
        f = find(tc, kind)
        if f and kind != '_api-response.json':
            d = json.load(open(f))
            out += '<div class=cb>' + ' · '.join(f'{esc(k)}: <b>{esc(str(v))}</b>' for k, v in d.items() if k != 'tcId') + '</div>'
    return out

tcs = parse_tc(TC_MD)
# chỉ render TC có evidence (đã chạy)
run = [t for t in tcs if imgs(t) or find(t, '_api-calls.json')]
# Thứ tự UC theo SRS: LIST → Phân trang → DETAIL → CREATE → TOGGLE → UPDATE → HISTORY → RESET → PERM
UC_RANK = {'TC-LIST': 0, 'TC-PAGE': 1, 'TC-DETAIL': 2, 'TC-CREATE': 3, 'TC-CVAL': 4, 'TC-TOGGLE': 5, 'TC-UPDATE': 6, 'TC-UVAL': 7, 'TC-HISTORY': 8, 'TC-RESET': 9, 'TC-PERM': 10, 'TC-I18N': 11, 'TC-I18NE': 12}
def rank(t):
    pre = re.sub(r'-\d+$', '', t)
    return (UC_RANK.get(pre, 99), int(re.search(r'(\d+)$', t).group(1)))
order = sorted(run, key=rank)
npass = sum(1 for t in run if tcs[t]['status'] == 'PASS')
nfail = sum(1 for t in run if tcs[t]['status'] == 'FAIL')

GROUP_NAME = {'TC-LIST': 'Danh sách', 'TC-PAGE': 'Phân trang', 'TC-DETAIL': 'Chi tiết', 'TC-CREATE': 'Tạo mới',
              'TC-CVAL': 'Validate — Tạo mới', 'TC-TOGGLE': 'Kích hoạt / Vô hiệu hóa', 'TC-UPDATE': 'Cập nhật',
              'TC-UVAL': 'Validate — Cập nhật', 'TC-HISTORY': 'Lịch sử thay đổi', 'TC-RESET': 'Reset mật khẩu', 'TC-PERM': 'Phân quyền', 'TC-I18N': 'Đa ngôn ngữ (EN)', 'TC-I18NE': 'Đa ngôn ngữ — Message (EN)'}

# Gom nhóm theo tính năng (giữ thứ tự UC)
from collections import OrderedDict
gmap = OrderedDict()
for t in order:
    gmap.setdefault(re.sub(r'-\d+$', '', t), []).append(t)

fails = [t for t in order if tcs[t]['status'] == 'FAIL']

# --- Phân cấp: Tính năng (UC) > các phần (prefix) ---
PARENTS = [
    ('UC1. Danh sách tài khoản', ['TC-LIST', 'TC-PAGE']),
    ('UC2. Chi tiết tài khoản', ['TC-DETAIL']),
    ('UC3. Tạo mới', ['TC-CREATE', 'TC-CVAL']),
    ('UC4. Kích hoạt / Vô hiệu hóa', ['TC-TOGGLE']),
    ('UC5. Cập nhật', ['TC-UPDATE', 'TC-UVAL']),
    ('UC6. Lịch sử thay đổi', ['TC-HISTORY']),
    ('UC7. Reset mật khẩu', ['TC-RESET']),
    ('Phân quyền', ['TC-PERM']),
    ('Đa ngôn ngữ (EN)', ['TC-I18N', 'TC-I18NE']),
]
# chỉ giữ parent/sub có TC thực tế
parents = []
for i, (pname, prefs) in enumerate(PARENTS):
    subs = [p for p in prefs if p in gmap]
    if subs:
        parents.append((f'uc{i}', pname, subs))

# --- Menu sidebar 2 cấp ---
nav = ''
for uid_, pname, subs in parents:
    pf = sum(1 for p in subs for t in gmap[p] if tcs[t]['status'] == 'FAIL')
    pfb = f'<span class=navfail>{pf}</span>' if pf else ''
    nav += f'<div class=navgroup><a class=navhead href="#{uid_}">{esc(pname)}{pfb}</a>'
    for p in subs:
        nf = sum(1 for t in gmap[p] if tcs[t]['status'] == 'FAIL')
        fb = f'<span class=navfail>{nf}</span>' if nf else ''
        nav += f'<a class=navsub href="#grp-{p}">{esc(GROUP_NAME.get(p, p))} <span class=navn>{len(gmap[p])}</span>{fb}</a>'
    nav += '</div>'

# --- Bảng tổng hợp FAIL ở đầu ---
if fails:
    items = ''.join(
        f'<li><a href="#{t}"><b>{t}</b> — {esc(tcs[t]["title"])}</a>'
        f'<div class=failnote>{esc(tcs[t]["actual"]) or "FAIL"}</div></li>' for t in fails)
    failbox = f'<div class=failbox><h2>❌ {len(fails)} case FAIL — bấm để tới case</h2><ul>{items}</ul></div>'
else:
    failbox = '<div class=okbox>✅ Không có case FAIL</div>'

# --- Nội dung phân cấp: UC > phần > card ---
content = ''
for uid_, pname, subs in parents:
    pall = [t for p in subs for t in gmap[p]]
    pnp = sum(1 for t in pall if tcs[t]['status'] == 'PASS')
    pnf = sum(1 for t in pall if tcs[t]['status'] == 'FAIL')
    content += f'<h1 id="{uid_}" class=uc>{esc(pname)} <span class=grpc>{pnp}✅ {pnf}❌ / {len(pall)} TC</span></h1>'
    for pre in subs:
        ts = gmap[pre]
        name = GROUP_NAME.get(pre, pre)
        nf = sum(1 for t in ts if tcs[t]['status'] == 'FAIL')
        np_ = sum(1 for t in ts if tcs[t]['status'] == 'PASS')
        content += f'<h2 id="grp-{pre}" class=grp>{esc(name)} <span class=grpc>{np_}✅ {nf}❌ / {len(ts)} TC</span></h2>'
        for t in ts:
            tc = tcs[t]; st = tc['status']; cls = st.lower()
            content += f'''<div class="card {cls}" id="{t}"><h3>{t} — {esc(tc["title"])} <span class=badge>{st}</span></h3>
<div class=meta><b>Các bước:</b><div class=box>{md_to_html(tc["steps"])}</div>
<b>Kết quả mong muốn:</b><div class=box>{md_to_html(tc["expected"])}</div>
<b>Kết quả thực tế:</b><div class=box>{esc(tc["actual"]) or ("Đúng kỳ vọng (PASS)" if st=="PASS" else st)}</div></div>
{imgs_html(t)}{extra_json(t)}{map_html(t)}{api_html(t)}</div>'''

out = f'''<!doctype html><html lang=vi><head><meta charset=utf-8><title>{esc(TITLE)}</title><style>
*{{box-sizing:border-box}} body{{font-family:Open Sans,Arial,sans-serif;margin:0;background:#f5f6f8;color:#222}}
.layout{{display:flex;align-items:flex-start}}
.side{{position:sticky;top:0;height:100vh;overflow:auto;width:250px;flex:0 0 250px;background:#1f2937;color:#e5e7eb;padding:16px 12px}}
.side h3{{margin:0 0 10px;font-size:15px;color:#fff}} .side a{{display:flex;align-items:center;gap:6px;color:#cbd5e1;text-decoration:none;padding:7px 8px;border-radius:6px;font-size:13px}}
.side a:hover{{background:#374151;color:#fff}} .navn{{margin-left:auto;background:#374151;border-radius:10px;padding:0 7px;font-size:11px}} .navfail{{margin-left:6px;background:#c0392b;color:#fff;border-radius:10px;padding:0 7px;font-size:11px}}
.navgroup{{margin:2px 0 8px}} .navhead{{font-weight:700;color:#fff !important;font-size:13px;border-top:1px solid #374151;margin-top:4px}} .navsub{{padding-left:20px !important;font-size:12px;color:#9aa6b5}}
h1.uc{{font-size:20px;margin:30px 0 4px;color:#1f2937;border-bottom:3px solid #1f2937;padding-bottom:6px;scroll-margin-top:10px}}
.main{{flex:1;padding:24px;min-width:0}} h1{{margin:0}} h4{{margin:12px 0 4px}}
.sum{{font-size:18px;margin:8px 0 16px}} .ok{{color:#1a7f37;font-weight:700}} .ng{{color:#c0392b;font-weight:700}}
.failbox{{background:#fff4f3;border:1px solid #f3b4ad;border-radius:10px;padding:12px 16px;margin:0 0 20px}} .failbox h2{{margin:0 0 8px;color:#c0392b;font-size:17px}}
.failbox ul{{margin:0;padding-left:18px}} .failbox li{{margin:6px 0}} .failbox a{{color:#c0392b;font-weight:600;text-decoration:none}} .failbox a:hover{{text-decoration:underline}} .failnote{{font-size:12px;color:#7a3b35;margin:2px 0 0}}
.okbox{{background:#e6f4ea;border:1px solid #a7d8b5;border-radius:10px;padding:12px 16px;margin:0 0 20px;color:#1a7f37;font-weight:600}}
h2.grp{{margin:26px 0 6px;border-bottom:2px solid #ccd;padding-bottom:5px;scroll-margin-top:10px}} .grpc{{font-size:13px;font-weight:400;color:#666;margin-left:8px}}
.card{{background:#fff;border-radius:10px;padding:14px;margin:12px 0;box-shadow:0 1px 4px #0001;border-left:6px solid #1a7f37;scroll-margin-top:10px}} .card.fail{{border-left-color:#c0392b}} .card.skip{{border-left-color:#999}}
.badge{{float:right;font-size:12px;padding:2px 10px;border-radius:12px;background:#e6f4ea;color:#1a7f37}} .card.fail .badge{{background:#fdecea;color:#c0392b}}
.meta{{font-size:13px;margin:6px 0}} .box{{background:#fafafa;border:1px solid #eee;border-radius:6px;padding:6px 10px;margin:3px 0 8px;white-space:normal}}
.shots{{display:flex;gap:10px;flex-wrap:wrap;margin:8px 0}} figure{{margin:0}} .shots img{{max-width:360px;border:1px solid #ddd;border-radius:6px;display:block}} figcaption{{font-size:11px;color:#666}}
.muted{{color:#999;font-size:12px}} table.api{{border-collapse:collapse;font-size:12px}} table.api td,table.api th{{border:1px solid #e0e0e0;padding:3px 8px;text-align:left;vertical-align:top}}
tr.main{{background:#f3e8ff;font-weight:600}} .mb{{background:#7c3aed;color:#fff;font-size:10px;padding:1px 5px;border-radius:8px}}
.cb{{background:#eef6ff;border:1px solid #cfe3ff;padding:7px;border-radius:6px;font-size:13px;margin:6px 0}}
details{{margin:5px 0;font-size:12px}} summary{{cursor:pointer;color:#7c3aed;font-weight:600}} pre{{background:#1e1e1e;color:#d4d4d4;padding:10px;border-radius:6px;overflow:auto;max-height:320px;font-size:11px}}</style></head>
<body><div class=layout>
<nav class=side><h3>📋 Tính năng</h3><a href="#top">⬆ Đầu trang</a>{nav}</nav>
<div class=main><h1 id=top>{esc(TITLE)}</h1>
<div class=sum>UAT · headless · <span class=ok>{npass} PASS</span> / <span class=ng>{nfail} FAIL</span> · {len(run)} TC có evidence</div>
{failbox}
{content}</div></div></body></html>'''
open(OUT, 'w', encoding='utf-8').write(out)
print(f'Report: {OUT} ({os.path.getsize(OUT)//1024} KB) — {npass} PASS / {nfail} FAIL / {len(run)} TC')
