"""
네이버 블로그 소개글 자동 업데이트
admin.blog.naver.com 에서 소개글을 직접 수정합니다.
"""
import json
import time
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR     = Path("C:/Users/WIN10/.antigravity")
NAVER_COOKIE = BASE_DIR / "naver_cookies.json"
BLOG_ID      = "jiji090"
MANAGE_URL   = f"https://admin.blog.naver.com/AdminMain.naver?blogId={BLOG_ID}&Redirect=Basicinfo"

NEW_INTRO = (
    "🐋 안녕하세요! 고래가 안내하는 혜택 정보 블로그예요\n"
    "나라에서 주는 돈, 신청 안 하면 그냥 내 돈 버리는 거예요!\n"
    "정부 혜택, 지원금, 대출, 세금, 생활비 절약법까지 알면 진짜 이득이 되는 정보만 골라서 올려드려요.\n"
    "📅 매주 월요일 - 전국 지역별 지원금 BEST 5\n"
    "📅 매주 목요일 - 전국 축제 행사 총정리\n"
    "버팀목대출, 청약, 전세자금, 종합소득세, 근로장려금, 에너지바우처, 실업급여, 알뜰폰, 금값 재테크까지!\n"
    "모든 정보는 공식 자료 기반이며, 공감과 이웃추가 하시면 매일 유용한 정보 받아볼 수 있어요!"
)


def load_cookies(context):
    if NAVER_COOKIE.exists():
        with open(NAVER_COOKIE, "r", encoding="utf-8") as f:
            context.add_cookies(json.load(f))
        print("✅ 네이버 쿠키 로드 완료")
        return True
    print("❌ 쿠키 파일 없음")
    return False


def save_cookies(context):
    with open(NAVER_COOKIE, "w", encoding="utf-8") as f:
        json.dump(context.cookies(), f)
    print("✅ 쿠키 저장 완료")


def ensure_login(page, context):
    page.goto("https://www.naver.com", wait_until="domcontentloaded")
    time.sleep(2)
    if any(c["name"] == "NID_AUT" for c in context.cookies()):
        print("✅ 자동 로그인 성공")
        return True

    print("\n┌─────────────────────────────────────────┐")
    print("│  브라우저에서 네이버 로그인 해주세요!    │")
    print("│  로그인하면 자동으로 다음으로 넘어가요   │")
    print("└─────────────────────────────────────────┘")
    page.goto("https://nid.naver.com/nidlogin.login", wait_until="domcontentloaded")
    page.bring_to_front()
    for _ in range(300):
        time.sleep(1)
        try:
            if any(c["name"] == "NID_AUT" for c in context.cookies()):
                save_cookies(context)
                print("✅ 로그인 성공")
                return True
        except:
            pass
    return False


def fill_and_save_intro(page):
    """관리 페이지에서 소개글 입력 후 저장"""
    print(f"\n관리 페이지로 이동: {MANAGE_URL}")
    page.goto(MANAGE_URL, wait_until="domcontentloaded")
    time.sleep(5)
    page.bring_to_front()

    cur_url = page.url
    print(f"현재 URL: {cur_url}")

    # 모든 프레임(중첩 iframe 포함)에서 textarea 탐색
    all_frames = page.frames
    print(f"프레임 수: {len(all_frames)}")

    for i, frame in enumerate(all_frames):
        frame_url = frame.url
        print(f"  프레임[{i}]: {frame_url[:70]}")
        try:
            # 소개글 textarea 찾기
            ta = frame.query_selector("textarea[name*='intro'], textarea[id*='intro'], #blogIntro")
            if ta and ta.is_visible():
                print(f"  → ✅ 소개글 textarea 발견! (프레임[{i}])")

                # 기존 내용 확인
                cur_val = frame.evaluate("el => el.value", ta)
                print(f"  → 현재 내용: {cur_val[:50]}...")

                # JavaScript로 내용 채우기 (가장 확실한 방법)
                frame.evaluate(
                    f"el => {{ el.value = {json.dumps(NEW_INTRO)}; el.dispatchEvent(new Event('input')); el.dispatchEvent(new Event('change')); }}",
                    ta
                )
                time.sleep(0.5)
                # 실제 입력됐는지 확인
                new_val = frame.evaluate("el => el.value", ta)
                print(f"  → ✅ 새 소개글 입력 완료! (길이: {len(new_val)}자)")

                # 저장 버튼 탐색
                save_selectors = [
                    "button:has-text('확인')",
                    "button:has-text('저장')",
                    "a:has-text('확인')",
                    "a:has-text('저장')",
                    "input[type='submit']",
                    "input[value='확인']",
                    "input[value='저장']",
                    ".btn_confirm",
                    ".btn_save",
                    "#btn_confirm",
                    "#btn_save",
                    "button[type='submit']",
                ]
                saved = False
                for sel in save_selectors:
                    try:
                        btn = frame.query_selector(sel)
                        if btn and btn.is_visible():
                            btn_text = btn.inner_text().strip() or btn.get_attribute("value") or ""
                            print(f"  → 저장 버튼 발견: [{btn_text}] ({sel})")
                            btn.click()
                            time.sleep(2)
                            print(f"  → ✅ 저장 클릭 완료!")
                            saved = True
                            break
                    except:
                        pass

                if not saved:
                    # 버튼을 못 찾으면 JavaScript로 폼 서밋 시도
                    print("  → 버튼 미발견, JS 폼 서밋 시도...")
                    try:
                        frame.evaluate("""
                            () => {
                                const form = document.querySelector('form');
                                if (form) form.submit();
                            }
                        """)
                        time.sleep(2)
                        saved = True
                        print("  → ✅ 폼 서밋 완료!")
                    except Exception as e:
                        print(f"  → ❌ 폼 서밋 실패: {e}")

                # 모든 저장 시도 후 버튼 리스트 출력
                if not saved:
                    print("\n  → 저장 버튼 목록 (전체):")
                    btns = frame.eval_on_selector_all(
                        "button, input[type='submit'], input[type='button'], a.btn",
                        "els => els.map(e => ({tag: e.tagName, text: (e.innerText||e.value||'').trim().slice(0,20), id: e.id, cls: e.className.slice(0,30)}))"
                    )
                    for b in btns:
                        print(f"      {b}")

                return saved

        except Exception as e:
            print(f"  → 프레임[{i}] 오류: {e}")

    print("❌ 소개글 textarea를 찾지 못했습니다.")
    print("   페이지를 스크린샷으로 저장합니다...")
    page.screenshot(path=str(BASE_DIR / "blog_images" / "manage_page_debug.png"))
    print(f"   → 저장됨: blog_images/manage_page_debug.png")
    return False


def main():
    print("=" * 58)
    print("  네이버 블로그 소개글 자동 업데이트")
    print(f"  대상: blog.naver.com/{BLOG_ID}")
    print("=" * 58)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=80)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        load_cookies(context)

        if not ensure_login(page, context):
            print("❌ 로그인 실패")
            browser.close()
            return

        success = fill_and_save_intro(page)

        if success:
            print("\n✅ 블로그 소개글 업데이트 성공!")
        else:
            print("\n❌ 자동 저장 실패 — 스크린샷 확인 후 수동 저장 필요")

        time.sleep(3)
        browser.close()
        print("완료.")


if __name__ == "__main__":
    main()
