"""
post_all.py
posts_pending/ 폴더의 모든 포스트를 순서대로 네이버+티스토리에 자동 발행
- 파일 하나씩 posts/ 로 이동 → blog_auto.py 실행 → 완료 후 posts_pending/ 에서 삭제
- Naver 성공 여부와 무관하게 모두 처리 (실패 시 로그 기록)
"""
import sys
import subprocess
import shutil
import logging
import time
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR     = Path("C:/Users/WIN10/.antigravity")
PENDING_DIR  = BASE_DIR / "posts_pending"
POSTS_DIR    = BASE_DIR / "posts"
POSTED_DIR   = BASE_DIR / "posted"
LOG_DIR      = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "post_all.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

DELAY_BETWEEN = 15   # 포스트 사이 대기 시간(초)
TIMEOUT_SEC   = 360  # 포스트 1개당 최대 대기 시간(초)


def get_pending() -> list[Path]:
    return sorted(PENDING_DIR.glob("*.txt")) + sorted(PENDING_DIR.glob("*.md"))


def run_blog_auto() -> tuple[bool, bool]:
    """blog_auto.py 실행 → (naver_ok, tistory_ok) 반환"""
    try:
        result = subprocess.run(
            ["python", "-X", "utf8", str(BASE_DIR / "blog_auto.py")],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=TIMEOUT_SEC,
        )
        out = result.stdout or ""
        print(out)
        naver_ok    = "네이버    ✅" in out or "네이버 ✅" in out
        tistory_ok  = "티스토리  ✅" in out or "티스토리 ✅" in out
        return naver_ok, tistory_ok
    except subprocess.TimeoutExpired:
        print("  ⚠️ blog_auto.py 타임아웃")
        logging.warning("blog_auto.py 타임아웃")
        return False, False
    except Exception as e:
        print(f"  ❌ blog_auto.py 실행 오류: {e}")
        logging.error(f"blog_auto.py 실행 오류: {e}")
        return False, False


def main():
    pending = get_pending()
    total   = len(pending)

    if total == 0:
        print("posts_pending/ 에 발행할 파일이 없습니다.")
        return

    print("=" * 55)
    print(f"  📤 일괄 발행 시작  —  총 {total}개")
    print(f"  ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("=" * 55)
    logging.info(f"===== post_all 시작: {total}개 =====")

    naver_ok_total = tistory_ok_total = fail_total = 0

    for idx, post_path in enumerate(pending, 1):
        print(f"\n[{idx}/{total}] {post_path.name}")
        logging.info(f"[{idx}/{total}] 시작: {post_path.name}")

        # 1. posts/ 로 복사
        dest = POSTS_DIR / post_path.name
        try:
            shutil.copy2(str(post_path), str(dest))
        except Exception as e:
            print(f"  복사 실패: {e}")
            logging.error(f"복사 실패 {post_path.name}: {e}")
            fail_total += 1
            continue

        # 2. blog_auto.py 실행
        naver_ok, tistory_ok = run_blog_auto()

        # 3. posts/ 에 파일이 남아있으면 직접 제거 (blog_auto가 이미 posted/ 로 옮겼을 수도 있음)
        if dest.exists():
            dest.unlink()

        # 4. 성공 시 posts_pending/ 에서 원본 삭제
        if naver_ok:
            post_path.unlink(missing_ok=True)
            naver_ok_total += 1
            if tistory_ok:
                tistory_ok_total += 1
            logging.info(
                f"완료: {post_path.name}  "
                f"네이버:{'✅' if naver_ok else '❌'}  "
                f"티스토리:{'✅' if tistory_ok else '❌'}"
            )
        else:
            fail_total += 1
            logging.warning(f"발행 실패 (파일 유지): {post_path.name}")
            print(f"  ⚠️ 네이버 실패 — posts_pending/ 에 파일 유지")

        # 5. 다음 포스트 전 대기 (마지막이면 생략)
        if idx < total:
            remaining = total - idx
            print(f"  ⏳ {DELAY_BETWEEN}초 대기 중... (남은 {remaining}개)")
            time.sleep(DELAY_BETWEEN)

    print()
    print("=" * 55)
    print(f"  📊 일괄 발행 완료")
    print(f"  네이버  성공: {naver_ok_total}개")
    print(f"  티스토리 성공: {tistory_ok_total}개")
    print(f"  실패/건너뜀: {fail_total}개")
    print("=" * 55)
    logging.info(
        f"===== post_all 완료  네이버:{naver_ok_total}  "
        f"티스토리:{tistory_ok_total}  실패:{fail_total} ====="
    )


if __name__ == "__main__":
    main()
