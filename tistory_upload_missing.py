"""
누락된 소상공인, 출산육아 글을 티스토리에 재업로드
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

UPLOAD_LIST = [
    {
        "file": "20260403_083044_2026_소상공인_정부혜택_블로그포스팅.txt",
        "title": "🏪 2026년 소상공인 정부지원 총정리 | 지금 신청 안 하면 손해 보는 혜택 모음"
    },
    {
        "file": "20260403_083141_2026_출산육아_정부혜택_총정리_네이버용.txt",
        "title": "👶 2026년 출산·육아 정부혜택 총정리! 놓치면 손해예요"
    },
]

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def upload_one(page, blog_name, title, content):
    html_content = txt_to_tistory_html(title, content)

    page.goto(f"https://{blog_name}.tistory.com/manage/newpost", wait_until="domcontentloaded")
    page.bring_to_front()
    time.sleep(5)

    if "login" in page.url or "auth" in page.url:
        print("    ❌ 로그인 필요")
        return False

    # 제목 입력
    for sel in ["#post-title-inp", ".tt_area_title textarea", "[placeholder*='제목']"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.click(sel)
            page.evaluate(f"navigator.clipboard.writeText({json.dumps(title)})")
            time.sleep(0.3)
            page.keyboard.press("Control+v")
            time.sleep(0.5)
            break
        except:
            continue

    time.sleep(2)

    # HTML 모드
    for btn in ["button:has-text('HTML')", "[title='HTML']", ".btn-html-mode"]:
        try:
            page.click(btn, timeout=2000)
            time.sleep(1)
            break
        except:
            continue

    # 내용 주입
    try:
        page.evaluate(f"""
            () => {{
                const cm = document.querySelector('.CodeMirror');
                if (cm && cm.CodeMirror) {{
                    cm.CodeMirror.setValue({json.dumps(html_content)});
                    return 'CodeMirror';
                }}
                const el = document.querySelector('.ProseMirror') || document.querySelector('[contenteditable=true]');
                if (el) {{
                    el.innerHTML = {json.dumps(html_content)};
                    return 'innerHTML';
                }}
                return 'not found';
            }}
        """)
    except Exception as e:
        print(f"    내용 주입 오류: {e}")
    time.sleep(3)

    # 발행 버튼 (완료 클릭 → 공개 → 발행)
    for sel in ["button:has-text('완료')", "button:has-text('발행')", "#publish-layer-btn"]:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.click(sel)
            time.sleep(5)
            break
        except:
            continue

    for sel in ["button:has-text('공개')"]:
        try:
            page.wait_for_selector(sel, timeout=5000)
            page.click(sel)
            time.sleep(2)
            break
        except:
            continue

    for sel in ["button:has-text('발행')"]:
        try:
            page.wait_for_selector(sel, timeout=5000)
            page.click(sel)
            time.sleep(3)
            break
        except:
            continue

    time.sleep(3)
    return True

def main():
    config = load_config()
    blog_name = config["tistory"]["blog_name"]
    email = config["tistory"]["email"]
    password = config["tistory"]["password"]

    print("=" * 55)
    print("  티스토리 누락 글 재업로드")
    print("=" * 55)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        ctx.grant_permissions(["clipboard-read", "clipboard-write"])

        if TISTORY_COOKIE.exists():
            with open(TISTORY_COOKIE, "r", encoding="utf-8") as f:
                ctx.add_cookies(json.load(f))

        page = ctx.new_page()
        page.goto(f"https://{blog_name}.tistory.com/manage", wait_until="domcontentloaded")
        time.sleep(3)

        if "login" in page.url or "auth" in page.url:
            print("  카카오 자동 로그인 중...")
            page.goto("https://www.tistory.com/auth/login", wait_until="domcontentloaded")
            time.sleep(3)
            try:
                page.click(".btn_login.link_kakao_id", timeout=5000)
            except:
                try:
                    page.click("a:has-text('카카오')", timeout=3000)
                except:
                    pass
            time.sleep(3)
            if "kakao" in page.url:
                try:
                    page.fill("#loginId--1", email)
                    time.sleep(0.3)
                    page.fill("#password--2", password)
                    time.sleep(0.3)
                    page.click(".btn_g.highlight.submit")
                    time.sleep(5)
                except:
                    pass
            # 대기
            for _ in range(60):
                time.sleep(2)
                if "tistory.com" in page.url and "login" not in page.url and "auth" not in page.url:
                    break
            page.goto(f"https://{blog_name}.tistory.com/manage", wait_until="domcontentloaded")
            time.sleep(3)
        print(f"  ✅ 접속: {page.url[:60]}")

        # 업로드
        ok = 0
        for item in UPLOAD_LIST:
            filepath = POSTED_DIR / item["file"]
            title = item["title"]

            if not filepath.exists():
                print(f"\n  ❌ 파일 없음: {item['file']}")
                continue

            content = filepath.read_text(encoding="utf-8")
            print(f"\n  [{ok+1}/{len(UPLOAD_LIST)}] {filepath.name[:50]}")
            print(f"    제목: {title[:50]}")

            result = upload_one(page, blog_name, title, content)
            if result:
                print(f"    ✅ 업로드 완료!")
                ok += 1
            else:
                print(f"    ❌ 업로드 실패")

            if ok < len(UPLOAD_LIST):
                print("    15초 대기...")
                time.sleep(15)

        print(f"\n  완료: {ok}/{len(UPLOAD_LIST)}개 성공")
        print(f"  블로그: https://{blog_name}.tistory.com")
        browser.close()

if __name__ == "__main__":
    main()
