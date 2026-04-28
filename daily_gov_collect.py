"""
매일 새벽 1시 자동 실행:
정부 공식 사이트 수집 → 업그레이드 블로그 글 생성 → SVG 이미지 자동 제작 → 네이버 업로드
"""
import sys
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR        = Path("C:/Users/WIN10/.antigravity")
POSTS_DIR       = BASE_DIR / "posts"
IMAGES_DIR      = POSTS_DIR / "images"
BLOG_IMAGES_DIR = BASE_DIR / "blog_images"
LOG_DIR         = BASE_DIR / "logs"

for d in [POSTS_DIR, IMAGES_DIR, BLOG_IMAGES_DIR, LOG_DIR]:
    d.mkdir(exist_ok=True)

try:
    logging.basicConfig(
        filename=LOG_DIR / "daily_gov_collect.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8"
    )
except Exception:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

CARD_COLORS = ["#6366f1", "#ec4899", "#10b981", "#f59e0b",
               "#ef4444", "#3b82f6", "#8b5cf6", "#06b6d4"]

SOURCES = [
    {"name": "정책브리핑",     "url": "https://www.korea.kr/news/policyNewsList.do",
     "title_sel": ".news-list li a, .list-type02 li a"},
    {"name": "복지로 새소식",  "url": "https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do",
     "title_sel": ".board-list td a, .list-wrap li a"},
    {"name": "정부24",         "url": "https://www.gov.kr/portal/rcvfvrSvc/main/nonLogin",
     "title_sel": ".service-list li a, .card-title"},
]

FALLBACK = [
    {"title": "소상공인 경영안정 지원",    "amount": "최대 200만원",  "link": "https://www.sbiz.or.kr/sup/main.do",                                          "source": "소진공",     "emoji": "💳"},
    {"title": "청년 월세 한시 특별지원",   "amount": "월 최대 20만원","link": "https://apply.lh.or.kr/lhapply/apply/wt/wrtApply/selectWrtApplyIngList.do",   "source": "LH청약센터", "emoji": "🏠"},
    {"title": "부모급여 신청",             "amount": "월 최대 100만원","link": "https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?welfareInfoId=WI202300000005", "source": "복지로", "emoji": "👶"},
    {"title": "청년도약계좌",              "amount": "월 최대 70만원","link": "https://ylaccount.kinfa.or.kr/main",                                          "source": "서민금융진흥원","emoji": "💰"},
    {"title": "에너지바우처 신청",         "amount": "최대 연 30만원","link": "https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?welfareInfoId=WI202000001450", "source": "복지로", "emoji": "⛽"},
]

EMOJIS = ["💰", "🏠", "👶", "🎓", "⛽", "💳", "🌱", "🏥", "🚌", "💼"]


# ══════════════════════════════════════════════
# SVG 이미지 자동 생성
# ══════════════════════════════════════════════

