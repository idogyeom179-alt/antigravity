"""
region_daily.py
매일 1개 지역 혜택 포스트 자동 생성 + 네이버/티스토리 업로드
17개 지역을 순환 (하루 1개씩 → 17일에 전 지역 완료)
충북(영동군) 포함 시 군별 특집 혜택도 함께 게시됨
"""
import sys, time, subprocess, logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

# region_collect.py 에서 데이터와 생성 함수 가져오기
from region_collect import (
    REGIONS,
    generate_region_post,
    svg_to_png,
    make_region_banner_svg,
    make_hashtag_svg,
)

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR        = Path("C:/Users/WIN10/.antigravity")
POSTS_DIR       = BASE_DIR / "posts"          # blog_auto.py 가 읽는 폴더
BLOG_IMAGES_DIR = BASE_DIR / "blog_images"
LOG_DIR         = BASE_DIR / "logs"

for d in [POSTS_DIR, BLOG_IMAGES_DIR, LOG_DIR]:
    d.mkdir(exist_ok=True)

try:
    logging.basicConfig(
        filename=LOG_DIR / "region_daily.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8"
    )
except Exception:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def pick_today_region() -> dict:
    """오늘의 지역 선택 — 연도+월일 기반으로 17개 순환"""
    now = datetime.now()
    # 2026-01-01 기준 경과일로 인덱스 결정 (매일 다른 지역)
    from datetime import date
    base = date(2026, 1, 1)
    today = date(now.year, now.month, now.day)
    day_offset = (today - base).days
    idx = day_offset % len(REGIONS)
    return REGIONS[idx], idx


def main():
    now       = datetime.now()
    today_str = now.strftime("%Y년 %m월 %d일")
    timestamp = now.strftime("%Y%m%d_%H%M")

    region, idx = pick_today_region()
    name = region["name"]
    emoji = region["emoji"]

    print("=" * 55)
    print(f"  🗺️ 오늘의 지역: {emoji} {name} (순번 {idx+1}/17)")
    print(f"  ({now.strftime('%Y-%m-%d %H:%M')})")
    print("=" * 55)
    logging.info(f"===== 지역별 포스트 시작: {name} =====")

    banner_name = f"region_{name}_{timestamp}.png"
    tag_name    = f"region_tags_{timestamp}.png"

    # ── 1. 이미지 생성 ──────────────────────────────────────
    print(f"\n[1] {name} 포스트 이미지 생성 중...")
    ok_count = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(viewport={"width": 1280, "height": 900})
        page    = ctx.new_page()

        if svg_to_png(page, make_region_banner_svg(region, today_str),
                      BLOG_IMAGES_DIR / banner_name):
            ok_count += 1
        if svg_to_png(page, make_hashtag_svg(region),
                      BLOG_IMAGES_DIR / tag_name):
            ok_count += 1

        browser.close()
    print(f"  이미지 {ok_count}/2개 생성 완료 ✅")

    # ── 2. 블로그 포스트 생성 ──────────────────────────────
    print(f"\n[2] {name} 포스트 본문 생성 중...")
    content  = generate_region_post(region, today_str, banner_name, tag_name)
    filename = f"{name}_혜택_{timestamp}.txt"
    post_path = POSTS_DIR / filename
    post_path.write_text(content, encoding="utf-8")
    print(f"  저장: {filename} ✅")
    logging.info(f"포스트 저장: {filename}")

    # ── 3. 네이버 + 티스토리 자동 업로드 ────────────────────
    print(f"\n[3] {name} 포스트 업로드 중...")
    try:
        result = subprocess.run(
            ["python", str(BASE_DIR / "blog_auto.py")],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=360
        )
        print(result.stdout)
        if result.returncode == 0:
            print(f"  {name} 업로드 완료 ✅")
            logging.info(f"{name} 업로드 완료")
        else:
            print(f"  {name} 업로드 실패 ❌\n{result.stderr[:300]}")
            logging.error(f"{name} 업로드 실패: {result.stderr[:300]}")
    except Exception as e:
        print(f"  업로드 오류: {e}")
        logging.error(f"업로드 오류: {e}")

    print("\n" + "=" * 55)
    print(f"  {emoji} {name} 지역혜택 포스팅 완료! 🎉")
    print("=" * 55)
    logging.info(f"===== {name} 포스팅 완료 =====")


if __name__ == "__main__":
    main()
