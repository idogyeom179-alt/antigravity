"""
티스토리 현재 글 목록 확인 + 누락된 글 재업로드
"""
import json
import time
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from tistory_formatter import txt_to_tistory_html

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path("C:/Users/WIN10/.antigravity")
TISTORY_COOKIE = BASE_DIR / "tistory_cookies.json"
CONFIG_PATH = BASE_DIR / "config.json"
POSTED_DIR = BASE_DIR / "posted"

# 올라가야 할 글 목록 (파일명 → 제목 매핑)
EXPECTED_POSTS = {
    "01_청년_정부혜택_총정리": "👩‍💼 2026년 청년 정부혜택 총정리! 20~30대라면 꼭 챙기세요",
    "02_노인_정부혜택_총정리": "👴👵 2026년 노인·어르신 정부혜택 총정리! 부모님께 꼭 알려드리세요",
    "03_주거지원_정부혜택_총정리": "🏠 2026년 주거 지원 정부혜택 총정리! 전세·월세 부담 줄이는 방법",
    "04_의료건강_정부혜택_총정리": "🏥 2026년 의료·건강 정부혜택 총정리! 병원비 아끼는 꿀팁",
    "05_취업고용_정부혜택_총정리": "💼 2026년 취업·고용 정부혜택 총정리! 직장 찾는 분들 필독!",
    "06_교육_정부혜택_총정리": "📚 2026년 교육 정부혜택 총정리! 학비 걱정 끝내는 방법",
    "07_신혼부부_정부혜택_총정리": "💑 2026년 신혼부부 정부혜택 총정리! 결혼하면 이만큼 받아요",
    "08_장애인_정부혜택_총정리": "♿ 2026년 장애인 정부혜택 총정리! 꼭 챙겨야 할 지원 모음",
    "09_저소득층_정부혜택_총정리": "🤝 2026년 저소득층 정부혜택 총정리! 기초수급자부터 차상위까지",
    "10_농어업인_정부혜택_총정리": "🌾 2026년 농어업인 정부혜택 총정리! 농촌에 사신다면 꼭 보세요",
    "소상공인_정부혜택": "🏪 2026년 소상공인 정부지원 총정리 | 지금 신청 안 하면 손해 보는 혜택 모음",
    "출산육아_정부혜택": "👶 2026년 출산·육아 정부혜택 총정리! 놓치면 손해예요",
}

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_tistory_posts(page, blog_name):
    """현재 티스토리 글 목록 조회"""
    posts = []
    page_num = 1
    while True:
        r = page.evaluate(f"""
            async () => {{
                const r = await fetch('https://{blog_name}.tistory.com/manage/posts.json?page={page_num}&count=50', {{
                    credentials: 'include'
                }});
                return await r.json();
            }}
        """)
        if not r or 'posts' not in r:
            break
        batch = r.get('posts', [])
        posts.extend(batch)
        if len(batch) < 50:
            break
        page_num += 1
    return posts

def find_source_file(key):
    """posted/ 폴더에서 해당 글 파일 찾기 (가장 최근 것)"""
    matches = sorted(POSTED_DIR.glob(f"*{key}*.txt"), reverse=True)
    return matches[0] if matches else None