def make_banner_svg(today_str, month_str, count):
    """날짜별 메인 배너 자동 생성"""
    return f"""<svg width="800" height="380" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0f172a"/>
      <stop offset="100%" style="stop-color:#1e3a8a"/>
    </linearGradient>
    <linearGradient id="gold" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#fbbf24"/>
      <stop offset="100%" style="stop-color:#f59e0b"/>
    </linearGradient>
    <linearGradient id="btn" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#f59e0b"/>
      <stop offset="100%" style="stop-color:#ef4444"/>
    </linearGradient>
  </defs>
  <rect width="800" height="380" fill="url(#bg)"/>
  <circle cx="700" cy="60"  r="130" fill="#6366f1" opacity="0.07"/>
  <circle cx="80"  cy="320" r="110" fill="#ec4899" opacity="0.06"/>
  <circle cx="400" cy="380" r="200" fill="#3b82f6" opacity="0.04"/>

  <!-- 날짜 뱃지 -->
  <rect x="270" y="32" width="260" height="34" rx="17" fill="url(#gold)"/>
  <text x="400" y="54" font-family="Arial" font-size="14" fill="#1e3a8a" text-anchor="middle" font-weight="bold">📅 {today_str} 최신 업데이트</text>

  <!-- 메인 타이틀 -->
  <text x="400" y="125" font-family="Arial" font-size="38" fill="white" text-anchor="middle" font-weight="bold">정부혜택 총정리 💰</text>
  <text x="400" y="175" font-family="Arial" font-size="22" fill="#fbbf24" text-anchor="middle" font-weight="bold">{month_str} 놓치면 손해!</text>

  <!-- 서브 문구 -->
  <text x="400" y="218" font-family="Arial" font-size="15" fill="white" text-anchor="middle" opacity="0.85">몰라서 못 받는 지원금, 오늘 다 챙겨가세요</text>

  <!-- 구분선 -->
  <rect x="120" y="235" width="560" height="1.5" rx="1" fill="white" opacity="0.15"/>

  <!-- 통계 3개 -->
  <text x="180" y="272" font-family="Arial" font-size="13" fill="white" text-anchor="middle" opacity="0.8">오늘 소식</text>
  <text x="180" y="298" font-family="Arial" font-size="28" fill="#fbbf24" text-anchor="middle" font-weight="bold">{count}건</text>

  <text x="400" y="272" font-family="Arial" font-size="13" fill="white" text-anchor="middle" opacity="0.8">신청 가능</text>
  <text x="400" y="298" font-family="Arial" font-size="28" fill="#86efac" text-anchor="middle" font-weight="bold">지금!</text>

  <text x="620" y="272" font-family="Arial" font-size="13" fill="white" text-anchor="middle" opacity="0.8">매일 업데이트</text>
  <text x="620" y="298" font-family="Arial" font-size="28" fill="#c4b5fd" text-anchor="middle" font-weight="bold">무료</text>

  <!-- CTA 버튼 -->
  <rect x="250" y="320" width="300" height="46" rx="23" fill="url(#btn)"/>
  <text x="400" y="349" font-family="Arial" font-size="17" fill="white" text-anchor="middle" font-weight="bold">👉 내 혜택 바로 확인하기</text>

  <text x="400" y="375" font-family="Arial" font-size="11" fill="white" text-anchor="middle" opacity="0.35">구독하고 매일 혜택 받아가세요 🔔</text>
</svg>"""


def make_benefit_cards_svg(articles):
    """혜택 카드 SVG 자동 생성"""
    items  = articles[:5]
    card_h = 72
    total  = 60 + len(items) * (card_h + 12) + 20
    cards  = ""
    y      = 60

    for i, a in enumerate(items):
        color = CARD_COLORS[i % len(CARD_COLORS)]
        emoji = a.get("emoji", EMOJIS[i % len(EMOJIS)])
        title = a.get("title", "")[:22]
        amt   = a.get("amount", "신청 가능")
        src   = a.get("source", "정부")

        cards += f"""
  <rect x="20" y="{y}" width="760" height="{card_h}" rx="12" fill="{color}" opacity="0.08"/>
  <rect x="20" y="{y}" width="6"   height="{card_h}" rx="3"  fill="{color}"/>
  <text x="48"  y="{y+24}" font-family="Arial" font-size="20">{emoji}</text>
  <text x="80"  y="{y+24}" font-family="Arial" font-size="16" fill="#1e293b" font-weight="bold">{title}</text>
  <text x="80"  y="{y+48}" font-family="Arial" font-size="13" fill="#64748b">📌 출처: {src}</text>
  <rect x="590" y="{y+16}" width="160" height="34" rx="17" fill="{color}"/>
  <text x="670"  y="{y+38}" font-family="Arial" font-size="13" fill="white" text-anchor="middle" font-weight="bold">💰 {amt}</text>"""
        y += card_h + 12

    return f"""<svg width="800" height="{total}" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="{total}" fill="#f8faff" rx="14"/>
  <rect x="2" y="2" width="796" height="{total-4}" rx="12" fill="none" stroke="#c7d2fe" stroke-width="2"/>
  <text x="400" y="38" font-family="Arial" font-size="17" fill="#4f46e5" text-anchor="middle" font-weight="bold">🎁 오늘의 정부혜택 한눈에 보기</text>
  {cards}
</svg>"""


