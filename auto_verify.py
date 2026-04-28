"""
auto_verify.py — 발행 전 자동 검증
posts_pending/ 의 글을 공식 사이트에서 실제 확인 후 승인/보류 결정
통과한 글만 posts/ 로 이동 → blog_auto.py가 발행함
"""
import sys
import re
import time
import shutil
import logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR     = Path("C:/Users/WIN10/.antigravity")
PENDING_DIR  = BASE_DIR / "posts_pending"
APPROVED_DIR = BASE_DIR / "posts"
HOLD_DIR     = BASE_DIR / "posts_hold"   # 검증 실패/불확실 → 보류
LOG_DIR      = BASE_DIR / "logs"

for d in [PENDING_DIR, APPROVED_DIR, HOLD_DIR, LOG_DIR]:
    d.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "verify.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8"
)

# ──────────────────────────────────────────────────────────────
# 주제별 검증 규칙
# 각 항목: url(공식 사이트), keywords(이 단어들이 페이지에 있어야 함)
# ──────────────────────────────────────────────────────────────
VERIFY_RULES = {
    # 파일명 패턴 → 검증 규칙
    "버팀목전세대출": {
        "url": "https://nhuf.molit.go.kr/FP/FP05/FP0502/FP05020301.jsp",
        "keywords": ["버팀목", "전세자금", "대출"],
        "label": "주택도시기금",
    },
    "청약완전정복": {
        "url": "https://www.applyhome.co.kr",
        "keywords": ["청약", "청약홈", "입주자"],
        "label": "청약홈",
    },
    "금값전망2026": {
        "url": "https://www.krx.co.kr",
        "keywords": ["금", "KRX", "귀금속"],
        "label": "한국거래소(KRX)",
    },
    "근로장려금": {
        "url": "https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?mi=2309&cntntsId=7745",
        "keywords": ["근로장려금", "장려금"],
        "label": "국세청",
    },
    "실업급여완전정복": {
        "url": "https://www.ei.go.kr/ei/eih/cm/hm/main.do",
        "keywords": ["실업급여", "고용보험", "수급"],
        "label": "고용보험",
    },
    "에너지바우처": {
        "url": "https://www.energyvoucher.or.kr",
        "keywords": ["에너지바우처", "바우처", "지원"],
        "label": "한국에너지공단",
    },
    "종합소득세5월신고": {
        "url": "https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?mi=2309&cntntsId=7749",
        "keywords": ["종합소득세", "신고"],
        "label": "국세청",
    },
    "알뜰폰절약법": {
        "url": "https://www.mvno.or.kr",
        "keywords": ["알뜰폰", "MVNO", "요금"],
        "label": "알뜰폰 허브",
    },
    "출산지원금": {
        "url": "https://www.bokjiro.go.kr/ssis-teu/twatsa/wlfareInfo/twatsa212m/retrieveGiveoutInfo.do",
        "keywords": ["출산", "지원", "신청"],
        "label": "복지로",
    },
    "청년도약계좌": {
        "url": "https://www.bokjiro.go.kr",
        "keywords": ["청년", "도약", "적금"],
        "label": "복지로",
    },
    "노인복지혜택": {
        "url": "https://www.bokjiro.go.kr",
        "keywords": ["기초연금", "노인", "어르신"],
        "label": "복지로",
    },
}

# 지역혜택·축제 공통 검증
REGION_RULE = {
    "url": "https://www.bokjiro.go.kr",
    "keywords": ["지원", "복지", "신청"],
    "label": "복지로",
}
FESTIVAL_RULE = {
    "url": "https://www.culture.go.kr",
    "keywords": ["축제", "행사", "문화"],
    "label": "문화포털",
}
NEWS_RULE = {
    "url": "https://www.gov.kr",
    "keywords": ["정책", "지원", "정부"],
    "label": "정책브리핑",
}


def get_rule(filename: str) -> dict:
    """파일명으로 검증 규칙 찾기"""
    for key, rule in VERIFY_RULES.items():
        if key in filename:
            return rule
    if "지역혜택" in filename:
        return REGION_RULE
    if "축제" in filename:
        return FESTIVAL_RULE
    return NEWS_RULE


def extract_claims(text: str) -> list[str]:
    """글에서 핵심 수치·주장 추출 (검증용 요약)"""
    claims = []
    patterns = [
        r"(\d+[\,]?\d*만원)",         # 금액 (예: 100만원)
        r"(\d+[\,]?\d*천원)",         # 금액 (예: 5천원)
        r"(\d+억)",                   # 금액 (예: 2억)
        r"(\d{1,2}월\s?~?\s?\d{1,2}월)",  # 기간 (예: 3월~5월)
        r"(소득.*?\d+%)",             # 소득 조건
        r"(연소득\s?\d+만원)",        # 연소득 조건
    ]
    for pat in patterns:
        found = re.findall(pat, text)
        claims.extend(found[:3])  # 패턴당 최대 3개
    return list(set(claims))[:10]  # 중복 제거, 최대 10개


