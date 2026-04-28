import json
import time
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright
from tistory_formatter import txt_to_tistory_html
from image_uploader import post_to_naver_with_images, extract_svg_markers, _paste_content_smart

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path("C:/Users/WIN10/.antigravity")
POSTS_DIR = BASE_DIR / "posts"
POSTED_DIR = BASE_DIR / "posted"
LOG_DIR = BASE_DIR / "logs"
CONFIG_PATH = BASE_DIR / "config.json"
NAVER_COOKIE = BASE_DIR / "naver_cookies.json"
CUSTOM_COOKIES = BASE_DIR / "cookies.json"
TISTORY_COOKIE = BASE_DIR / "tistory_cookies.json"

LOG_DIR.mkdir(exist_ok=True)
POSTED_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "blog_auto.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

def paste_with_links(page, content):
    """[LINK:텍스트|URL] 마커 및 URL을 클릭 가능한 링크로 삽입"""
    _paste_content_smart(page, content)


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_next_post():
    posts = sorted(POSTS_DIR.glob("*.txt")) + sorted(POSTS_DIR.glob("*.md"))
    return posts[0] if posts else None

def parse_post(post_path):
    content = post_path.read_text(encoding="utf-8")
    title = post_path.stem.replace("_", " ")
    for line in content.split("\n"):
        stripped = line.strip().lstrip("#").strip()
        if stripped and len(stripped) > 3 and not stripped.startswith("[") and not stripped.startswith("=") and not stripped.startswith("━"):
            title = stripped
            break
    return title, content

def save_cookies(context, path):
    cookies = context.cookies()
    targets = {path}
    if path == NAVER_COOKIE:
        targets.add(CUSTOM_COOKIES)
    for target in targets:
        try:
            with open(target, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False)
            print(f"   쿠키 저장 완료: {target.name}")
        except Exception as e:
            print(f"   쿠키 저장 실패: {target.name} {e}")

def load_cookies(context, path):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                context.add_cookies(json.load(f))
            return True
        except Exception as e:
            print(f"   쿠키 로드 실패: {path.name} {e}")
    return False


def run_tistory_auto_login():
    print("  티스토리 자동 로그인 스크립트 실행 중...")
    try:
        result = subprocess.run(
            ["python", str(BASE_DIR / "tistory_auto_login.py")],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=900
        )
        print(result.stdout)
        if result.returncode == 0:
            print("  티스토리 자동 로그인 완료")
            return True
        print(f"  티스토리 자동 로그인 실패: {result.returncode}")
        print(result.stderr)
    except Exception as e:
        print(f"  티스토리 자동 로그인 오류: {e}")
    return False


def attempt_naver_login_with_credentials(page, context, config):
    nav = config.get("naver", {})
    if not nav.get("id") or not nav.get("password"):
        return False

    page.goto("https://nid.naver.com/nidlogin.login", wait_until="domcontentloaded")
    time.sleep(2)

    selectors = [
        ("#id", nav["id"]),
        ("#id_input", nav["id"]),
        ("input[name='id']", nav["id"]),
        ("input[type='text']", nav["id"]),
    ]
    pw_selectors = [
        ("#pw", nav["password"]),
        ("#pw_input", nav["password"]),
        ("input[name='pw']", nav["password"]),
        ("input[type='password']", nav["password"]),
    ]

    filled = False
    for sel, value in selectors:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.fill(sel, value)
            filled = True
            break
        except Exception:
            continue

    for sel, value in pw_selectors:
        try:
            page.wait_for_selector(sel, timeout=3000)
            page.fill(sel, value)
            filled = True
            break
        except Exception:
            continue

    if not filled:
        return False

    for btn in ["#log.login", "button[type='submit']", "button.btn_login", "button.login_btn", "#log.login"]:
        try:
            page.click(btn, timeout=3000)
            break
        except Exception:
            continue

    for _ in range(30):
        time.sleep(1)
        try:
            if any(c["name"] == "NID_AUT" for c in context.cookies()):
                save_cookies(context, NAVER_COOKIE)
                print("   네이버 자동 로그인 성공")
                return True
        except Exception:
            pass
    return False


