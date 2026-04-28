"""
review_posts.py — 발행 전 글 검토 & 승인 도구
posts_pending/ 폴더의 글을 하나씩 보여주고
승인하면 posts/ 로 이동 → blog_auto.py가 자동 발행함
"""
import sys
import shutil
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR      = Path("C:/Users/WIN10/.antigravity")
PENDING_DIR   = BASE_DIR / "posts_pending"
APPROVED_DIR  = BASE_DIR / "posts"
REJECTED_DIR  = BASE_DIR / "posts_rejected"

for d in [PENDING_DIR, APPROVED_DIR, REJECTED_DIR]:
    d.mkdir(exist_ok=True)

DIVIDER     = "─" * 58
DIVIDER_BIG = "═" * 58

# 글 종류별 공식 출처 안내
SOURCE_HINT = {
    "주제_": "공식 출처: 글 상단 ✅ 검증 안내 박스 확인",
    "지역혜택": "공식 출처: 복지로(bokjiro.go.kr) · 정부24(gov.kr)",
    "축제_":   "공식 출처: 문화포털(culture.go.kr) · 한국관광공사(visitkorea.or.kr)",
    "수집_":   "공식 출처: 네이버 뉴스 수집 글 — 원문 링크 확인 권장",
}


def get_source_hint(filename: str) -> str:
    for prefix, hint in SOURCE_HINT.items():
        if prefix in filename:
            return hint
    return "글 내용에서 출처 직접 확인"


def show_post(path: Path, idx: int, total: int) -> None:
    """글 내용을 보기 좋게 출력"""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    print(f"\n{DIVIDER_BIG}")
    print(f"  [{idx}/{total}]  {path.name}")
    print(f"  종류: {get_source_hint(path.name)}")
    print(DIVIDER_BIG)

    # 첫 40줄 미리보기 (너무 길면 잘라서 표시)
    preview = lines[:40]
    for line in preview:
        print(line)

    if len(lines) > 40:
        print(f"\n  ... (이하 {len(lines)-40}줄 생략) ...")

    print(DIVIDER)
    print(f"  📄 전체 {len(lines)}줄 / {len(text)}자")


def prompt_action() -> str:
    """사용자 입력 받기"""
    print()
    print("  ✅ Y  → 승인 (posts/ 로 이동, 다음 발행 때 올라감)")
    print("  ❌ N  → 거절 (posts_rejected/ 로 이동, 발행 안 함)")
    print("  ⏩ S  → 건너뛰기 (나중에 다시 검토)")
    print("  📄 F  → 전체 내용 보기")
    print("  🚪 Q  → 검토 종료")
    print()
    while True:
        raw = input("  선택 [Y/N/S/F/Q]: ").strip().upper()
        if raw in ("Y", "N", "S", "F", "Q"):
            return raw
        print("  Y, N, S, F, Q 중 하나를 입력하세요.")


def show_full(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    print(f"\n{DIVIDER_BIG}")
    print(text)
    print(DIVIDER_BIG)


def main():
    pending = sorted(PENDING_DIR.glob("*.txt")) + sorted(PENDING_DIR.glob("*.md"))

    print(DIVIDER_BIG)
    print("  📋 발행 전 글 검토 도구")
    print(f"  대기 중인 글: {len(pending)}개")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(DIVIDER_BIG)

    if not pending:
        print("\n  대기 중인 글이 없어요. 이미 다 검토했거나 아직 수집 전이에요.")
        return

    approved = rejected = skipped = 0

    for idx, path in enumerate(pending, 1):
        show_post(path, idx, len(pending))

        while True:
            action = prompt_action()

            if action == "F":
                show_full(path)
                continue

            if action == "Y":
                dest = APPROVED_DIR / path.name
                shutil.move(str(path), str(dest))
                print(f"\n  ✅ 승인됨 → posts/{path.name}")
                approved += 1

            elif action == "N":
                dest = REJECTED_DIR / path.name
                shutil.move(str(path), str(dest))
                print(f"\n  ❌ 거절됨 → posts_rejected/{path.name}")
                rejected += 1

            elif action == "S":
                print(f"\n  ⏩ 건너뜀 (posts_pending/ 에 그대로 보관)")
                skipped += 1

            elif action == "Q":
                print(f"\n  🚪 검토 중단")
                break

            break

        if action == "Q":
            break

    print()
    print(DIVIDER_BIG)
    print(f"  검토 완료!")
    print(f"  ✅ 승인: {approved}개  ❌ 거절: {rejected}개  ⏩ 건너뜀: {skipped}개")
    if approved > 0:
        print(f"  → 승인된 {approved}개는 다음 발행 시간(오전 10시 / 오후 5시)에 자동 업로드돼요.")
    print(DIVIDER_BIG)


if __name__ == "__main__":
    main()
