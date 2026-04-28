"""
새벽 1시 자동 실행: 네이버·정책뉴스에서 최신 정부혜택 정보 수집 후 블로그 글 자동 생성
"""
import sys
import time
import logging
import re
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path("C:/Users/WIN10/.antigravity")
POSTS_DIR = BASE_DIR / "posts_pending"
LOG_DIR = BASE_DIR / "logs"

LOG_DIR.mkdir(exist_ok=True)
POSTS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "auto_collect.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

# 수집 대상 키워드
KEYWORDS = [
    "정부지원금 신청",
    "복지혜택 2026",
    "정부보조금 신규",
    "지원금 새소식",
    "청년혜택 2026",
    "출산혜택 신설",
    "소상공인 지원금",
    "주거지원 혜택",
]

# 수집 대상 사이트
SOURCES = [
    {"name": "정책브리핑", "url": "https://www.korea.kr/news/policyNewsList.do"},
    {"name": "복지로 새소식", "url": "https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do"},
    {"name": "네이버 정책뉴스", "url": "https://search.naver.com/search.naver?where=news&query=정부지원금+2026&sort=1"},
]

def collect_from_naver(page, keyword):
    """네이버 뉴스에서 키워드 관련 최신 기사 수집"""
    results = []
    try:
        url = f"https://search.naver.com/search.naver?where=news&query={keyword}&sort=1&ds=&de=&mynews=0&office_type=0"
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(2)

        # 뉴스 기사 제목과 요약 수집
        items = page.evaluate("""
            () => {
                const articles = Array.from(document.querySelectorAll('.news_wrap, .news_area'));
                return articles.slice(0, 5).map(a => ({
                    title: (a.querySelector('.news_tit, a.title') || {innerText: ''}).innerText.trim(),
                    summary: (a.querySelector('.news_dsc, .dsc_wrap') || {innerText: ''}).innerText.trim(),
                    link: (a.querySelector('a.news_tit, a.title') || {href: ''}).href
                })).filter(r => r.title);
            }
        """)
        results = items
        logging.info(f"네이버 수집: '{keyword}' -> {len(results)}건")
    except Exception as e:
        logging.error(f"네이버 수집 실패 '{keyword}': {e}")
    return results

def collect_from_policy(page):
    """정책브리핑에서 최신 정책 뉴스 수집"""
    results = []
    try:
        page.goto("https://www.korea.kr/news/policyNewsList.do", wait_until="domcontentloaded")
        time.sleep(3)
        items = page.evaluate("""
            () => {
                const articles = Array.from(document.querySelectorAll('.news-list li, .list-item'));
                return articles.slice(0, 8).map(a => ({
                    title: (a.querySelector('a, .tit') || {innerText: ''}).innerText.trim(),
                    link: (a.querySelector('a') || {href: ''}).href
                })).filter(r => r.title.length > 5);
            }
        """)
        results = items
        logging.info(f"정책브리핑 수집: {len(results)}건")
    except Exception as e:
        logging.error(f"정책브리핑 수집 실패: {e}")
    return results

def generate_post(keyword, articles):
    """수집한 기사를 바탕으로 블로그 포스트 생성"""
    today = datetime.now().strftime("%Y년 %m월 %d일")
    month = datetime.now().strftime("%Y년 %m월")

    # 기사 목록 텍스트 구성
    article_text = ""
    for i, a in enumerate(articles[:5], 1):
        if a.get("title"):
            article_text += f"\n📰 {a['title']}"
            if a.get("summary"):
                article_text += f"\n   {a['summary'][:100]}"
            if a.get("link") and a["link"].startswith("http"):
                article_text += f"\n   👉 {a['link']}"
            article_text += "\n"

    if not article_text:
        return None

    # 카테고리 판단
    category = "정부혜택"
    if "청년" in keyword:
        category = "청년혜택"
    elif "출산" in keyword or "육아" in keyword:
        category = "출산육아"
    elif "소상공인" in keyword:
        category = "소상공인"
    elif "주거" in keyword:
        category = "주거지원"

    post = f"""{month} 최신 {category} 뉴스 총정리 | 이번 달 꼭 챙겨야 할 혜택


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 {today} 기준 최신 정보 업데이트!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

매달 바뀌는 정부 혜택, 놓치지 않도록
최신 뉴스를 모아서 정리해 드릴게요! 📰

키워드: {keyword}


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 이번 달 주요 소식
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{article_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 관련 신청 바로가기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 전체 복지혜택 신청
   👉 복지로 바로가기 → https://www.bokjiro.go.kr

🏛️ 정부 서비스 신청
   👉 정부24 바로가기 → https://www.gov.kr

📰 정책 뉴스 더 보기
   👉 정책브리핑 바로가기 → https://www.korea.kr


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 마무리
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

정부 혜택은 신청해야만 받을 수 있어요! 💪
놓치지 말고 꼭 챙기세요!


#{category} #정부혜택 #2026정부지원 #복지로 #지원금신청 #정책뉴스 #{keyword.replace(" ", "")}
"""
    return post


def save_post(title, content):
    """생성된 글을 posts 폴더에 저장"""
    safe_title = re.sub(r'[\\/:*?"<>|]', '', title)[:40]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"수집_{timestamp}_{safe_title}.txt"
    filepath = POSTS_DIR / filename
    filepath.write_text(content, encoding="utf-8")
    print(f"  저장: {filename}")
    logging.info(f"글 저장: {filename}")
    return filepath


def main():
    print("=" * 50)
    print(f"  자료 수집 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("=" * 50)
    logging.info("===== 자료 수집 시작 =====")

    saved = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # 백그라운드 실행
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        # 정책브리핑 수집
        print("\n[1] 정책브리핑 수집 중...")
        policy_articles = collect_from_policy(page)
        if policy_articles:
            content = generate_post("정부 정책 새소식", policy_articles)
            if content:
                save_post("정책브리핑_최신뉴스", content)
                saved += 1

        # 네이버 키워드별 수집 (하루 2개만)
        print("\n[2] 네이버 뉴스 수집 중...")
        for keyword in KEYWORDS[:2]:
            articles = collect_from_naver(page, keyword)
            if articles:
                content = generate_post(keyword, articles)
                if content:
                    save_post(keyword, content)
                    saved += 1
            time.sleep(3)

        browser.close()

    print(f"\n총 {saved}개 글 생성 완료!")
    print("posts/ 폴더에 저장됐어요. 오전 10시에 자동 업로드됩니다!")
    logging.info(f"자료 수집 완료: {saved}개 생성")


if __name__ == "__main__":
    main()