def naver_login(page, context, config):
    if load_cookies(context, NAVER_COOKIE) or load_cookies(context, CUSTOM_COOKIES):
        page.goto("https://www.naver.com", wait_until="domcontentloaded")
        time.sleep(2)
        cookies = context.cookies()
        if any(c["name"] == "NID_AUT" for c in cookies):
            print("   네이버 자동 로그인 성공")
            return True

    if attempt_naver_login_with_credentials(page, context, config):
        return True

    print("\n  ┌─────────────────────────────────────────┐")
    print("  │  네이버 브라우저 창에서 로그인 해주세요!  │")
    print("  │  로그인하면 자동으로 다음으로 넘어가요   │")
    print("  └─────────────────────────────────────────┘")
    page.goto("https://nid.naver.com/nidlogin.login", wait_until="domcontentloaded")
    page.bring_to_front()

    for i in range(300):
        time.sleep(1)
        if i % 15 == 0 and i > 0:
            print(f"   {i}초 경과... 로그인 대기 중")
        try:
            if "nidlogin" not in page.url and "naver.com" in page.url:
                save_cookies(context, NAVER_COOKIE)
                return True
            if any(c["name"] == "NID_AUT" for c in context.cookies()):
                save_cookies(context, NAVER_COOKIE)
                return True
        except:
            pass
    return False

def post_to_naver(page, config, title, content):
    try:
        blog_id = config["naver"]["blog_id"]
        page.goto(f"https://blog.naver.com/PostWriteForm.naver?blogId={blog_id}", wait_until="domcontentloaded")
        page.bring_to_front()
        time.sleep(6)

        try:
            page.click(".se-help-panel-close-button", timeout=3000)
            time.sleep(0.5)
        except:
            pass

        try:
            page.click(".se-documentTitle")
            time.sleep(0.5)
            page.keyboard.press("Control+a")
            page.keyboard.press("Delete")
            page.evaluate(f"navigator.clipboard.writeText({json.dumps(title)})")
            time.sleep(0.3)
            page.keyboard.press("Control+v")
            time.sleep(0.5)
        except Exception as e:
            logging.warning(f"네이버 제목 입력 실패: {e}")

        try:
            page.wait_for_selector(".se-content", timeout=5000)
            page.click(".se-content")
            time.sleep(0.5)
            paste_with_links(page, content)
            time.sleep(2)
        except Exception as e:
            logging.error(f"네이버 본문 입력 실패: {e}")
            return False

        time.sleep(2)

        page.evaluate("""
            () => {
                const btn = Array.from(document.querySelectorAll('button'))
                    .find(b => b.className.includes('publish_btn'));
                if (btn) btn.click();
            }
        """)
        time.sleep(3)

        page.evaluate("""
            () => {
                const btn = Array.from(document.querySelectorAll('button'))
                    .find(b => b.className.includes('confirm_btn'));
                if (btn) btn.click();
            }
        """)
        time.sleep(4)

        logging.info(f"네이버 포스팅 완료: {title}")
        print("   네이버 ✅")
        return True

    except Exception as e:
        logging.error(f"네이버 포스팅 실패: {e}")
        print(f"   네이버 ❌ {e}")
        return False

