"""
네이버용 txt 파일을 티스토리 스타일 HTML로 변환
- 깔끔한 카드 디자인
- 섹션별 색상 구분
- 클릭 가능한 링크 버튼
- [SVG: filename.svg] 마커 → 인라인 SVG 자동 삽입
"""
from pathlib import Path

IMAGES_DIR = Path("C:/Users/WIN10/.antigravity/posts/images")

def _embed_svg(filename):
    """SVG 파일을 읽어 인라인 HTML로 반환"""
    path = IMAGES_DIR / filename
    if path.exists():
        svg_code = path.read_text(encoding="utf-8")
        return (
            f'<div style="margin:20px 0;text-align:center;border-radius:14px;overflow:hidden;">'
            f'{svg_code}</div>'
        )
    return ""

def txt_to_tistory_html(title, content):
    lines = content.strip().split("\n")

    html_sections = []
    current_section_title = ""
    current_section_lines = []

    def flush_section():
        nonlocal current_section_title, current_section_lines
        if not current_section_lines and not current_section_title:
            return
        block = render_section(current_section_title, current_section_lines)
        if block:
            html_sections.append(block)
        current_section_title = ""
        current_section_lines = []

    def render_section(sec_title, sec_lines):
        # 빈 섹션 제외
        body_lines = [l for l in sec_lines if l.strip() and not l.strip().startswith("━")]
        if not body_lines and not sec_title:
            return ""

        rows = []
        for line in body_lines:
            line = line.strip()
            if not line:
                continue

            # 링크 줄 → 버튼
            if "→ https://" in line or "→ http://" in line:
                parts = line.split("→ ", 1)
                label = parts[0].strip().lstrip("👉").strip()
                url = parts[1].strip()
                rows.append(
                    f'<a href="{url}" target="_blank" rel="noopener" '
                    f'style="display:inline-block;margin:4px 6px 4px 0;padding:8px 18px;'
                    f'background:#3C5AFD;color:#fff;border-radius:6px;font-size:14px;'
                    f'text-decoration:none;font-weight:600;">{label} →</a>'
                )
            # 전화번호 줄
            elif "☎" in line:
                rows.append(f'<p style="margin:6px 0;font-size:15px;">{line}</p>')
            # 체크리스트 항목
            elif line.startswith("✅") or line.startswith("→"):
                text = line.lstrip("✅→").strip()
                rows.append(
                    f'<li style="margin:5px 0;font-size:15px;color:#333;">{text}</li>'
                )
            # 표/리스트 항목 (└ 스타일)
            elif line.startswith("💰") or line.startswith("🏠") or line.startswith("💼") \
                    or line.startswith("👶") or line.startswith("🧒") or line.startswith("🏥") \
                    or line.startswith("🚌") or line.startswith("🚆") or line.startswith("🏛️") \
                    or line.startswith("🌿") or line.startswith("💈") or line.startswith("🎓") \
                    or line.startswith("🏡") or line.startswith("💍") or line.startswith("🤰") \
                    or line.startswith("🏘") or line.startswith("🚗") or line.startswith("✈️") \
                    or line.startswith("🌾") or line.startswith("🍼") or line.startswith("💳"):
                rows.append(
                    f'<p style="margin:5px 0;font-size:15px;padding-left:8px;'
                    f'border-left:3px solid #3C5AFD;color:#222;">{line}</p>'
                )
            # 📦 박스 제목
            elif line.startswith("📦"):
                text = line.lstrip("📦").strip()
                rows.append(
                    f'<p style="margin:12px 0 6px;font-size:16px;font-weight:700;color:#3C5AFD;">'
                    f'📦 {text}</p>'
                )
            # 해시태그 줄
            elif line.startswith("#") and " #" in line:
                tags = line.split()
                tag_html = " ".join(
                    f'<span style="display:inline-block;margin:3px;padding:4px 10px;'
                    f'background:#EEF2FF;color:#3C5AFD;border-radius:20px;font-size:13px;">{t}</span>'
                    for t in tags if t.startswith("#")
                )
                rows.append(f'<div style="margin-top:12px;">{tag_html}</div>')
            # 일반 텍스트
            elif len(line) > 1:
                rows.append(f'<p style="margin:6px 0;font-size:15px;color:#444;">{line}</p>')

        if not rows:
            return ""

        # li 태그들을 ul로 묶기
        merged = []
        in_ul = False
        for r in rows:
            if r.startswith("<li"):
                if not in_ul:
                    merged.append('<ul style="padding-left:20px;margin:8px 0;">')
                    in_ul = True
                merged.append(r)
            else:
                if in_ul:
                    merged.append("</ul>")
                    in_ul = False
                merged.append(r)
        if in_ul:
            merged.append("</ul>")

        body_html = "\n".join(merged)

        if sec_title:
            return f"""
<div style="margin:24px 0;padding:20px 24px;background:#F8F9FF;border-radius:12px;border-left:5px solid #3C5AFD;">
  <h3 style="margin:0 0 14px;font-size:17px;color:#1a1a2e;font-weight:700;">{sec_title}</h3>
  {body_html}
</div>"""
        else:
            return f"""
<div style="margin:16px 0;">
  {body_html}
</div>"""

    # 본문 파싱
    intro_lines = []
    parsing_intro = True

    for line in lines:
        raw = line.strip()

        # 구분선
        if raw.startswith("━" * 5):
            flush_section()
            parsing_intro = False
            continue

        # 섹션 제목 (📌, 📊)
        if raw.startswith("📌") or raw.startswith("📊"):
            flush_section()
            current_section_title = raw.lstrip("📌📊").strip()
            parsing_intro = False
            continue

        # [SVG: filename.svg] 마커 → 인라인 SVG 삽입
        if raw.startswith("[SVG:") and raw.endswith("]"):
            flush_section()
            filename = raw[5:-1].strip()
            svg_html = _embed_svg(filename)
            if svg_html:
                html_sections.append(svg_html)
            parsing_intro = False
            continue

        # 이미지 안내줄 스킵
        if raw.startswith("[ 이미지") or raw.startswith("> 🖼️"):
            continue

        if parsing_intro and raw and not raw.startswith("━"):
            intro_lines.append(raw)
        else:
            current_section_lines.append(line)

    flush_section()

    # 인트로 블록
    intro_html = ""
    if intro_lines:
        intro_texts = []
        for l in intro_lines:
            if l.strip():
                intro_texts.append(
                    f'<p style="margin:8px 0;font-size:16px;color:#333;line-height:1.7;">{l}</p>'
                )
        intro_html = f"""
<div style="margin:0 0 24px;padding:20px 24px;background:#EEF2FF;border-radius:12px;">
  {"".join(intro_texts)}
</div>"""

    # 전체 HTML 조합
    full_html = f"""<div style="font-family:'Noto Sans KR',sans-serif;max-width:720px;margin:0 auto;color:#222;">

<h2 style="font-size:24px;font-weight:800;color:#1a1a2e;margin:0 0 20px;line-height:1.4;">
  {title}
</h2>

{intro_html}

{"".join(html_sections)}

<div style="margin-top:32px;padding:16px 20px;background:#1a1a2e;border-radius:10px;text-align:center;">
  <p style="color:#aaa;font-size:13px;margin:0 0 8px;">이 글이 도움이 됐다면 구독&amp;공감 눌러주세요! 💙</p>
  <p style="color:#fff;font-size:14px;margin:0;">매달 최신 정부혜택 정보를 업데이트합니다 🔔</p>
</div>

</div>"""

    return full_html


