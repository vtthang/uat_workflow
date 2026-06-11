#!/usr/bin/env python3
"""
Sinh HTML report UAT từ evidence/ + pipeline_report.md
Chạy: python3 scripts/generate-report.py
"""

import os, json, base64, re, html as html_mod
from pathlib import Path

# ─── CONFIG ──────────────────────────────────────────────────────────────────
EVIDENCE_ROOT = Path('evidence/uat/admin/user-management')
PIPELINE_REPORT = Path('pipeline_report.md')
OUTPUT = Path('QuanLyNguoiDung_report_2026-06-10.html')
BASE_URL = 'https://admin-1sme.tpcloud.com.vn'

# Thứ tự func-section và metadata
FUNC_CONFIG = [
    { 'key': 'list',    'label': 'Xem danh sách',         'uc': 'UC-VIEW-LIST-USER',        'slug': 'xem-danh-sach' },
    { 'key': 'detail',  'label': 'Xem chi tiết',           'uc': 'UC-VIEW-DETAIL-USER',      'slug': 'xem-chi-tiet' },
    { 'key': 'create',  'label': 'Tạo mới tài khoản',      'uc': 'UC-CREATE-USER',           'slug': 'tao-moi' },
    { 'key': 'toggle',  'label': 'Kích hoạt / Vô hiệu hóa','uc': 'UC-ACTIVE/INACTIVE-USER',  'slug': 'kich-hoat' },
    { 'key': 'update',  'label': 'Cập nhật tài khoản',     'uc': 'UC-UPDATE-USER',           'slug': 'cap-nhat' },
    { 'key': 'history', 'label': 'Lịch sử thay đổi',       'uc': 'UC-HISTORY-CHANGE-USER',   'slug': 'lich-su' },
    { 'key': 'reset',   'label': 'Reset mật khẩu',         'uc': 'UC-RESET-PWD',             'slug': 'reset-mat-khau' },
]

METHOD_COLORS = {
    'GET': '#2563eb', 'POST': '#059669',
    'PUT': '#d97706', 'PATCH': '#d97706', 'DELETE': '#dc2626',
}

# ─── PARSE PIPELINE REPORT ───────────────────────────────────────────────────
def parse_pipeline_report():
    """Trả về dict tcId -> {name, status}"""
    result = {}
    if not PIPELINE_REPORT.exists():
        return result
    text = PIPELINE_REPORT.read_text()
    for line in text.splitlines():
        m = re.match(r'\|\s*(TC-[A-Z]+-\d+)\s*\|\s*([^|]+?)\s*\|\s*(✅ PASS|❌ FAIL|⏭️ SKIP)', line)
        if m:
            tc_id, name, raw_status = m.group(1), m.group(2).strip(), m.group(3)
            if '✅' in raw_status:
                status = 'PASS'
            elif '❌' in raw_status:
                status = 'FAIL'
            else:
                status = 'SKIP'
            result[tc_id] = {'name': name, 'status': status}
    return result

# ─── EVIDENCE HELPERS ────────────────────────────────────────────────────────
def get_tc_ids_for_func(func_key):
    """Lấy danh sách TC ID từ file _api-calls.json và screenshots trong thư mục func."""
    func_dir = EVIDENCE_ROOT / func_key
    if not func_dir.exists():
        return []
    tc_ids = set()
    for f in func_dir.iterdir():
        m = re.match(r'(TC-[A-Z]+-\d+)', f.name)
        if m:
            tc_ids.add(m.group(1))
    return sorted(tc_ids, key=lambda x: int(re.search(r'\d+$', x).group()))

def get_api_calls(func_key, tc_id):
    """Đọc _api-calls.json, trả về list entries."""
    p = EVIDENCE_ROOT / func_key / f'{tc_id}_api-calls.json'
    if not p.exists():
        return []
    with open(p) as f:
        return json.load(f)

def get_screenshots(func_key, tc_id):
    """Trả về list (label, base64_str) theo thứ tự filename."""
    func_dir = EVIDENCE_ROOT / func_key
    shots = []
    for f in sorted(func_dir.iterdir()):
        if f.name.startswith(f'[{tc_id}]') and f.suffix == '.png':
            label_m = re.search(r'\]\[([^\]]+)\]', f.name)
            label = label_m.group(1) if label_m else f.stem
            data = base64.b64encode(f.read_bytes()).decode()
            shots.append((label, data))
    return shots

# ─── HTML RENDERERS ──────────────────────────────────────────────────────────
def render_screenshots(shots):
    if not shots:
        return ''
    items = ''
    for label, b64 in shots:
        items += f'''<div class="carousel-item">
      <div class="img-label">{html_mod.escape(label)}</div>
      <img src="data:image/png;base64,{b64}" onclick="openModal(this)" />
    </div>'''
    return f'<div class="section-title">📷 Screenshots ({len(shots)} ảnh)</div><div class="carousel">{items}</div>'

