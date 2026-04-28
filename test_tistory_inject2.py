"""
티스토리 발행 2차 디버그 — Playwright 네이티브 클릭으로 "공개 발행"
"""
import json, time, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path("C:/Users/WIN10/.antigravity")
COOKIE   = BASE_DIR / "tistory_cookies.json"
BLOG     = "info23027"
TITLE    = "🐋 [테스트] 네이티브 클릭 발행 테스트"
CONTENT  = "<h2>주입 테스트</h2><p>Playwright 네이티브 클릭으로 발행합니다 🎉</p>"

def shot(page, name):
    p = str(BASE_DIR / "blog_images" / f"inject2_{name}.png")
    page.screenshot(path=p)
    print(f"  📸 {name}")

def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=150)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        ctx.add_cookies(cookies)
        page = ctx.new_page()

        print("[1] 글쓰기 페이지...")
        page.goto(f"https://{BLOG}.tistory.com/manage/newpost",
                  wait_until="domcontentloaded")
        time.sleep(6)

        if "login" in page.url or "auth" in page.url:
            print("❌ 쿠키 만료")
            browser.close()
            return

        print("[2] 제목 입력...")
        for sel in ["#post-title-inp", ".tt_area_title textarea"]:
            try:
                page.wait_for_selector(sel, timeout=3000)
                page.click(sel)
                page.evaluate(f"navigator.clipboard.writeText({json.dumps(TITLE)})")
                time.sleep(0.3)
                page.keyboard.press("Control+v")
                time.sleep(0.5)
                print(f"  → 완료 ({sel})")
                break
            except:
                continue

        print("[3] TinyMCE setContent 주입...")
        result = page.evaluate(f"""
            () => {{
                try {{
                    if (window.tinymce && tinymce.activeEditor) {{
                        tinymce.activeEditor.setContent({json.dumps(CONTENT)});
                        return 'OK len=' + tinymce.activeEditor.getContent().length;
                    }}
                    return 'TinyMCE 없음';
                }} catch(e) {{ return 'ERR: ' + e.message; }}
            }}
        """)
        print(f"  → {result}")
        time.sleep(2)
        shot(page, "03_after_inject")

        print("[4] 완료 버튼 (Playwright 네이티브)...")
        try:
            page.wait_for_selector("button:has-text('완료')", timeout=5000)
            page.click("button:has-text('완료')")
            print("  → 완료 클릭")
            time.sleep(5)
        except Exception as e:
            print(f"  → 완료 실패: {e}")
        shot(page, "04_after_done")

        print("[5] 패널 스크롤 + 공개 라디오...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)

        # 공개 라디오 ID 찾기
        radio_id = page.evaluate("""
            () => {
                const label = Array.from(document.querySelectorAll('label'))
                    .find(l => l.offsetParent !== null && l.innerText.trim() === '공개');
                return label ? label.htmlFor : null;
            }
        """)
        print(f"  → 라디오 ID: {radio_id}")

        if radio_id:
            page.click(f"#{radio_id}", timeout=3000)
            print(f"  → #{radio_id} 클릭")
        time.sleep(2)
        shot(page, "05_after_radio")

        print("[6] 가시 버튼 목록...")
        btns = page.evaluate("""
            () => Array.from(document.querySelectorAll('button'))
                 .filter(b => b.offsetParent !== null && b.innerText.trim())
                 .map(b => b.innerText.trim())
        """)
        print(f"  → {btns}")

        print("[7] '공개 발행' Playwright 네이티브 클릭...")
        # JS evaluate 대신 Playwright locator 사용
        publish_btn = None
        for kw in ['공개 발행', '공개 저장', '발행']:
            loc = page.locator(f"button:visible").filter(has_text=kw)
            # 정확히 일치하는 것만
            matching = [b for b in btns if b.strip() == kw]
            if matching:
                try:
                    # 정확한 텍스트로 XPath 클릭
                    page.locator(f"xpath=//button[normalize-space(text())='{kw}' and @style!='display: none']").first.click(timeout=3000)
                    publish_btn = kw
                    print(f"  → XPath 클릭: '{kw}'")
                    break
                except Exception as e:
                    print(f"  → XPath 실패 '{kw}': {e}")
                    # fallback: has-text + filter
                    try:
                        page.locator("button").filter(has_text=kw).first.click(timeout=2000)
                        publish_btn = kw
                        print(f"  → locator filter 클릭: '{kw}'")
                        break
                    except Exception as e2:
                        print(f"  → filter 실패: {e2}")

        if not publish_btn:
            print("  → 발행 버튼 못 찾음!")

        print("[8] URL 변경 대기...")
        try:
            page.wait_for_url(lambda url: "newpost" not in url, timeout=12000)
            print(f"  → ✅ URL 변경: {page.url}")
        except:
            print(f"  → ⚠️ URL 변경 없음: {page.url}")
            # 에러 메시지나 validation 확인
            error_msg = page.evaluate("""
                () => {
                    const errs = Array.from(document.querySelectorAll('.error, .alert, [class*="error"], [class*="alert"]'))
                        .filter(e => e.offsetParent && e.innerText.trim());
                    return errs.map(e => e.innerText.trim().slice(0, 60));
                }
            """)
            print(f"  → 에러 메시지: {error_msg}")

            toast_msg = page.evaluate("""
                () => {
                    const toasts = Array.from(document.querySelectorAll('[class*="toast"], [class*="snack"], [role="alert"]'))
                        .filter(e => e.innerText.trim());
                    return toasts.map(e => e.innerText.trim().slice(0, 60));
                }
            """)
            print(f"  → 토스트: {toast_msg}")

        time.sleep(3)
        shot(page, "08_final")
        print(f"\n최종 URL: {page.url}")
        time.sleep(5)
        browser.close()

if __name__ == "__main__":
    main()