def make_cta_svg():
    """신청 유도 CTA 배너 SVG"""
    return f"""<svg width="800" height="160" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="cta" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#2563eb"/>
      <stop offset="100%" style="stop-color:#7c3aed"/>
    </linearGradient>
  </defs>
  <rect width="800" height="160" fill="url(#cta)" rx="16"/>
  <circle cx="720" cy="30"  r="80" fill="white" opacity="0.05"/>
  <circle cx="60"  cy="140" r="70" fill="white" opacity="0.05"/>

  <text x="400" y="52"  font-family="Arial" font-size="20" fill="white" text-anchor="middle" font-weight="bold">💡 오늘 바로 신청하세요!</text>
  <text x="400" y="84"  font-family="Arial" font-size="14" fill="white" text-anchor="middle" opacity="0.9">혜택은 신청해야만 받을 수 있어요 · 기간 지나면 소급 안 돼요!</text>

  <rect x="80"  y="104" width="180" height="38" rx="19" fill="white" opacity="0.15"/>
  <text x="170" y="127" font-family="Arial" font-size="13" fill="white" text-anchor="middle" font-weight="bold">🏛️ 정부24 신청</text>

  <rect x="310" y="104" width="180" height="38" rx="19" fill="white" opacity="0.15"/>
  <text x="400" y="127" font-family="Arial" font-size="13" fill="white" text-anchor="middle" font-weight="bold">💰 복지로 신청</text>

  <rect x="540" y="104" width="180" height="38" rx="19" fill="white" opacity="0.15"/>
  <text x="630" y="127" font-family="Arial" font-size="13" fill="white" text-anchor="middle" font-weight="bold">📞 1345 전화문의</text>
</svg>"""


def make_hashtag_svg():
    """알록달록 해시태그 SVG"""
    tags = [
        ("#정부지원금",   "#6366f1", 20,  50, 130),
        ("#복지혜택",     "#ec4899", 160, 50, 110),
        ("#지원금신청",   "#f59e0b", 280, 50, 120),
        ("#생활지원금",   "#10b981", 410, 50, 120),
        ("#정부24",       "#ef4444", 540, 50, 100),
        ("#복지로",       "#3b82f6", 650, 50, 100),
        ("#소상공인",     "#8b5cf6", 20,  100,110),
        ("#청년혜택",     "#06b6d4", 140, 100,110),
        ("#출산혜택",     "#f97316", 260, 100,110),
        ("#매일업데이트", "#e11d48", 380, 100,160),
    ]
    rects = ""
    for tag, color, x, y, w in tags:
        cx = x + w // 2
        rects += f"""
  <rect x="{x}" y="{y}" width="{w}" height="34" rx="17" fill="{color}"/>
  <text x="{cx}" y="{y+22}" font-family="Arial" font-size="12" fill="white" text-anchor="middle" font-weight="bold">{tag}</text>"""

    return f"""<svg width="800" height="155" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="155" fill="#f8faff" rx="14"/>
  <rect x="2" y="2" width="796" height="151" rx="12" fill="none" stroke="#e0e7ff" stroke-width="2"/>
  <text x="400" y="30" font-family="Arial" font-size="14" fill="#6366f1" text-anchor="middle" font-weight="bold">🔖 관련 태그</text>
  {rects}
</svg>"""


# ══════════════════════════════════════════════
# SVG → PNG 변환 (Playwright 활용)
# ══════════════════════════════════════════════

def svg_to_png(page, svg_content: str, png_path: Path):
    """SVG 문자열을 PNG 파일로 변환"""
    try:
        page.goto("about:blank", wait_until="domcontentloaded")
        page.set_content(
            f"<!DOCTYPE html><html><body style='margin:0;padding:0;background:white'>"
            f"{svg_content}</body></html>",
            wait_until="domcontentloaded"
        )
        time.sleep(0.8)
        el = page.query_selector("svg")
        if el:
            el.screenshot(path=str(png_path))
        else:
            page.screenshot(path=str(png_path), full_page=True)
        return True
    except Exception as e:
        logging.warning(f"PNG 변환 실패 ({png_path.name}): {e}")
        return False