def make_tistory_cardnews_html(t: dict, today_str: str, banner_svg: str = "") -> str:
    """
    티스토리 전용 카드뉴스 스타일 HTML 생성.
    네이버 버전(정보 정리형)과 완전히 다른 스타일:
    - 스토리텔링 hook
    - Q&A 카드
    - Before/After 비교
    - 핵심 요약 카드
    """
    color  = t.get("color", "#3C5AFD")
    emoji  = t.get("emoji", "💡")
    tid    = t.get("id", "")
    title  = t.get("title_ko", tid)
    sub    = t.get("subtitle", "")
    intro  = t.get("intro", "")
    tips   = t.get("tips", [])
    how_to = t.get("how_to", [])
    docs   = t.get("documents", [])
    regions= t.get("regions", [])
    apply  = t.get("apply", "https://www.bokjiro.go.kr")
    target = t.get("target", "")
    top_pick_name, top_pick_desc = t.get("top_pick", ("", ""))
    tags   = " ".join(t.get("tags", []))

    # ── 헤더 카드 ──────────────────────────────
    header = f"""
<div style="background:linear-gradient(135deg,{color}dd,{color}88);
            color:#fff;padding:36px 28px;border-radius:18px;
            text-align:center;margin-bottom:20px;box-shadow:0 4px 20px {color}44;">
  <div style="font-size:56px;margin-bottom:8px">{emoji}</div>
  <h2 style="margin:0 0 8px;font-size:24px;font-weight:900">{title}</h2>
  <p style="margin:0;font-size:15px;opacity:.9">{sub}</p>
  <p style="margin:10px 0 0;font-size:12px;opacity:.7;background:rgba(0,0,0,.15);
            display:inline-block;padding:4px 12px;border-radius:20px;">
    🐋 고래가 공식 자료로 확인한 정보  ·  {today_str} 기준
  </p>
</div>"""

    # ── 배너 SVG (있으면 삽입) ──────────────────
    banner_block = ""
    if banner_svg:
        banner_block = (
            f'<div style="margin:0 0 20px;border-radius:14px;overflow:hidden;">'
            f'{banner_svg}</div>'
        )

    # ── hook 카드 (스토리텔링) ──────────────────
    hook_lines = [l for l in intro.strip().splitlines() if l.strip()]
    hook_text  = "<br>".join(hook_lines[:3])
    hook = f"""
<div style="background:#fffbeb;border-left:5px solid #f59e0b;
            padding:20px 22px;border-radius:0 12px 12px 0;margin-bottom:20px;">
  <p style="margin:0 0 6px;font-weight:700;color:#92400e;">🐋 고래의 한마디</p>
  <p style="margin:0;font-size:15px;line-height:1.7;color:#1c1c1c;">{hook_text}</p>
</div>"""

    # ── 대상 독자 배지 ──────────────────────────
    target_badge = ""
    if target:
        target_badge = f"""
<div style="display:inline-block;background:{color};color:#fff;
            padding:6px 16px;border-radius:20px;font-size:13px;
            font-weight:700;margin-bottom:20px;">👥 {target} 필독!</div>"""

    # ── Q&A 카드 (how_to 단계를 Q&A 형식으로) ──
    qa_colors = ["#e8f4fd","#f0fdf4","#fdf4ff","#fff7ed","#f0f9ff"]
    qa_border = ["#3b82f6","#22c55e","#a855f7","#f97316","#0ea5e9"]
    qa_cards  = ""
    for i, step in enumerate(how_to[:5]):
        bg  = qa_colors[i % len(qa_colors)]
        bd  = qa_border[i % len(qa_border)]
        qa_cards += f"""
<div style="background:{bg};border-left:4px solid {bd};
            padding:16px 18px;border-radius:0 10px 10px 0;margin-bottom:12px;">
  <p style="margin:0 0 4px;font-weight:700;color:{bd};font-size:13px;">STEP {i+1}</p>
  <p style="margin:0;font-size:14px;line-height:1.6;color:#1c1c1c;">{step}</p>
</div>"""

    # ── Before / After 비교 카드 ────────────────
    ba_rows = ""
    for region, amount in regions[:6]:
        star = "⭐" in region
        bg   = f"{color}18" if star else "#f8fafc"
        ba_rows += f"""
  <div style="display:flex;align-items:center;padding:10px 14px;
              background:{bg};border-radius:8px;margin-bottom:6px;">
    <span style="flex:1;font-size:14px;font-weight:{'700' if star else '400'};
                 color:#1e293b;">{region.replace(' ⭐','')}{' ⭐' if star else ''}</span>
    <span style="font-size:13px;color:{color};font-weight:700;">{amount}</span>
  </div>"""

    compare_title = "유형별 한눈에 비교" if target else "지역별 얼마나 받을까?"
    compare = f"""
<div style="margin-bottom:20px;">
  <h3 style="font-size:17px;font-weight:800;color:#1e293b;
             margin:0 0 12px;padding-left:10px;
             border-left:4px solid {color};">📊 {compare_title}</h3>
  {ba_rows}
  <div style="margin-top:10px;padding:12px 16px;background:{color};
              border-radius:10px;color:#fff;font-size:14px;font-weight:700;">
    🏆 {top_pick_name} — {top_pick_desc}
  </div>
</div>"""

    # ── 준비서류 체크리스트 ──────────────────────
    doc_items = "".join(
        f'<li style="margin-bottom:6px;font-size:14px;">📄 {d}</li>'
        for d in docs
    )
    checklist = f"""
<div style="background:#f8fafc;border-radius:12px;padding:18px 20px;margin-bottom:20px;">
  <p style="margin:0 0 10px;font-weight:700;font-size:15px;color:#1e293b;">
    ✅ 이것만 준비하면 돼요!
  </p>
  <ul style="margin:0;padding-left:18px;list-style:none;">{doc_items}</ul>
</div>"""

    # ── 꿀팁 카드 ───────────────────────────────
    tip_items = "".join(
        f'<div style="display:flex;gap:10px;margin-bottom:10px;">'
        f'<span style="font-size:20px">💡</span>'
        f'<p style="margin:0;font-size:14px;line-height:1.6;color:#1c1c1c;">{tip}</p>'
        f'</div>'
        for tip in tips[:4]
    )
    tips_block = f"""
<div style="margin-bottom:20px;">
  <h3 style="font-size:17px;font-weight:800;color:#1e293b;
             margin:0 0 14px;padding-left:10px;
             border-left:4px solid #f59e0b;">💡 몰랐으면 손해! 꿀팁</h3>
  {tip_items}
</div>"""

    # ── 핵심 요약 카드 ───────────────────────────
    summary = f"""
<div style="background:linear-gradient(135deg,#1e293b,#334155);
            color:#fff;border-radius:16px;padding:24px;margin-bottom:20px;">
  <p style="margin:0 0 14px;font-size:16px;font-weight:800;">
    🐋 고래의 핵심 요약
  </p>
  <p style="margin:0 0 8px;font-size:14px;opacity:.9;">
    {emoji} <strong>{title}</strong> — {sub}
  </p>
  <p style="margin:0 0 8px;font-size:13px;opacity:.8;">
    ✅ {len(how_to)}단계면 신청 완료  ·  서류 {len(docs)}가지만 준비
  </p>
  <p style="margin:0;font-size:13px;opacity:.7;">
    ⚠️ 지원 조건·금액은 변동될 수 있으니 신청 전 공식 사이트 확인 필수!
  </p>
</div>"""

    # ── CTA / 신청 버튼 ─────────────────────────
    cta = f"""
<div style="text-align:center;margin-bottom:24px;">
  <a href="{apply}" target="_blank" rel="noopener"
     style="display:inline-block;background:{color};color:#fff;
            padding:14px 32px;border-radius:30px;font-size:15px;
            font-weight:700;text-decoration:none;box-shadow:0 4px 14px {color}55;">
    👉 지금 바로 신청하기
  </a>
</div>"""

    # ── 구독 CTA ────────────────────────────────
    subscribe = """
<div style="background:#f0f9ff;border:2px solid #bae6fd;border-radius:14px;
            padding:20px;text-align:center;margin-bottom:20px;">
  <p style="margin:0 0 6px;font-size:16px;font-weight:700;color:#0369a1;">
    🐋 매주 이득 되는 정보 받아보세요!
  </p>
  <p style="margin:0;font-size:13px;color:#475569;">
    구독 🔔 하시면 매주 월요일 지역별 혜택, 목요일 축제 정보 자동 알림이에요
  </p>
</div>"""

    # ── 해시태그 ────────────────────────────────
    tag_html = f'<p style="font-size:13px;color:#94a3b8;margin:0;">{tags}</p>'

    full_html = f"""<div style="max-width:680px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,'맑은 고딕',sans-serif;padding:16px;">
{header}
{banner_block}
{hook}
{target_badge}
{compare}
<h3 style="font-size:17px;font-weight:800;color:#1e293b;
           margin:0 0 14px;padding-left:10px;
           border-left:4px solid {color};">📋 신청 방법 (총 {len(how_to)}단계)</h3>
{qa_cards}
{checklist}
{tips_block}
{summary}
{cta}
{subscribe}
{tag_html}
</div>"""

    return full_html


if __name__ == "__main__":
    # 테스트
    test_content = """테스트 제목입니다

━━━━━━━━━━━━━━━━━
📌 테스트 섹션
━━━━━━━━━━━━━━━━━

📦 지원 내용
✅ 월 100만 원
✅ 신청: 복지로

👉 복지로 바로가기 → https://www.bokjiro.go.kr

#테스트 #정부혜택
"""
    html = txt_to_tistory_html("테스트", test_content)
    with open("test_output.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("test_output.html 생성 완료")