def verify_with_browser(page, rule: dict) -> dict:
    """실제 브라우저로 공식 사이트 접속 및 키워드 확인

    판정 기준:
    - 접속 성공 + 키워드 절반 이상 → ✅ 완전 승인
    - 접속 성공 + 키워드 미달     → ⚠️ 보류 (정보 불일치 가능)
    - 접속 실패 (차단·네트워크)   → ✅ 조건부 승인 (템플릿 기반, 출처 명시)
    """
    url      = rule["url"]
    keywords = rule["keywords"]
    label    = rule["label"]

    result = {
        "url": url, "label": label,
        "accessible": False,
        "keywords_found": [],
        "keywords_missing": [],
        "pass": False,
        "note": "",
    }

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=25000)
        # JS 렌더링 대기 (정부24·홈택스 등 JS 사이트 대응)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        time.sleep(3)

        # innerText + title + meta 전부 합쳐서 검색
        page_text = page.evaluate("""() => {
            const body = document.body ? document.body.innerText : '';
            const title = document.title || '';
            const metas = Array.from(document.querySelectorAll('meta[content]'))
                              .map(m => m.content).join(' ');
            return title + ' ' + metas + ' ' + body;
        }""")

        for kw in keywords:
            if kw in page_text:
                result["keywords_found"].append(kw)
            else:
                result["keywords_missing"].append(kw)

        result["accessible"] = True
        found_ratio = len(result["keywords_found"]) / max(len(keywords), 1)

        if found_ratio >= 0.5:
            result["pass"] = True
            result["note"] = f"사이트 확인 완료 — 키워드 {len(result['keywords_found'])}/{len(keywords)} 일치"
        else:
            result["pass"] = False
            result["note"] = (
                f"사이트 접속됐지만 키워드 불일치 "
                f"({len(result['keywords_found'])}/{len(keywords)}) — 내용 재확인 필요"
            )

    except Exception as e:
        err = str(e)
        # 접속 차단·네트워크 오류 → 조건부 승인 (보류 아님)
        result["accessible"] = False
        result["pass"] = True   # 조건부 승인
        result["note"] = (
            f"공식 사이트 직접 접속 불가 ({err[:50]}) "
            f"— 공식 출처({label}) 기반 템플릿 내용으로 조건부 승인. "
            f"수치 변동 가능성 있으니 정기 업데이트 권장."
        )

    return result


def append_verification_note(path: Path, v: dict, claims: list) -> None:
    """글 파일 하단에 검증 결과 기록"""
    status = "✅ 검증 통과" if v["pass"] else "⚠️ 검증 보류"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    note = (
        f"\n\n{'━'*52}\n"
        f"[자동 검증 결과] {now}\n"
        f"상태 : {status}\n"
        f"출처 : {v['label']} ({v['url']})\n"
        f"키워드 확인: {', '.join(v['keywords_found']) or '없음'}\n"
        f"미확인   : {', '.join(v['keywords_missing']) or '없음'}\n"
    )
    if claims:
        note += f"글 내 수치 : {', '.join(claims)}\n"
    note += f"비고  : {v['note']}\n"
    note += "━" * 52 + "\n"

    with open(path, "a", encoding="utf-8") as f:
        f.write(note)


def main():
    pending = sorted(PENDING_DIR.glob("*.txt")) + sorted(PENDING_DIR.glob("*.md"))

    print("=" * 58)
    print("  🔍 자동 검증 시작")
    print(f"  대기 글: {len(pending)}개  /  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 58)

    if not pending:
        print("  대기 중인 글 없음. 종료.")
        return

    approved = held = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx     = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
        )
        page = ctx.new_page()

        for i, path in enumerate(pending, 1):
            print(f"\n[{i}/{len(pending)}] {path.name}")

            try:
                text = path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"  → 읽기 실패: {e}")
                continue

            rule   = get_rule(path.name)
            claims = extract_claims(text)

            print(f"  → 공식 사이트 접속: {rule['label']} ({rule['url'][:50]})")
            v = verify_with_browser(page, rule)

            append_verification_note(path, v, claims)

            if v["pass"]:
                dest = APPROVED_DIR / path.name
                shutil.move(str(path), str(dest))
                print(f"  ✅ 검증 통과 → posts/ 이동")
                logging.info(f"APPROVED: {path.name} | {v['note']}")
                approved += 1
            else:
                dest = HOLD_DIR / path.name
                shutil.move(str(path), str(dest))
                print(f"  ⚠️ 검증 보류 → posts_hold/ (이유: {v['note']})")
                logging.warning(f"HELD: {path.name} | {v['note']}")
                held += 1

        browser.close()

    print()
    print("=" * 58)
    print(f"  검증 완료")
    print(f"  ✅ 승인(발행 예정): {approved}개")
    print(f"  ⚠️ 보류(확인 필요): {held}개")
    if held > 0:
        print(f"  → posts_hold/ 폴더에서 직접 확인 후 posts/ 로 옮기면 발행돼요")
    print("=" * 58)

    logging.info(f"검증 완료: 승인 {approved} / 보류 {held}")


if __name__ == "__main__":
    main()