def is_main_api(entry):
    """Xác định entry là main API nếu có responseBody."""
    return 'responseBody' in entry

def render_api_table(calls):
    if not calls:
        return ''
    rows = ''
    for e in calls:
        method = e.get('method', '')
        url = e.get('url', '')
        status = e.get('status', '')
        is_main = is_main_api(e)

        # Tách path và query
        parts = url.split('?', 1)
        path = re.sub(r'^https?://[^/]+', '', parts[0])
        query = f'<span style="color:#94a3b8">?{html_mod.escape(parts[1])}</span>' if len(parts) > 1 else ''
        main_badge = ' <span style="background:#7c3aed;color:#fff;font-size:9px;padding:1px 5px;border-radius:3px">MAIN</span>' if is_main else ''

        m_color = METHOD_COLORS.get(method, '#475569')
        s_color = '#16a34a' if str(status).startswith('2') else '#dc2626'
        row_style = ' style="background:#f5f3ff"' if is_main else ''

        rows += f'''<tr{row_style}>
      <td class="method" style="color:{m_color}">{method}</td>
      <td>{html_mod.escape(path)}{query}{main_badge}</td>
      <td style="color:{s_color}">{status}</td>
    </tr>'''

    return f'''<div class="section-title">📡 API Calls ({len(calls)})</div>
<table><thead><tr>
  <th style="width:70px">Method</th><th>Endpoint</th><th style="width:60px">Status</th>
</tr></thead><tbody>{rows}</tbody></table>'''

def render_response_body(calls):
    """Section 5.6 — đọc responseBody từ entry isMain trong api-calls."""
    main_entries = [e for e in calls if is_main_api(e)]
    if not main_entries:
        return ''

    blocks = ''
    for e in main_entries:
        method = e.get('method', '')
        url = e.get('url', '')
        path = re.sub(r'^https?://[^/]+', '', url.split('?')[0])
        status = e.get('status', '')
        body = e.get('responseBody')

        # Đếm items nếu có
        total_items = ''
        if isinstance(body, dict):
            data = body.get('data')
            if isinstance(data, dict) and 'totalItems' in data:
                total_items = f' · {data["totalItems"]} total items'
            elif isinstance(data, str):
                total_items = ' · id: ' + data[:36]

        s_color = '#16a34a' if str(status).startswith('2') else '#dc2626'
        m_color = METHOD_COLORS.get(method, '#475569')
        json_str = html_mod.escape(json.dumps(body, ensure_ascii=False, indent=2))

        blocks += f'''<details style="margin-top:8px">
  <summary>
    <span style="color:{m_color};font-weight:700">{method}</span>
    <code style="margin:0 6px">{html_mod.escape(path)}</code>
    <span style="color:{s_color};font-weight:700">{status}</span>
    {total_items}
  </summary>
  <pre style="background:#0f172a;color:#e2e8f0;padding:10px;border-radius:6px;font-size:11px;max-height:300px;overflow:auto;margin-top:6px">{json_str}</pre>
</details>'''

    return blocks

def render_tc_card(tc_id, tc_meta, func_key):
    status = tc_meta.get('status', 'SKIP')
    name = tc_meta.get('name', tc_id)

    badge_colors = {'PASS': '#16a34a', 'FAIL': '#dc2626', 'SKIP': '#d97706'}
    color = badge_colors.get(status, '#64748b')

    shots = get_screenshots(func_key, tc_id)
    calls = get_api_calls(func_key, tc_id)

    screenshots_html = render_screenshots(shots)

    if status == 'SKIP':
        body = screenshots_html or '<div style="color:#94a3b8;font-size:12px;padding:8px">Không có evidence — TC bị skip</div>'
    else:
        api_table = render_api_table(calls)
        response_body = render_response_body(calls)
        body = screenshots_html + api_table + response_body

    return f'''<div class="tc-card" id="{tc_id}">
  <div class="tc-header">
    <span class="tc-id">{tc_id}</span>
    <span class="tc-name">{html_mod.escape(name)}</span>
    <span class="tc-badge" style="background:{color}">{status}</span>
  </div>
  <div class="tc-body">{body}</div>
</div>'''

