from pathlib import Path

html = Path('deploy/index.html').read_text(encoding='utf-8')

replacements = [
    # CSS 변수
    ('--bg:#0f0c29;--bg2:#1a1744;--card:#1e1b4b;--card2:#252266;',
     '--bg:#f0fdf4;--bg2:#dcfce7;--card:#ffffff;--card2:#f0fdf4;'),
    ('--accent:#7c3aed;--accent2:#a855f7;--green:#10b981;--red:#ef4444;',
     '--accent:#16a34a;--accent2:#22c55e;--green:#16a34a;--red:#ef4444;'),
    ('--text:#f1f5f9;--text2:#94a3b8;--border:#2d2a5e;',
     '--text:#1a2e1a;--text2:#4d7a4d;--border:#bbf7d0;'),

    # 헤더/바텀내비 그라디언트
    ('background:linear-gradient(135deg,#0f0c29,#302b63)', 'background:linear-gradient(135deg,#16a34a,#059669)'),
    ('background:linear-gradient(90deg,#a855f7,#ec4899)', 'background:linear-gradient(90deg,#16a34a,#059669)'),

    # 설치 배너
    ('background:linear-gradient(135deg,rgba(124,58,237,.3),rgba(168,85,247,.2));border:1px solid rgba(124,58,237,.4)',
     'background:linear-gradient(135deg,rgba(22,163,74,.15),rgba(34,197,94,.1));border:1px solid rgba(22,163,74,.35)'),

    # 버튼 그라디언트
    ('background:linear-gradient(135deg,#1e3a5f,#1a56db)', 'background:linear-gradient(135deg,#16a34a,#22c55e)'),
    ('background:linear-gradient(135deg,#0f2460,#1a3a8f)', 'background:linear-gradient(135deg,#bbf7d0,#d1fae5)'),

    # rgba 보라/퍼플
    ('rgba(124,58,237,.15)', 'rgba(22,163,74,.15)'),
    ('rgba(124,58,237,.1)', 'rgba(22,163,74,.1)'),
    ('rgba(168,85,247,.2)', 'rgba(34,197,94,.15)'),
    ('rgba(124,58,237,.4)', 'rgba(22,163,74,.35)'),
    ('rgba(124,58,237,.3)', 'rgba(22,163,74,.2)'),
    ('rgba(124,58,237', 'rgba(22,163,74'),

    # progress bar, hover
    ('background:rgba(255,255,255,.1);border-radius:99px', 'background:rgba(22,163,74,.15);border-radius:99px'),
    ('background:rgba(255,255,255,.05)', 'background:rgba(22,163,74,.08)'),
    ('background:rgba(255,255,255,.1)}', 'background:rgba(22,163,74,.12)}'),

    # nav active
    ('.nav-item.active{color:var(--accent2)}', '.nav-item.active{color:var(--accent)}'),

    # dot 색
    ('background:#ec4899', 'background:#22c55e'),

    # 팁 박스
    ('background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.25)',
     'background:rgba(22,163,74,.08);border:1px solid rgba(22,163,74,.2)'),

    # 하드코딩 hex
    ('#a855f7', '#22c55e'),
    ('#7c3aed', '#16a34a'),
    ('#302b63', '#d1fae5'),
    ('#0f0c29', '#f0fdf4'),
    ('#1a1744', '#dcfce7'),
    ('#1e1b4b', '#ffffff'),
    ('#252266', '#f0fdf4'),
    ('#2d2a5e', '#bbf7d0'),
    ('#ec4899', '#16a34a'),
    ('#f1f5f9', '#1a2e1a'),
    ('#94a3b8', '#4d7a4d'),

    # 메타 theme-color
    ('content="#a855f7"', 'content="#16a34a"'),
    ('content="#0f0c29"', 'content="#f0fdf4"'),
]

count = 0
for old, new in replacements:
    if old in html:
        html = html.replace(old, new)
        count += 1
        print(f'OK: {old[:70]}')

Path('deploy/index.html').write_text(html, encoding='utf-8')
print(f'\n총 {count}개 교체 완료')