# ══════════════════════════════════════════════
# 블로그 글 생성 (업그레이드 스타일)
# ══════════════════════════════════════════════

def generate_post(articles, today_str, month_str, banner_name, card_name, cta_name, tag_name):
    """업그레이드된 블로그 글 생성"""

    # 혜택별 카드 블록
    benefit_blocks = ""
    for i, a in enumerate(articles[:5]):
        emoji = a.get("emoji", EMOJIS[i % len(EMOJIS)])
        title = a.get("title", "")
        amt   = a.get("amount", "신청 가능")
        src   = a.get("source", "정부")
        link  = a.get("link", "https://www.gov.kr")

        benefit_blocks += f"""
┌──────────────────────────────────────────┐
│  {emoji} {title}
│
│  💵 지원 금액 : {amt}
│  📋 출처      : {src}
└──────────────────────────────────────────┘
   👉 지금 바로 신청하기 → {link}

"""

    # 신청 방법 표
    apply_table = """
┌──────────────┬──────────────────────────────┐
│  방법         │  링크                         │
├──────────────┼──────────────────────────────┤
│ 🖥️ 온라인   │  www.gov.kr (정부24)          │
│ 💻 복지포털  │  www.bokjiro.go.kr (복지로)   │
│ 📞 전화      │  1345 (복지 콜센터, 무료)     │
│ 🏢 방문      │  가까운 주민센터              │
└──────────────┴──────────────────────────────┘"""

    safe_month = month_str.replace(' ', '')

    return f"""🔥 {today_str} 정부혜택 총정리! 오늘 꼭 챙겨야 할 지원금 모음 💰

[IMAGE:{banner_name}]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 {today_str} 기준 · 최신 업데이트 완료!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

안녕하세요 여러분~ 🙌
매일 아침 따끈따끈한 정부혜택 소식 들고 왔어요!
오늘도 놓치면 진짜 손해인 지원금들 모아봤어요 👇
신청해야만 받을 수 있으니 끝까지 읽어주세요! 💪


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎁 오늘의 혜택 한눈에 보기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[IMAGE:{card_name}]


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 혜택별 상세 정보 & 신청 링크
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{benefit_blocks}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 신청 방법 총정리
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{apply_table}

🏛️ 정부24 바로가기
   👉 온라인 신청 → https://www.gov.kr

💰 복지로 바로가기
   👉 온라인 신청 → https://www.bokjiro.go.kr

📰 정책브리핑 새소식
   👉 최신 정보 → https://www.korea.kr


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 꼭 기억하세요!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[IMAGE:{cta_name}]

┌─────────────────────────────────────┐
│  ⚠️ 이것만은 꼭!                     │
│                                       │
│  ✔️ 혜택은 반드시 직접 신청해야 받아요  │
│  ✔️ 신청 기간 지나면 소급 적용 안 돼요  │
│  ✔️ 모르겠으면 1345로 전화하세요 (무료) │
│  ✔️ 가까운 주민센터 방문도 가능해요!   │
└─────────────────────────────────────┘


오늘도 여기까지 읽어주셔서 감사해요! 🙏
이 글이 도움됐다면 공감❤️ & 구독🔔 눌러주세요!
매일 아침 최신 혜택 정보로 찾아올게요 😊

[IMAGE:{tag_name}]

#정부지원금 #복지혜택 #지원금신청 #{safe_month}혜택 #정부24 #복지로 #소상공인 #청년혜택 #출산혜택 #매일업데이트
"""


# ══════════════════════════════════════════════
# 수집
# ══════════════════════════════════════════════

