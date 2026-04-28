"""
티스토리 재로그인 + 글 목록 확인 + 중복/불량 글 정리
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

    print("=" * 55)
    print(f"  티스토리 블로그: {blog_name}.tistory.com")
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

        # 기존 쿠키 시도
        if TISTORY_COOKIE.exists():
            with open(TISTORY_COOKIE, "r", encoding="utf-8") as f:
                ctx.add_cookies(json.load(f))

        page = ctx.new_page()
        page.goto(f"https://{blog_name}.tistory.com/manage", wait_until="domcontentloaded")
        time.sleep(3)

        if "login" in page.url or "auth" in page.url:
            print("\n  브라우저에서 카카오 로그인 해주세요! (5분)")
            page.goto("https://www.tistory.com/auth/login", wait_until="domcontentloaded")
            page.bring_to_front()
            logged_in = False
            for i in range(300):
                time.sleep(1)
                cur = page.url
                cookies = ctx.cookies()
                has_session = any(c["name"] in ("TSSESSION", "TIARA") for c in cookies)
                if has_session and "tistory.com" in cur and "login" not in cur and "auth" not in cur:
                    logged_in = True
                    break
                if i % 10 == 0:
                    print(f"  대기중... {i}초")
            if logged_in:
                save_cookies(ctx, TISTORY_COOKIE)
                print("  ✅ 로그인 성공! 쿠키 저장 완료")
            else:
                print("  ❌ 로그인 실패 또는 타임아웃")
                browser.close()
                return
        else:
            print(f"  ✅ 자동 로그인 성공")
            save_cookies(ctx, TISTORY_COOKIE)

        # 글 목록 조회
        print("\n  글 목록 조회 중...")
        page.goto(f"https://{blog_name}.tistory.com/manage", wait_until="domcontentloaded")
        time.sleep(2)

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
            if not r or 'posts' not in r:
                break
            batch = r.get('posts', [])
            all_posts.extend(batch)
            if len(batch) < 50:
                break

        print(f"  총 {len(all_posts)}개 글\n")

        if not all_posts:
            print("  ⚠️ 글이 없거나 API 오류")
            input("Enter 종료...")
            browser.close()
            return

        # 전체 목록 출력
        print("  [현재 글 목록]")
        for post in all_posts:
            pid = post.get('id')
            title = post.get('title', '(제목없음)')
            vis = post.get('visibility', '?')
            print(f"    ID {pid:3}: [{vis:7}] {title[:55]}")

        # 잘못된 제목 감지
        bad_posts = []
        for post in all_posts:
            t = post.get('title', '')
            if any(kw in t for kw in ["main_image", "=====", "[메인 이미지", "━━━", "🖼️ ["]):
                bad_posts.append(post)

        if bad_posts:
            print(f"\n  [잘못된 제목 {len(bad_posts)}개 - 삭제]")
            for post in bad_posts:
                pid = post.get('id')
                t = post.get('title', '')
                r = page.evaluate(f"""
                    async () => {{
                        const resp = await fetch(
                            'https://{blog_name}.tistory.com/manage/post/{pid}.json',
                            {{method: 'DELETE', credentials: 'include'}}
                        );
                        return resp.status;
                    }}
                """)
                print(f"    삭제 ID {pid}: '{t[:40]}' → HTTP {r}")
                time.sleep(1)

        # 중복 제목 감지
        title_map = {}
        for post in all_posts:
            t = post.get('title', '')
            if t not in title_map:
                title_map[t] = []
            title_map[t].append(post.get('id'))

        dups = {t: ids for t, ids in title_map.items() if len(ids) > 1}
        if dups:
            print(f"\n  [중복 글 {len(dups)}개 - 최신만 유지]")
            for t, ids in dups.items():
                keep = max(ids)
                print(f"    제목: '{t[:40]}'")
                print(f"    IDs: {ids}  → 유지: {keep}")
                for del_id in ids:
                    if del_id != keep:
                        r = page.evaluate(f"""
                            async () => {{
                                const resp = await fetch(
                                    'https://{blog_name}.tistory.com/manage/post/{del_id}.json',
                                    {{method: 'DELETE', credentials: 'include'}}
                                );
                                return resp.status;
                            }}
                        """)
                        print(f"    삭제 ID {del_id}: HTTP {r}")
                        time.sleep(1)
        else:
            print("\n  ✅ 중복 없음!")

        # 비공개 글 공개 전환
        private_posts = [p for p in all_posts if p.get('visibility') == 'PRIVATE'
                         and p.get('id') not in [bp.get('id') for bp in bad_posts]]
        if private_posts:
            print(f"\n  [비공개 {len(private_posts)}개 → 공개 전환]")
            for post in private_posts:
                pid = post.get('id')
                t = post.get('title', '')
                r = page.evaluate(f"""
                    async () => {{
                        const resp = await fetch(
                            'https://{blog_name}.tistory.com/manage/post/{pid}.json',
                            {{
                                method: 'PUT',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{visibility: 'PUBLIC'}}),
                                credentials: 'include'
                            }}
                        );
                        return resp.status;
                    }}
                """)
                print(f"    공개 ID {pid}: '{t[:40]}' → HTTP {r}")
                time.sleep(1)
        else:
            print("\n  ✅ 비공개 글 없음 (이미 모두 공개)")

        print("\n  완료!")
        input("  [Enter] 브라우저 닫기...")
        browser.close()

if __name__ == "__main__":
    main()
