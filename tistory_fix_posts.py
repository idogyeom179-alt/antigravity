"""
티스토리 글 목록 확인 + 중복/불량 정리 (items API 사용)
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

def kakao_login(page, ctx, email, password, blog_name):
    """카카오 자동 로그인"""
    page.goto("https://www.tistory.com/auth/login", wait_until="domcontentloaded")
    time.sleep(3)

    # 카카오 버튼 클릭
    try:
        page.click(".btn_login.link_kakao_id", timeout=5000)
    except:
        try:
            page.click("a:has-text('카카오')", timeout=3000)
        except:
            pass
    time.sleep(3)

    # 카카오 폼 입력
    cur = page.url
    if "kakao" in cur:
        try:
            page.wait_for_selector("#loginId--1", timeout=5000)
            page.fill("#loginId--1", email)
            time.sleep(0.3)
            page.fill("#password--2", password)
            time.sleep(0.3)
            page.click(".btn_g.highlight.submit", timeout=5000)
            print("  카카오 로그인 폼 입력 완료")
        except:
            try:
                for sel in ["input[name='loginId']", "input[type='email']"]:
                    try:
                        page.fill(sel, email, timeout=3000)
                        break
                    except: continue
                for sel in ["input[name='password']", "input[type='password']"]:
                    try:
                        page.fill(sel, password, timeout=3000)
                        break
                    except: continue
                for sel in ["button[type='submit']", ".submit", ".btn_login"]:
                    try:
                        page.click(sel, timeout=3000)
                        break
                    except: continue
            except Exception as e:
                print(f"  폼 오류: {e}")

    # 티스토리 manage 페이지 도착 대기
    for i in range(120):
        time.sleep(1)
        cur = page.url
        if "tistory.com" in cur and ("manage" in cur or ("login" not in cur and "auth" not in cur and "kakao" not in cur)):
            print(f"  ✅ 로그인 성공!")
            break
        if i % 20 == 0 and i > 0:
            print(f"  대기 {i}초...")

    save_cookies(ctx, TISTORY_COOKIE)
    page.goto(f"https://{blog_name}.tistory.com/manage", wait_until="domcontentloaded")
    time.sleep(3)
    return "manage" in page.url or "tistory.com" in page.url

def get_all_posts(page, blog_name):
    """items 키로 모든 글 가져오기"""
    all_posts = []
    for pg in range(1, 10):
        r = page.evaluate(f"""
            async () => {{
                const resp = await fetch(
                    'https://{blog_name}.tistory.com/manage/posts.json?page={pg}&count=50',
                    {{credentials: 'include'}}
                );
                if (!resp.ok) return {{error: resp.status}};
                const data = await resp.json();
                return data;
            }}
        """)
        if not r or isinstance(r, dict) and 'error' in r:
            break

        # items 또는 posts 키 사용
        batch = r.get('items') or r.get('posts') or []
        if not batch:
            print(f"  [페이지 {pg}] 응답: {str(r)[:200]}")
            break

        all_posts.extend(batch)
        total = r.get('totalCount', r.get('total', 0))
        print(f"  페이지 {pg}: {len(batch)}개 (전체 {total}개)")

        if len(all_posts) >= total or len(batch) < 50:
            break
        time.sleep(0.5)

    return all_posts

def main():
    config = load_config()
    blog_name = config["tistory"]["blog_name"]
    email = config["tistory"]["email"]
    password = config["tistory"]["password"]

    print("=" * 55)
    print(f"  티스토리 글 정리 시작: {blog_name}.tistory.com")
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

        # 저장된 쿠키 로드
        if TISTORY_COOKIE.exists():
            with open(TISTORY_COOKIE, "r", encoding="utf-8") as f:
                ctx.add_cookies(json.load(f))

        page = ctx.new_page()

        # 로그인 확인
        page.goto(f"https://{blog_name}.tistory.com/manage", wait_until="domcontentloaded")
        time.sleep(3)

        if "login" in page.url or "auth" in page.url:
            print("  쿠키 만료 → 카카오 자동 로그인...")
            kakao_login(page, ctx, email, password, blog_name)
        else:
            print("  ✅ 쿠키로 자동 로그인")
            save_cookies(ctx, TISTORY_COOKIE)

        # 글 목록 조회
        print("\n  [글 목록 조회]")
        all_posts = get_all_posts(page, blog_name)
        print(f"\n  총 {len(all_posts)}개 글\n")

        # 전체 목록 출력
        print("  ─" * 28)
        for post in all_posts:
            pid = post.get('id')
            title = post.get('title', '(없음)')
            vis = post.get('visibility', post.get('status', '?'))
            print(f"  ID {str(pid):4}: [{str(vis):10}] {title[:50]}")
        print("  ─" * 28)

        # 불량 제목 삭제
        bad_kw = ["main_image", "=====", "[메인 이미지", "━━━", "🖼️ [", "SVG", ".svg"]
        bad_posts = [p for p in all_posts
                     if any(kw in str(p.get('title','')) for kw in bad_kw)]
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
                print(f"  삭제 ID {pid}: '{t[:45]}' → HTTP {r}")
                time.sleep(1)
        else:
            print("\n  ✅ 불량 제목 글 없음")

        # 중복 삭제
        title_map = {}
        for post in all_posts:
            t = post.get('title','')
            pid = int(post.get('id', 0))
            title_map.setdefault(t, []).append(pid)

        dups = {t: ids for t, ids in title_map.items() if len(ids) > 1}
        if dups:
            print(f"\n  [중복 {len(dups)}개 - 최신 ID 유지]")
            for t, ids in dups.items():
                keep = max(ids)
                del_ids = [i for i in ids if i != keep]
                print(f"  '{t[:40]}': 유지 {keep}, 삭제 {del_ids}")
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
        else:
            print("\n  ✅ 중복 없음!")

        # 비공개 → 공개
        bad_ids = {post.get('id') for post in bad_posts}
        private_posts = [p for p in all_posts
                         if str(p.get('visibility','')) in ('PRIVATE', 'private', '0', 'false')
                         and str(p.get('id')) not in bad_ids]
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
                print(f"  공개 ID {pid}: '{t[:40]}' → HTTP {r}")
                time.sleep(1)
        else:
            print("\n  ✅ 모두 공개 상태!")

        print("\n  ✅ 전체 완료!")
        print(f"\n  티스토리 블로그: https://{blog_name}.tistory.com")
        browser.close()

if __name__ == "__main__":
    main()