def collect_from_site(page, source):
    results = []
    try:
        page.goto(source["url"], wait_until="domcontentloaded", timeout=20000)
        time.sleep(3)
        items = page.evaluate(f"""
            () => {{
                const els = Array.from(document.querySelectorAll('{source["title_sel"]}'));
                return els.slice(0,8).map(el => ({{
                    title: el.innerText.trim(),
                    link:  el.href || ''
                }})).filter(r => r.title.length > 3);
            }}
        """)
        for item in items:
            results.append({
                "title":  item.get("title","")[:30],
                "amount": "신청 가능",
                "link":   item.get("link", source["url"]),
                "source": source["name"],
                "emoji":  EMOJIS[len(results) % len(EMOJIS)],
            })
        logging.info(f"{source['name']} 수집: {len(results)}건")
        print(f"  {source['name']}: {len(results)}건")
    except Exception as e:
        logging.error(f"{source['name']} 실패: {e}")
        print(f"  {source['name']}: 실패")
    return results


# ══════════════════════════════════════════════
# 메인
# ══════════════════════════════════════════════

def main():
    now       = datetime.now()
    today_str = now.strftime("%Y년 %m월 %d일")
    month_str = now.strftime("%Y년 %m월")
    timestamp = now.strftime("%Y%m%d_%H%M")

    print("=" * 52)
    print(f"  💰 정부혜택 수집 시작 ({now.strftime('%Y-%m-%d %H:%M')})")
    print("=" * 52)
    logging.info("===== 정부혜택 수집 시작 =====")

    # ── 1. 수집 + 이미지 PNG 변환 (Playwright 한 세션으로) ──
    all_articles = []
    print("\n[1] 정부 공식 사이트 수집 중...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = ctx.new_page()
        for src in SOURCES:
            all_articles.extend(collect_from_site(page, src))
            time.sleep(2)

        print(f"  총 수집: {len(all_articles)}건")
        if len(all_articles) < 2:
            print("  ⚠️ 수집 부족 → 기본 혜택 정보로 대체")
            all_articles = FALLBACK

        # ── 2. SVG → PNG 이미지 자동 생성 ──
        print("\n[2] 이미지 자동 생성 중...")
        banner_name = f"daily_banner_{timestamp}.png"
        card_name   = f"daily_cards_{timestamp}.png"
        cta_name    = f"daily_cta_{timestamp}.png"
        tag_name    = f"daily_tags_{timestamp}.png"

        svg_jobs = [
            (make_banner_svg(today_str, month_str, len(all_articles)), banner_name),
            (make_benefit_cards_svg(all_articles),                     card_name),
            (make_cta_svg(),                                           cta_name),
            (make_hashtag_svg(),                                       tag_name),
        ]
        ok_count = 0
        for svg_content, png_name in svg_jobs:
            if svg_to_png(page, svg_content, BLOG_IMAGES_DIR / png_name):
                ok_count += 1
        print(f"  이미지 {ok_count}/4개 생성 완료 ✅")
        browser.close()

    # ── 3. 블로그 글 생성 ──
    print("\n[3] 블로그 글 생성 중...")
    content  = generate_post(all_articles, today_str, month_str,
                             banner_name, card_name, cta_name, tag_name)
    filename = f"정부혜택_{timestamp}.txt"
    (POSTS_DIR / filename).write_text(content, encoding="utf-8")
    print(f"  저장: {filename} ✅")
    logging.info(f"글 저장: {filename}")

    # ── 4. 네이버 자동 업로드 ──
    print("\n[4] 네이버 블로그 업로드 중...")
    try:
        result = subprocess.run(
            ["python", str(BASE_DIR / "blog_auto.py")],
            cwd=str(BASE_DIR),
            capture_output=True, text=True,
            encoding="utf-8", timeout=300
        )
        print(result.stdout)
        if result.returncode == 0:
            print("  네이버 업로드 완료 ✅")
            logging.info("네이버 업로드 완료")
        else:
            print(f"  네이버 업로드 실패 ❌\n{result.stderr}")
            logging.error(f"업로드 실패: {result.stderr}")
    except Exception as e:
        print(f"  업로드 오류: {e}")
        logging.error(f"업로드 오류: {e}")

    print("\n" + "=" * 52)
    print("  전체 완료! 🎉")
    print("=" * 52)
    logging.info("수집·이미지·글·업로드 완료")


if __name__ == "__main__":
    main()