def move_to_posted(post_path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = POSTED_DIR / f"{timestamp}_{post_path.name}"
    shutil.move(str(post_path), str(dest))
    logging.info(f"파일 이동: {dest.name}")
    print(f"   파일 이동 완료")


def post_to_tistory(page, context, title: str, html_content: str, _retry: bool = False) -> bool:
    """티스토리에 HTML 콘텐츠 발행 (완료→공개→발행 3단계)"""
    try:
        blog_name = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["tistory"]["blog_name"]
    except Exception:
        blog_name = "info23027"

    try:
        if TISTORY_COOKIE.exists():
            context.add_cookies(json.loads(TISTORY_COOKIE.read_text(encoding="utf-8")))

        page.goto(f"https://{blog_name}.tistory.com/manage/newpost",
                  wait_until="domcontentloaded")
        page.bring_to_front()
        time.sleep(5)

        if "login" in page.url or "auth" in page.url:
            print("   티스토리 ❌ 쿠키 만료 또는 로그인 필요")
            if run_tistory_auto_login():
                context.clear_cookies()
                page = context.new_page()
                if TISTORY_COOKIE.exists():
                    context.add_cookies(json.loads(TISTORY_COOKIE.read_text(encoding="utf-8")))
                page.goto(f"https://{blog_name}.tistory.com/manage/newpost",
                          wait_until="domcontentloaded")
                page.bring_to_front()
                time.sleep(5)
                if "login" in page.url or "auth" in page.url:
                    print("   티스토리 자동 로그인 후에도 로그인 페이지가 남아있음")
                    return False
            else:
                return False

        # ── 제목 입력 ──────────────────────────────
        for sel in ["#post-title-inp", ".tt_area_title textarea", "[placeholder*='제목']"]:
            try:
                page.wait_for_selector(sel, timeout=3000)
                page.click(sel)
                page.evaluate(f"navigator.clipboard.writeText({json.dumps(title)})")
                time.sleep(0.3)
                page.keyboard.press("Control+v")
                time.sleep(0.5)
                break
            except Exception:
                continue

        time.sleep(2)

        # ── HTML 주입: TinyMCE (기본모드에서 직접, HTML 모드 전환 불필요) ──
        injected = page.evaluate(f"""
            () => {{
                try {{
                    if (window.tinymce && tinymce.activeEditor) {{
                        tinymce.activeEditor.setContent({json.dumps(html_content)});
                        // React 상태 업데이트용 이벤트 발생
                        tinymce.activeEditor.fire('change');
                        tinymce.activeEditor.fire('input');
                        tinymce.activeEditor.undoManager.add();
                        return 'TinyMCE OK len=' + tinymce.activeEditor.getContent().length;
                    }}
                }} catch(e) {{}}
                // 폴백: contenteditable 직접 주입
                const el = document.querySelector('.ProseMirror')
                        || document.querySelector('[contenteditable=true]');
                if (el) {{
                    el.innerHTML = {json.dumps(html_content)};
                    el.dispatchEvent(new Event('input', {{bubbles:true}}));
                    el.dispatchEvent(new Event('change', {{bubbles:true}}));
                    return 'contenteditable OK';
                }}
                return 'NOT FOUND';
            }}
        """)
        print(f"   HTML 주입: {injected}")
        logging.info(f"티스토리 HTML 주입: {injected}")
        time.sleep(3)

        # ── 완료 버튼: Playwright + JS evaluate 병행 ──────
        done_clicked = False
        try:
            page.wait_for_selector("button:has-text('완료')", timeout=5000)
            page.locator("button").filter(has_text="완료").first.click(timeout=3000)
            done_clicked = True
            print("   완료 버튼 클릭 (locator)")
        except Exception as e:
            print(f"   완료 버튼 locator 실패: {e}")
        if not done_clicked:
            result_done = page.evaluate("""
                () => {
                    const btn = Array.from(document.querySelectorAll('button'))
                        .find(b => b.offsetParent !== null && (b.innerText||'').trim() === '완료');
                    if (btn) { btn.click(); return true; }
                    return false;
                }
            """)
            print(f"   완료 버튼 JS evaluate: {result_done}")
        time.sleep(5)

        # ── 공개 라디오 선택: Playwright 네이티브 클릭 ──
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        radio_id = page.evaluate("""
            () => {
                const label = Array.from(document.querySelectorAll('label'))
                    .find(l => l.offsetParent !== null && l.innerText.trim() === '공개');
                return label ? label.htmlFor : null;
            }
        """)
        if radio_id:
            try:
                page.click(f"#{radio_id}", timeout=3000)
                print(f"   공개 선택: #{radio_id}")
            except Exception as e:
                print(f"   공개 선택 실패: {e}")
        else:
            try:
                page.locator("xpath=//label[normalize-space(text())='공개']").first.click(timeout=3000)
                print("   공개 선택: XPath")
            except Exception as e:
                print(f"   공개 선택 fallback 실패: {e}")
        time.sleep(2)

        # ── 발행 버튼: Playwright locator 네이티브 클릭 ──
        # JS evaluate.click()은 React 이벤트를 못 트리거함 → locator 사용
        visible_btns = page.evaluate("""
            () => Array.from(document.querySelectorAll('button'))
                 .filter(b => b.offsetParent !== null)
                 .map(b => (b.innerText||'').trim())
                 .filter(t => t)
        """)
        logging.info(f"티스토리 발행 패널 버튼: {visible_btns}")
        publish_kw = next(
            (kw for kw in ['공개 발행', '공개 저장', '발행', '저장'] if kw in visible_btns),
            None
        )
        if publish_kw:
            # Playwright 네이티브 클릭
            clicked_pub = False
            try:
                page.locator("button").filter(has_text=publish_kw).first.click(timeout=3000)
                clicked_pub = True
                print(f"   발행 버튼: {publish_kw} (locator)")
            except Exception as e:
                print(f"   발행 버튼 locator 실패: {e}")
            if not clicked_pub:
                # JS evaluate 폴백
                js_click = page.evaluate(f"""
                    () => {{
                        const kw = {json.dumps(publish_kw)};
                        const btn = Array.from(document.querySelectorAll('button'))
                            .find(b => b.offsetParent !== null && (b.innerText||'').trim() === kw);
                        if (btn) {{ btn.click(); return true; }}
                        return false;
                    }}
                """)
                print(f"   발행 버튼 JS evaluate: {js_click}")
        else:
            # 발행 버튼 못 찾으면 JS evaluate로 직접 시도
            js_fallback = page.evaluate("""
                () => {
                    for (const kw of ['공개 발행', '공개 저장', '발행', '저장']) {
                        const btn = Array.from(document.querySelectorAll('button'))
                            .find(b => b.offsetParent !== null && (b.innerText||'').trim() === kw);
                        if (btn) { btn.click(); return kw; }
                    }
                    return null;
                }
            """)
            if js_fallback:
                print(f"   발행 버튼 JS 폴백: {js_fallback}")
            else:
                print(f"   발행 버튼 없음 (버튼: {visible_btns})")
                logging.warning(f"티스토리 발행 버튼 없음: {visible_btns}")

        # ── URL 변경 대기 (최대 25초, 티스토리는 처리가 느림) ──
        try:
            page.wait_for_url(lambda url: "newpost" not in url, timeout=25000)
        except Exception:
            time.sleep(5)  # 추가 대기 후 URL 재확인
        time.sleep(2)

        # ── 발행 후 URL 확인 ─────────────────────
        cur_url = page.url
        if "newpost" not in cur_url and blog_name in cur_url:
            logging.info(f"티스토리 포스팅 완료: {title}")
            print("   티스토리 ✅")
            return True

        # ── 실패 진단: 에러 메시지/토스트 확인 ──
        error_msgs = page.evaluate("""
            () => {
                const errs = Array.from(document.querySelectorAll(
                    '.error, .alert, [class*="error"], [class*="alert"], [role="alert"]'
                )).filter(e => e.offsetParent && e.innerText.trim());
                const toasts = Array.from(document.querySelectorAll(
                    '[class*="toast"], [class*="snack"], [class*="Toast"]'
                )).filter(e => e.innerText.trim());
                return [...errs, ...toasts].map(e => e.innerText.trim().slice(0, 80));
            }
        """)
        if error_msgs:
            logging.warning(f"티스토리 에러 메시지: {error_msgs}")
            print(f"   에러 메시지: {error_msgs}")

        logging.warning(f"티스토리 발행 불확실 (URL: {cur_url})")
        print(f"   티스토리 ⚠️ (URL: {cur_url[:60]})")

        # ── 쿠키 만료 가능성 → 자동 재로그인 후 1회 재시도 ──
        if "newpost" in cur_url and not _retry:
            print("   티스토리 세션 만료 의심 → 자동 재로그인 시도...")
            if run_tistory_auto_login():
                print("   재로그인 성공 → 재시도 중...")
                context.clear_cookies()
                if TISTORY_COOKIE.exists():
                    context.add_cookies(json.loads(TISTORY_COOKIE.read_text(encoding="utf-8")))
                page2 = context.new_page()
                result2 = post_to_tistory(page2, context, title, html_content, _retry=True)
                page2.close()
                return result2
            else:
                logging.warning("티스토리 재로그인 실패 또는 건너뜀")

        return False

    except Exception as e:
        logging.error(f"티스토리 포스팅 실패: {e}")
        print(f"   티스토리 ❌ {e}")
        return False


def get_tistory_html_for(post_path: Path) -> tuple[str, str] | None:
    """네이버 .txt 파일에 대응하는 티스토리 .html 파일 찾기
    반환: (title, html_content) 또는 None"""
    # 주제_XXX_TISTORY_timestamp.html 패턴 찾기
    stem = post_path.stem  # 예: 주제_알뜰폰절약법_20260420_0728
    parts = stem.split("_")
    # timestamp 부분 추출 (마지막 두 파트: 날짜_시간)
    if len(parts) >= 2:
        ts_suffix = "_".join(parts[-2:])  # 20260420_0728
        tid = "_".join(parts[1:-2]) if len(parts) > 3 else parts[1]  # 알뜰폰절약법
        ts_file = post_path.parent / f"주제_{tid}_TISTORY_{ts_suffix}.html"
        if ts_file.exists():
            html = ts_file.read_text(encoding="utf-8")
            # 제목은 .txt에서 추출한 것 그대로 사용
            title_line = ""
            for line in post_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip().lstrip("#").strip()
                if stripped and len(stripped) > 3 and not stripped.startswith("["):
                    title_line = stripped
                    break
            return title_line, html, ts_file
    return None


def main():
    logging.info("===== 블로그 자동화 시작 =====")
    print("=" * 45)
    print("  네이버 + 티스토리 자동 업로드")
    print("=" * 45)

    config = load_config()
    post_path = get_next_post()

    if not post_path:
        print("❌ posts/ 폴더에 올릴 파일이 없습니다.")
        logging.info("포스팅할 파일 없음")
        return

    title, content = parse_post(post_path)
    print(f"파일: {post_path.name}")
    print(f"제목: {title[:50]}")

    # 티스토리 전용 HTML 파일 확인
    tistory_data = get_tistory_html_for(post_path) if "주제_" in post_path.name else None

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )

        # ── 네이버 발행 ──
        naver_context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        naver_context.grant_permissions(["clipboard-read", "clipboard-write"])
        naver_page = naver_context.new_page()

        print("\n[네이버 업로드 중...]")
        naver_logged = naver_login(naver_page, naver_context, config)
        naver_ok = False
        if naver_logged:
            if extract_svg_markers(content):
                naver_ok = post_to_naver_with_images(naver_page, config, title, content)
            else:
                naver_ok = post_to_naver(naver_page, config, title, content)
        naver_context.close()

        # ── 티스토리 발행 ──
        tistory_ok = False
        print("\n[티스토리 업로드 중...]")
        tistory_context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        tistory_page = tistory_context.new_page()

        if tistory_data:
            ts_title, ts_html, ts_file = tistory_data
            tistory_ok = post_to_tistory(tistory_page, tistory_context, ts_title, ts_html)
            if tistory_ok:
                move_to_posted(ts_file)
        else:
            # 티스토리 전용 HTML 없으면 기존 txt → HTML 변환해서 발행
            ts_html = txt_to_tistory_html(title, content)
            tistory_ok = post_to_tistory(tistory_page, tistory_context, title, ts_html)

        tistory_context.close()
        browser.close()

    if naver_ok:
        move_to_posted(post_path)

    print("\n" + "=" * 45)
    print(f"  네이버    {'✅ 성공' if naver_ok else '❌ 실패'}")
    print(f"  티스토리  {'✅ 성공' if tistory_ok else '❌ 실패'}")
    print("=" * 45)
    logging.info(f"결과 - 네이버:{naver_ok} 티스토리:{tistory_ok}")

if __name__ == "__main__":
    main()