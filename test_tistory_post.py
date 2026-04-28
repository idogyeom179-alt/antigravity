"""
티스토리 발행 단계별 디버그 — 각 단계마다 스크린샷 저장
"""
import json, time, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path("C:/Users/WIN10/.antigravity")
COOKIE   = BASE_DIR / "tistory_cookies.json"
SHOT_DIR = BASE_DIR / "blog_images"
BLOG     = "info23027"

TITLE   = "🐋 [테스트] 고래가 알려주는 오늘의 혜택 정보"
CONTENT = "<h2>테스트 글입니다</h2><p>티스토리 발행 테스트 중이에요 🐋</p>"

def shot(page, name):
    path = str(SHOT_DIR / f"debug_{name}.png")
    page.screenshot(path=path)
    print(f"  📸 스크린샷: {name} (URL: {page.url[:60]})")

def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=200)
        ctx  = browser.new_context(viewport={"width": 1280, "height": 900})
        ctx.add_cookies(cookies)
        page = ctx.new_page()

        print("[1] 글쓰기 페이지 이동...")
        page.goto(f"https://{BLOG}.tistory.com/manage/newpost",
                  wait_until="domcontentloaded")
        time.sleep(5)
        shot(page, "01_newpost")

        if "login" in page.url or "auth" in page.url:
            print("❌ 로그인 필요")
            browser.close()
            return

        print("[2] 제목 입력...")
        for sel in ["#post-title-inp", ".tt_area_title textarea", "[placeholder*='제목']"]:
            try:
                page.wait_for_selector(sel, timeout=3000)
                page.click(sel)
                page.evaluate(f"navigator.clipboard.writeText({json.dumps(TITLE)})")
                time.sleep(0.3)
                page.keyboard.press("Control+v")
                time.sleep(0.5)
                print(f"  → 제목 입력 완료 ({sel})")
                break
            except Exception:
                continue
        shot(page, "02_title")

        print("[3] HTML 모드 버튼 찾기...")
        # 모든 버튼 목록 출력
        btns = page.eval_on_selector_all(
            "button",
            "els => els.map(e => ({text: e.innerText.trim().slice(0,20), id: e.id, cls: e.className.slice(0,30)}))"
        )
        print(f"  → 버튼 목록 ({len(btns)}개):")
        for b in btns[:20]:
            if b['text'] or b['id']:
                print(f"     [{b['text']}] id={b['id']} cls={b['cls'][:20]}")

        for btn_sel in ["button:has-text('HTML')", "[title='HTML']", ".btn-html-mode"]:
            try:
                page.click(btn_sel, timeout=2000)
                print(f"  → HTML 버튼 클릭: {btn_sel}")
                time.sleep(1)
                break
            except Exception:
                pass
        shot(page, "03_html_mode")

        print("[4] CodeMirror 주입...")
        result = page.evaluate(f"""
            () => {{
                const cm = document.querySelector('.CodeMirror');
                if (cm && cm.CodeMirror) {{
                    cm.CodeMirror.setValue({json.dumps(CONTENT)});
                    return 'CodeMirror OK';
                }}
                const el = document.querySelector('.ProseMirror')
                        || document.querySelector('[contenteditable=true]');
                if (el) {{
                    el.innerHTML = {json.dumps(CONTENT)};
                    return 'innerHTML OK';
                }}
                return 'NOT FOUND';
            }}
        """)
        print(f"  → 주입 결과: {result}")
        time.sleep(3)
        shot(page, "04_content")

        print("[5] 완료/발행 버튼 찾기...")
        btns2 = page.eval_on_selector_all(
            "button",
            "els => els.map(e => ({text: e.innerText.trim().slice(0,20), id: e.id, visible: e.offsetParent !== null}))"
        )
        print(f"  → 현재 버튼 목록:")
        for b in btns2:
            if b['text']:
                print(f"     [{b['text']}] visible={b['visible']}")

        for sel in ["button:has-text('완료')", "button:has-text('발행')", "#publish-layer-btn"]:
            try:
                page.wait_for_selector(sel, timeout=3000)
                page.click(sel)
                print(f"  → 클릭: {sel}")
                time.sleep(5)
                break
            except Exception as e:
                print(f"  → 실패: {sel} ({e})")
        shot(page, "05_after_complete")

        print("[6] 공개 선택 (정확히 '공개' 텍스트만)...")
        # 가시 요소 목록 출력 (button + div + label)
        all_vis = page.evaluate("""
            () => Array.from(document.querySelectorAll('div,button,label,span,li'))
                 .filter(e => e.offsetParent !== null && (e.innerText||'').trim())
                 .map(e => ({tag:e.tagName, text:(e.innerText||'').trim().slice(0,25), cls:e.className.slice(0,30)}))
                 .filter(e => e.text.length < 20)
        """)
        print(f"  → 가시 요소 (짧은 텍스트):")
        for v in all_vis[:30]:
            print(f"     <{v['tag']}> [{v['text']}] cls={v['cls']}")

        clicked = page.evaluate("""
            () => {
                const el = Array.from(document.querySelectorAll('div,button,label,span,li,a'))
                    .find(e => e.offsetParent !== null && (e.innerText||e.textContent||'').trim() === '공개');
                if (el) { el.click(); return el.tagName + ':' + el.className.slice(0,40); }
                return 'NOT FOUND';
            }
        """)
        print(f"  → 공개 클릭: {clicked}")
        time.sleep(2)
        shot(page, "06_after_public")

        print("[6-2] 공개 클릭 후 버튼 목록...")
        btns_after_public = page.evaluate("""
            () => Array.from(document.querySelectorAll('button'))
                 .filter(b => b.offsetParent !== null && b.innerText.trim())
                 .map(b => b.innerText.trim().slice(0,25))
        """)
        for b in btns_after_public:
            print(f"     [{b}]")

        print("[7] 저장 버튼 (공개 저장 or 저장)...")
        save_result = page.evaluate("""
            () => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const exact = ['공개 저장', '발행', '저장'];
                for (const kw of exact) {
                    const btn = buttons.find(b =>
                        b.offsetParent !== null &&
                        (b.innerText || '').trim() === kw
                    );
                    if (btn) { btn.click(); return '클릭:' + kw; }
                }
                return 'NOT FOUND:' + buttons.filter(b=>b.offsetParent).map(b=>b.innerText.trim().slice(0,15)).join(',');
            }
        """)
        print(f"  → 저장 결과: {save_result}")
        time.sleep(3)

        shot(page, "07_final")
        print(f"\n최종 URL: {page.url}")
        time.sleep(3)
        browser.close()

if __name__ == "__main__":
    main()
