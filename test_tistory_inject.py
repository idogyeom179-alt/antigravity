"""
티스토리 HTML 주입 방법 정밀 디버그
1. TinyMCE 존재 여부 확인
2. HTML 모드 전환 후 CodeMirror 확인
3. 기본모드 복귀 버튼 텍스트 확인
4. 주입 후 TinyMCE.getContent() 로 실제 내용 확인
"""
import json, time, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR   = Path("C:/Users/WIN10/.antigravity")
COOKIE     = BASE_DIR / "tistory_cookies.json"
BLOG       = "info23027"

TITLE      = "🐋 [테스트] TinyMCE 주입 디버그"
CONTENT    = "<h2>주입 테스트</h2><p>이 내용이 보이면 성공 🎉</p><p>TinyMCE 경로로 주입된 HTML입니다.</p>"

def shot(page, name):
    p = str(BASE_DIR / "blog_images" / f"inject_{name}.png")
    page.screenshot(path=p)
    print(f"  📸 {name}")

def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=150)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        ctx.add_cookies(cookies)
        page = ctx.new_page()

        print("[1] 글쓰기 페이지 이동...")
        page.goto(f"https://{BLOG}.tistory.com/manage/newpost",
                  wait_until="domcontentloaded")
        time.sleep(6)
        shot(page, "01_loaded")

        if "login" in page.url or "auth" in page.url:
            print("❌ 쿠키 만료")
            browser.close()
            return

        print("[2] TinyMCE 상태 확인 (HTML 모드 전환 전)...")
        tstate = page.evaluate("""
            () => ({
                hasTinyMCE: !!(window.tinymce),
                hasActiveEditor: !!(window.tinymce && tinymce.activeEditor),
                editorId: window.tinymce && tinymce.activeEditor ? tinymce.activeEditor.id : null,
                contentLen: window.tinymce && tinymce.activeEditor ? tinymce.activeEditor.getContent().length : -1,
            })
        """)
        print(f"  → {tstate}")

        print("[3] 제목 입력...")
        for sel in ["#post-title-inp", ".tt_area_title textarea", "[placeholder*='제목']"]:
            try:
                page.wait_for_selector(sel, timeout=3000)
                page.click(sel)
                page.evaluate(f"navigator.clipboard.writeText({json.dumps(TITLE)})")
                time.sleep(0.3)
                page.keyboard.press("Control+v")
                time.sleep(0.5)
                print(f"  → 제목 완료 ({sel})")
                break
            except:
                continue

        print("[4] 현재 모드의 모든 버튼 출력...")
        btns = page.evaluate("""
            () => Array.from(document.querySelectorAll('button'))
                 .filter(b => b.offsetParent !== null)
                 .map(b => b.innerText.trim().slice(0, 20))
                 .filter(t => t)
        """)
        print(f"  → 가시 버튼: {btns}")

        # TinyMCE가 있으면 바로 주입 시도
        tstate2 = page.evaluate("""
            () => ({
                hasTinyMCE: !!(window.tinymce),
                hasActiveEditor: !!(window.tinymce && tinymce.activeEditor),
            })
        """)

        if tstate2['hasActiveEditor']:
            print("[5A] TinyMCE 직접 주입 (HTML 모드 전환 없이)...")
            result = page.evaluate(f"""
                () => {{
                    try {{
                        tinymce.activeEditor.setContent({json.dumps(CONTENT)});
                        return 'TinyMCE setContent OK, len=' + tinymce.activeEditor.getContent().length;
                    }} catch(e) {{
                        return 'ERROR: ' + e.message;
                    }}
                }}
            """)
            print(f"  → {result}")
            time.sleep(2)
            shot(page, "05a_tinymce_inject")
        else:
            print("[5B] TinyMCE 없음 → HTML 모드 전환...")
            # HTML 버튼 찾기
            all_btns_detail = page.evaluate("""
                () => Array.from(document.querySelectorAll('button'))
                     .map(b => ({
                         text: b.innerText.trim().slice(0,15),
                         title: (b.getAttribute('title')||'').slice(0,15),
                         cls: b.className.slice(0,30),
                         visible: b.offsetParent !== null
                     }))
                     .filter(b => b.text || b.title)
            """)
            print("  → 전체 버튼 목록:")
            for b in all_btns_detail[:30]:
                print(f"     [{b['text']}] title={b['title']} vis={b['visible']}")

            for btn_sel in ["button:has-text('HTML')", "[title='HTML']", ".btn-html-mode"]:
                try:
                    page.click(btn_sel, timeout=2000)
                    print(f"  → HTML 버튼 클릭: {btn_sel}")
                    time.sleep(2)
                    break
                except:
                    pass
            shot(page, "05b_html_mode")

            print("[5B-2] HTML 모드 전환 후 상태 확인...")
            cm_state = page.evaluate("""
                () => {
                    const cm = document.querySelector('.CodeMirror');
                    return {
                        hasCodeMirror: !!cm,
                        hasCMInstance: !!(cm && cm.CodeMirror),
                        hasTinyMCE: !!(window.tinymce && tinymce.activeEditor),
                    };
                }
            """)
            print(f"  → {cm_state}")

            # 기본모드 복귀 버튼 탐색
            btns_after_html = page.evaluate("""
                () => Array.from(document.querySelectorAll('button'))
                     .filter(b => b.offsetParent !== null)
                     .map(b => ({text: b.innerText.trim().slice(0,20), cls: b.className.slice(0,30)}))
                     .filter(b => b.text)
            """)
            print("  → HTML 모드 후 가시 버튼:")
            for b in btns_after_html:
                print(f"     [{b['text']}] {b['cls']}")

            # CodeMirror 주입
            inject_result = page.evaluate(f"""
                () => {{
                    const cm = document.querySelector('.CodeMirror');
                    if (cm && cm.CodeMirror) {{
                        cm.CodeMirror.setValue({json.dumps(CONTENT)});
                        return 'CodeMirror setValue OK';
                    }}
                    return 'CodeMirror NOT FOUND';
                }}
            """)
            print(f"  → CodeMirror 주입: {inject_result}")
            time.sleep(1)

            # 기본모드 버튼 클릭
            back_result = page.evaluate("""
                () => {
                    const candidates = ['기본모드', '비주얼', '편집기', 'WYSIWYG', 'Visual'];
                    for (const kw of candidates) {
                        const btn = Array.from(document.querySelectorAll('button'))
                            .find(b => b.offsetParent !== null && (b.innerText||'').trim().includes(kw));
                        if (btn) { btn.click(); return '클릭:' + kw; }
                    }
                    return 'NOT FOUND';
                }
            """)
            print(f"  → 기본모드 복귀: {back_result}")
            time.sleep(2)

            # 기본모드 복귀 후 TinyMCE 확인
            tstate3 = page.evaluate("""
                () => ({
                    hasTinyMCE: !!(window.tinymce && tinymce.activeEditor),
                    contentLen: window.tinymce && tinymce.activeEditor
                        ? tinymce.activeEditor.getContent().length : -1,
                    contentPreview: window.tinymce && tinymce.activeEditor
                        ? tinymce.activeEditor.getContent().slice(0, 80) : 'N/A',
                })
            """)
            print(f"  → 기본모드 복귀 후 TinyMCE: {tstate3}")
            shot(page, "05b_after_back")

        print("[6] 완료 버튼 클릭...")
        for sel in ["button:has-text('완료')", "#publish-layer-btn"]:
            try:
                page.wait_for_selector(sel, timeout=4000)
                page.click(sel)
                print(f"  → 클릭: {sel}")
                time.sleep(5)
                break
            except Exception as e:
                print(f"  → 실패: {sel}: {e}")
        shot(page, "06_after_complete")

        print("[7] 공개 패널 분석...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)

        panel_info = page.evaluate("""
            () => {
                const labels = Array.from(document.querySelectorAll('label'))
                    .filter(l => l.offsetParent !== null)
                    .map(l => ({
                        text: l.innerText.trim(),
                        for: l.htmlFor,
                        checked: document.getElementById(l.htmlFor)
                            ? document.getElementById(l.htmlFor).checked : null
                    }));
                const btns = Array.from(document.querySelectorAll('button'))
                    .filter(b => b.offsetParent !== null)
                    .map(b => b.innerText.trim());
                return { labels, buttons: btns };
            }
        """)
        print(f"  → 라벨: {panel_info['labels']}")
        print(f"  → 버튼: {panel_info['buttons']}")

        print("[8] 공개 라디오 클릭...")
        radio_id = page.evaluate("""
            () => {
                const label = Array.from(document.querySelectorAll('label'))
                    .find(l => l.offsetParent !== null && l.innerText.trim() === '공개');
                return label ? label.htmlFor : null;
            }
        """)
        if radio_id:
            page.click(f"#{radio_id}", timeout=3000)
            print(f"  → #{radio_id} 클릭")
        else:
            print("  → 공개 라벨 없음!")
        time.sleep(2)
        shot(page, "07_after_public")

        print("[9] 공개 클릭 후 버튼 목록...")
        btns_final = page.evaluate("""
            () => Array.from(document.querySelectorAll('button'))
                 .filter(b => b.offsetParent !== null && b.innerText.trim())
                 .map(b => b.innerText.trim())
        """)
        print(f"  → {btns_final}")

        print("[10] 발행 버튼 클릭...")
        clicked = page.evaluate("""
            () => {
                const candidates = ['공개 발행', '공개 저장', '발행', '저장'];
                for (const kw of candidates) {
                    const btn = Array.from(document.querySelectorAll('button'))
                        .find(b => b.offsetParent !== null && (b.innerText||'').trim() === kw);
                    if (btn) { btn.click(); return '클릭:' + kw; }
                }
                return 'NOT FOUND';
            }
        """)
        print(f"  → {clicked}")

        try:
            page.wait_for_url(lambda url: "newpost" not in url, timeout=12000)
            print(f"  → URL 변경됨! {page.url}")
        except:
            print(f"  → URL 변경 없음 (10초 후): {page.url}")

        time.sleep(3)
        shot(page, "10_final")
        print(f"\n최종 URL: {page.url}")
        input("\n[Enter] 누르면 브라우저 닫기...")
        browser.close()

if __name__ == "__main__":
    main()