def upload_post(page, blog_name, title, content):
    """티스토리에 글 업로드"""
    html_content = txt_to_tistory_html(title, content)
    page.goto(f"https://{blog_name}.tistory.com/manage/newpost", wait_until="domcontentloaded")
    page.bring_to_front()
    time.sleep(5)

    if "login" in page.url or "auth" in page.url:
        print("  ❌ 로그인 필요!")
        return False

    # 제목 입력
    for sel in ["#post-title-inp", ".tt_area_title textarea", "[placeholder*='제목']"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.click(sel)
            page.evaluate(f"navigator.clipboard.writeText({json.dumps(title)})")
            time.sleep(0.3)
            page.keyboard.press("Control+v")
            break
        except:
            continue
    time.sleep(2)

    # HTML 모드 전환
    for html_btn in ["button:has-text('HTML')", "[title='HTML']", ".btn-html-mode"]:
        try:
            page.click(html_btn, timeout=2000)
            time.sleep(1)
            break
        except:
            continue

    # HTML 주입
    try:
        page.evaluate(f"""
            () => {{
                const cm = document.querySelector('.CodeMirror');
                if (cm && cm.CodeMirror) {{ cm.CodeMirror.setValue({json.dumps(html_content)}); return; }}
                const el = document.querySelector('.ProseMirror') || document.querySelector('[contenteditable=true]');
                if (el) el.innerHTML = {json.dumps(html_content)};
            }}
        """)
        time.sleep(2)
    except:
        pass

    time.sleep(2)

    # 발행 버튼
    for sel in ["button:has-text('발행')", "button:has-text('완료')", "#publish-layer-btn"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.click(sel)
            time.sleep(5)
            break
        except:
            continue

    # 공개 → 발행
    for sel in ["button:has-text('공개')"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.click(sel)
            time.sleep(2)
            break
        except:
            continue

    for sel in ["button:has-text('발행')"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.click(sel)
            time.sleep(3)
            break
        except:
            continue

    return True

def main():
    config = load_config()
    blog_name = config["tistory"]["blog_name"]

    print("=" * 55)
    print("  티스토리 글 상태 확인 및 재업로드")
    print("=" * 55)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        ctx.grant_permissions(["clipboard-read", "clipboard-write"])

        # 쿠키 로드
        if TISTORY_COOKIE.exists():
            with open(TISTORY_COOKIE, "r", encoding="utf-8") as f:
                ctx.add_cookies(json.load(f))
            print("  티스토리 쿠키 로드 완료")

        page = ctx.new_page()
        page.goto(f"https://{blog_name}.tistory.com/manage", wait_until="domcontentloaded")
        time.sleep(3)

        if "login" in page.url or "auth" in page.url:
            print("  ❌ 로그인 필요! 카카오 로그인 해주세요 (5분)")
            page.goto("https://www.tistory.com/auth/login", wait_until="domcontentloaded")
            page.bring_to_front()
            for _ in range(300):
                time.sleep(1)
                if "tistory.com" in page.url and "login" not in page.url and "auth" not in page.url:
                    print("  ✅ 로그인 성공!")
                    break
        else:
            print(f"  ✅ 티스토리 자동 로그인 성공")

        # 현재 글 목록 조회
        print("\n  현재 티스토리 글 목록 조회 중...")
        posts = get_tistory_posts(page, blog_name)
        print(f"  총 {len(posts)}개 글 발견\n")

        existing_titles = set()
        for post in posts:
            t = post.get('title', '')
            v = post.get('visibility', '')
            print(f"  ID {post.get('id')}: [{v}] {t[:50]}")
            existing_titles.add(t)

        # 중복 확인
        print("\n\n  [중복 검사]")
        title_count = {}
        for post in posts:
            t = post.get('title', '')
            title_count[t] = title_count.get(t, [])
            title_count[t].append(post.get('id'))

        dups = {t: ids for t, ids in title_count.items() if len(ids) > 1}
        if dups:
            print(f"  중복 {len(dups)}개 발견!")
            for t, ids in dups.items():
                print(f"    '{t[:40]}': IDs {ids}")
                # 최신(가장 큰 ID) 남기고 나머지 삭제
                keep_id = max(ids)
                for del_id in ids:
                    if del_id != keep_id:
                        r = page.evaluate(f"""
                            async () => {{
                                const r = await fetch('https://{blog_name}.tistory.com/manage/post/{del_id}.json', {{
                                    method: 'DELETE', credentials: 'include'
                                }});
                                return r.status;
                            }}
                        """)
                        print(f"    삭제 ID {del_id}: HTTP {r}")
                        time.sleep(1)
        else:
            print("  ✅ 중복 없음!")

        # 잘못된 제목 글 삭제 (===, [메인 이미지] 등)
        print("\n  [잘못된 제목 글 정리]")
        bad_keywords = ["main_image", "=====", "[메인 이미지"]
        for post in posts:
            t = post.get('title', '')
            if any(kw in t for kw in bad_keywords):
                post_id = post.get('id')
                r = page.evaluate(f"""
                    async () => {{
                        const r = await fetch('https://{blog_name}.tistory.com/manage/post/{post_id}.json', {{
                            method: 'DELETE', credentials: 'include'
                        }});
                        return r.status;
                    }}
                """)
                print(f"  삭제: '{t[:40]}' (ID {post_id}): HTTP {r}")
                time.sleep(1)

        print("\n완료!")
        input("  [Enter] 브라우저 닫기...")
        browser.close()

if __name__ == "__main__":
    main()
