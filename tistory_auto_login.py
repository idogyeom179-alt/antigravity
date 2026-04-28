"""
카카오 계정으로 티스토리 자동 로그인 + 쿠키 저장 + 글 목록 확인
"""
import json
import time
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path("C:/Users/WIN10/.antigravity")
TISTORY_COOKIE = BASE_DIR / "tistory_cookies.json"
CONFIG_PATH = BASE_DIR / "config.json"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cookies(context, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(context.cookies(), f, ensure_ascii=False, indent=2)

def main():
    config = load_config()
    blog_name = config["tistory"]["blog_name"]
    email = config["tistory"]["email"]
    password = config["tistory"]["password"]

    print("=" * 55)
    print(f"  티스토리 자동 로그인 시작")
    print(f"  블로그: {blog_name}.tistory.com")
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

        page = ctx.new_page()

        # 티스토리 로그인 페이지
        print("  티스토리 로그인 페이지 이동...")
        page.goto("https://www.tistory.com/auth/login", wait_until="domcontentloaded")
        time.sleep(3)

        # 카카오 로그인 버튼 클릭
        print("  카카오 로그인 버튼 클릭...")
        try:
            page.click(".btn_login.link_kakao_id", timeout=5000)
        except:
            try:
                page.click("a:has-text('카카오')", timeout=5000)
            except:
                try:
                    page.click("button:has-text('카카오')", timeout=5000)
                except:
                    # 카카오 로그인 URL 직접 이동
                    page.goto("https://accounts.kakao.com/login?continue=https%3A%2F%2Fkauth.kakao.com%2Foauth%2Fauthorize%3Fresponse_type%3Dcode%26redirect_uri%3Dhttps%253A%252F%252Fwww.tistory.com%252Fauth%252Fkakao%26client_id%3Df378a788fe3c1f5ec1d71ec2eb36f6ee%26state%3D",
                               wait_until="domcontentloaded")
        time.sleep(3)

        cur_url = page.url
        print(f"  현재 URL: {cur_url[:80]}")

        # 카카오 로그인 폼 입력
        if "kakao" in cur_url or "accounts.kakao" in cur_url:
            print("  카카오 로그인 폼 입력 중...")
            try:
                # 이메일 입력
                page.wait_for_selector("#loginId--1", timeout=5000)
                page.fill("#loginId--1", email)
                time.sleep(0.5)
                # 비밀번호 입력
                page.fill("#password--2", password)
                time.sleep(0.5)
                # 로그인 버튼 클릭
                page.click(".btn_g.highlight.submit", timeout=5000)
                print("  로그인 버튼 클릭!")
            except:
                try:
                    # 다른 셀렉터 시도
                    for email_sel in ["input[name='loginId']", "input[type='email']", "#loginId"]:
                        try:
                            page.wait_for_selector(email_sel, timeout=3000)
                            page.fill(email_sel, email)
                            break
                        except:
                            continue

                    for pw_sel in ["input[name='password']", "input[type='password']", "#password"]:
                        try:
                            page.fill(pw_sel, password)
                            break
                        except:
                            continue

                    for btn_sel in ["button[type='submit']", ".btn_login", ".submit"]:
                        try:
                            page.click(btn_sel, timeout=3000)
                            break
                        except:
                            continue
                    print("  대체 셀렉터로 로그인 시도")
                except Exception as e:
                    print(f"  로그인 폼 오류: {e}")
                    print("  수동으로 로그인 해주세요 (3분)...")

        # 로그인 완료 대기
        print("  로그인 완료 대기 중...")
        for i in range(180):
            time.sleep(1)
            cur = page.url
            cookies = ctx.cookies()
            # TSSESSION 또는 manage 페이지 도착 확인
            has_ts = any(c["name"] == "TSSESSION" for c in cookies)
            on_manage = "tistory.com" in cur and "manage" in cur
            on_home = "tistory.com" in cur and "login" not in cur and "auth" not in cur and "kakao" not in cur

            if has_ts or on_manage:
                print(f"  ✅ 로그인 성공! (URL: {cur[:60]})")
                save_cookies(ctx, TISTORY_COOKIE)
                print(f"  쿠키 저장 완료 ({len(cookies)}개)")
                break
            if i % 15 == 0 and i > 0:
                print(f"  대기중... {i}초 / URL: {cur[:50]}")
        else:
            print("  ❌ 로그인 타임아웃")
            try:
                input("수동 로그인 후 Enter 누르면 계속...")
            except (EOFError, KeyboardInterrupt):
                pass
            save_cookies(ctx, TISTORY_COOKIE)

        # 관리 페이지 이동
        page.goto(f"https://{blog_name}.tistory.com/manage", wait_until="domcontentloaded")
        time.sleep(3)
        print(f"\n  관리 페이지 URL: {page.url}")

        # 글 목록 조회
        print("\n  [글 목록 조회]")
        all_posts = []
        for pg in range(1, 5):
            r = page.evaluate(f"""
                async () => {{
                    const resp = await fetch(
                        'https://{blog_name}.tistory.com/manage/posts.json?page={pg}&count=50',
                        {{credentials: 'include'}}
                    );
                    if (!resp.ok) return null;
                    return await resp.json();
                }}
            """)
            if not r or not isinstance(r, dict) or 'posts' not in r:
                print(f"    페이지 {pg}: 응답 없음/오류 → {str(r)[:100]}")
                break
            batch = r.get('posts', [])
            all_posts.extend(batch)
            print(f"    페이지 {pg}: {len(batch)}개")
            if len(batch) < 50:
                break
            time.sleep(1)

        print(f"\n  총 {len(all_posts)}개 글\n")

        for post in all_posts:
            pid = post.get('id')
            title = post.get('title', '(없음)')
            vis = post.get('visibility', '?')
            print(f"    ID {pid:3}: [{vis:8}] {title[:55]}")

        # 불량 제목 삭제
        bad_kw = ["main_image", "=====", "[메인 이미지", "━━━", "🖼️ ["]
        bad_posts = [p for p in all_posts if any(kw in p.get('title','') for kw in bad_kw)]
        if bad_posts:
            print(f"\n  [불량 글 {len(bad_posts)}개 삭제]")
            for post in bad_posts:
                pid = post.get('id')
                t = post.get('title','')
                r = page.evaluate(f"""
                    async () => {{
                        const resp = await fetch(
                            'https://{blog_name}.tistory.com/manage/post/{pid}.json',
                            {{method:'DELETE', credentials:'include'}}
                        );
                        return resp.status;
                    }}
                """)
                print(f"    삭제 ID {pid}: '{t[:40]}' → {r}")
                time.sleep(1)

        # 중복 제목 삭제
        title_map = {}
        for post in all_posts:
            t = post.get('title','')
            title_map.setdefault(t, []).append(post.get('id'))
        dups = {t:ids for t,ids in title_map.items() if len(ids)>1}
        if dups:
            print(f"\n  [중복 {len(dups)}개 - 최신 유지]")
            for t, ids in dups.items():
                keep = max(ids)
                del_ids = [i for i in ids if i != keep]
                print(f"    '{t[:40]}': 유지 {keep}, 삭제 {del_ids}")
                for del_id in del_ids:
                    r = page.evaluate(f"""
                        async () => {{
                            const resp = await fetch(
                                'https://{blog_name}.tistory.com/manage/post/{del_id}.json',
                                {{method:'DELETE', credentials:'include'}}
                            );
                            return resp.status;
                        }}
                    """)
                    print(f"    삭제 {del_id}: HTTP {r}")
                    time.sleep(1)

        # 비공개 → 공개
        private_posts = [p for p in all_posts
                         if p.get('visibility') == 'PRIVATE'
                         and p.get('id') not in [bp.get('id') for bp in bad_posts]]
        if private_posts:
            print(f"\n  [비공개 {len(private_posts)}개 → 공개]")
            for post in private_posts:
                pid = post.get('id')
                t = post.get('title','')
                r = page.evaluate(f"""
                    async () => {{
                        const resp = await fetch(
                            'https://{blog_name}.tistory.com/manage/post/{pid}.json',
                            {{
                                method: 'PUT',
                                headers: {{'Content-Type':'application/json'}},
                                body: JSON.stringify({{visibility:'PUBLIC'}}),
                                credentials: 'include'
                            }}
                        );
                        return resp.status;
                    }}
                """)
                print(f"    공개 ID {pid}: '{t[:40]}' → HTTP {r}")
                time.sleep(1)
        else:
            print("\n  ✅ 모든 글 이미 공개 상태")

        print("\n  ✅ 완료!")
        try:
            input("  [Enter] 브라우저 닫기...")
        except (EOFError, KeyboardInterrupt):
            pass
        browser.close()

if __name__ == "__main__":
    main()