# ─── MAIN BUILD ──────────────────────────────────────────────────────────────
def build_report():
    tc_meta = parse_pipeline_report()

    # Đếm tổng
    total_pass = sum(1 for v in tc_meta.values() if v['status'] == 'PASS')
    total_fail = sum(1 for v in tc_meta.values() if v['status'] == 'FAIL')
    total_skip = sum(1 for v in tc_meta.values() if v['status'] == 'SKIP')
    total_tc = len(tc_meta)

    total_screenshots = 0
    total_api_calls = 0
    for fc in FUNC_CONFIG:
        func_dir = EVIDENCE_ROOT / fc['key']
        if func_dir.exists():
            total_screenshots += len(list(func_dir.glob('[[]TC-*].png')))
            for jf in func_dir.glob('*_api-calls.json'):
                with open(jf) as f:
                    total_api_calls += len(json.load(f))

    # Nav links
    nav_links = ''.join(f'<a href="#func-{fc["slug"]}">{fc["label"]}</a>' for fc in FUNC_CONFIG)

    # Func sections
    sections_html = ''
    for fc in FUNC_CONFIG:
        tc_ids = get_tc_ids_for_func(fc['key'])

        # TC có trong pipeline report nhưng không có evidence (e.g. SKIP)
        func_prefix = {
            'list': 'LIST', 'detail': 'DETAIL', 'create': 'CREATE',
            'toggle': 'TOGGLE', 'update': 'UPDATE', 'history': 'HISTORY', 'reset': 'RESET',
        }[fc['key']]
        # Thêm TC từ pipeline report nếu chưa có trong evidence
        for pid in tc_meta:
            if pid.startswith(f'TC-{func_prefix}-') and pid not in tc_ids:
                tc_ids.append(pid)
        tc_ids = sorted(set(tc_ids), key=lambda x: int(re.search(r'\d+$', x).group()))

        n_pass = sum(1 for t in tc_ids if tc_meta.get(t, {}).get('status') == 'PASS')
        n_fail = sum(1 for t in tc_ids if tc_meta.get(t, {}).get('status') == 'FAIL')
        n_skip = sum(1 for t in tc_ids if tc_meta.get(t, {}).get('status') == 'SKIP')

        badges = ''
        if n_pass: badges += f'<span class="badge-pass">{n_pass} PASS</span>'
        if n_skip: badges += f'<span class="badge-skip">{n_skip} SKIP</span>'
        if n_fail: badges += f'<span class="badge-fail">{n_fail} FAIL</span>'

        cards = ''.join(render_tc_card(t, tc_meta.get(t, {'name': t, 'status': 'SKIP'}), fc['key']) for t in tc_ids)

        sections_html += f'''<section class="func-section" id="func-{fc['slug']}">
  <div class="func-header">
    <h2>{fc['label']}</h2>
    <div class="func-badges">{badges}</div>
    <span class="func-uc">{fc['uc']}</span>
  </div>
  <div class="tc-list">{cards}</div>
</section>'''

    css = '''
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:13px;background:#f8fafc;color:#1e293b}
.top-nav{position:sticky;top:0;z-index:100;background:#1e293b;color:#fff;display:flex;align-items:center;gap:4px;padding:0 16px;height:44px;flex-wrap:wrap}
.top-nav h1{font-size:14px;font-weight:700;color:#7c3aed;margin-right:12px;white-space:nowrap}
.top-nav a{color:#cbd5e1;text-decoration:none;font-size:12px;padding:4px 8px;border-radius:4px;white-space:nowrap}
.top-nav a:hover{background:#334155;color:#fff}
.report-header{background:#fff;border-bottom:1px solid #e2e8f0;padding:20px 24px}
.report-header h1{font-size:22px;font-weight:700;color:#1e293b}
.meta{color:#64748b;font-size:12px;margin:6px 0 14px}
.summary-row{display:flex;gap:10px;flex-wrap:wrap}
.summary-box{background:#f1f5f9;border-radius:8px;padding:12px 20px;min-width:90px;text-align:center}
.summary-box .num{font-size:26px;font-weight:700;color:#1e293b}
.summary-box .lbl{font-size:11px;color:#64748b;margin-top:2px}
.summary-box.pass .num{color:#16a34a}
.summary-box.skip .num{color:#d97706}
.summary-box.fail .num{color:#dc2626}
main{max-width:1200px;margin:0 auto;padding:20px 16px}
.func-section{background:#fff;border:1px solid #e2e8f0;border-radius:10px;margin-bottom:20px;overflow:hidden}
.func-header{background:#f8fafc;padding:14px 18px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #e2e8f0}
.func-header h2{font-size:15px;font-weight:700;color:#1e293b}
.func-uc{font-size:11px;color:#64748b;font-family:monospace;margin-left:auto}
.func-badges{display:flex;gap:6px}
.badge-pass{background:#dcfce7;color:#16a34a;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}
.badge-skip{background:#fef3c7;color:#d97706;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}
.badge-fail{background:#fee2e2;color:#dc2626;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}
.tc-list{padding:12px}
.tc-card{border:1px solid #e2e8f0;border-radius:8px;margin-bottom:10px;overflow:hidden}
.tc-header{display:flex;align-items:center;gap:8px;padding:8px 14px;background:#f8fafc;border-bottom:1px solid #e2e8f0}
.tc-id{font-family:monospace;font-size:12px;background:#1e293b;color:#fff;padding:2px 7px;border-radius:4px}
.tc-name{flex:1;font-size:13px;font-weight:500}
.tc-badge{color:#fff;font-size:11px;padding:2px 8px;border-radius:10px;font-weight:700}
.tc-body{padding:12px 14px}
.section-title{font-size:12px;font-weight:600;color:#475569;margin:10px 0 6px}
.carousel{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px}
.carousel-item{border:1px solid #e2e8f0;border-radius:6px;overflow:hidden;background:#f8fafc}
.img-label{font-size:10px;color:#64748b;padding:3px 6px;background:#f1f5f9;border-bottom:1px solid #e2e8f0}
.carousel-item img{max-width:280px;max-height:180px;display:block;cursor:zoom-in;object-fit:cover}
table{width:100%;border-collapse:collapse;font-size:12px;margin-bottom:8px}
th{background:#f1f5f9;padding:5px 8px;text-align:left;font-weight:600;color:#475569;border-bottom:1px solid #e2e8f0}
td{padding:4px 8px;border-bottom:1px solid #f1f5f9;vertical-align:middle}
.method{font-family:monospace;font-weight:700;font-size:11px}
details summary{cursor:pointer;font-size:12px;color:#7c3aed;font-weight:600;padding:4px 0;user-select:none}
details summary:hover{opacity:.8}
code{background:#f1f5f9;padding:1px 5px;border-radius:3px;font-family:monospace;font-size:11px}
.modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:999;cursor:pointer;align-items:center;justify-content:center}
.modal.open{display:flex}
.modal img{max-width:92vw;max-height:90vh;border-radius:6px}
.modal-close{position:absolute;top:16px;right:20px;color:#fff;font-size:24px;cursor:pointer;z-index:1000}
'''

    js = '''
function openModal(el){document.getElementById('modal-img').src=el.src;document.getElementById('modal').classList.add('open')}
function closeModal(){document.getElementById('modal').classList.remove('open')}
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal()});
document.querySelectorAll('a[href^="#"]').forEach(a=>{
  a.addEventListener('click',e=>{e.preventDefault();document.querySelector(a.getAttribute('href'))?.scrollIntoView({behavior:'smooth',block:'start'})});
});
'''

    html = f'''<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>UAT Report — Quản lý người dùng — 2026-06-10</title>
<style>{css}</style>
</head>
<body>
<nav class="top-nav"><h1>UAT — Quản lý người dùng</h1>{nav_links}</nav>
<div class="report-header">
  <h1>Báo cáo UAT — Quản lý người dùng</h1>
  <div class="meta">Môi trường: UAT ({BASE_URL}) | Portal: Admin | Ngày chạy: 2026-06-10 | Version: 2.1</div>
  <div class="summary-row">
    <div class="summary-box"><div class="num">{total_tc}</div><div class="lbl">Tổng TC</div></div>
    <div class="summary-box pass"><div class="num">{total_pass}</div><div class="lbl">PASS</div></div>
    <div class="summary-box skip"><div class="num">{total_skip}</div><div class="lbl">SKIP</div></div>
    <div class="summary-box fail"><div class="num">{total_fail}</div><div class="lbl">FAIL</div></div>
    <div class="summary-box"><div class="num">{total_screenshots}</div><div class="lbl">Screenshots</div></div>
    <div class="summary-box"><div class="num">{total_api_calls}</div><div class="lbl">API Calls</div></div>
  </div>
</div>
<main>{sections_html}</main>
<div class="modal" id="modal" onclick="closeModal()">
  <span class="modal-close" onclick="closeModal()">✕</span>
  <img id="modal-img" src="" alt=""/>
</div>
<script>{js}</script>
</body>
</html>'''

    OUTPUT.write_text(html, encoding='utf-8')
    print(f'✅ Report saved: {OUTPUT} ({OUTPUT.stat().st_size // 1024}KB)')
    print(f'   {total_tc} TCs | {total_pass} PASS | {total_fail} FAIL | {total_skip} SKIP')
    print(f'   {total_screenshots} screenshots | {total_api_calls} API calls')

if __name__ == '__main__':
    os.chdir(Path(__file__).parent.parent)
    build_report()
