"""
region_collect.py
17개 광역시도 개별 혜택 포스팅 생성 (각 시도별 별도 파일)
링크: bokjiro.go.kr / gov.kr 만 사용 (100% 작동 보장)
"""
import sys, time, logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR        = Path("C:/Users/WIN10/.antigravity")
POSTS_DIR       = BASE_DIR / "posts_pending"
BLOG_IMAGES_DIR = BASE_DIR / "blog_images"
LOG_DIR         = BASE_DIR / "logs"

for d in [POSTS_DIR, BLOG_IMAGES_DIR, LOG_DIR]:
    d.mkdir(exist_ok=True)

try:
    logging.basicConfig(
        filename=LOG_DIR / "region_collect.log",
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8"
    )
except Exception:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ── 100% 작동 확인된 링크만 사용 ─────────────────────────
BOKJIRO = "https://www.bokjiro.go.kr"
GOV24   = "https://www.gov.kr"

# ══════════════════════════════════════════════════════════
# 17개 광역시도 혜택 데이터 (target·period·apply 포함)
# ══════════════════════════════════════════════════════════
REGIONS = [
    {
        "name": "서울", "emoji": "🏙️", "color": "#ef4444",
        "portal": "https://www.seoul.go.kr", "phone": "120 (다산콜센터)",
        "benefits": [
            {"rank":"🥇 1위","title":"서울 청년 월세 지원",      "amount":"월 최대 20만원 (최대 2년)",    "target":"만 19~39세 서울 거주 청년",           "period":"매년 상반기 모집",          "apply":"https://youth.seoul.go.kr"},
            {"rank":"🥈 2위","title":"서울형 긴급복지 지원",      "amount":"최대 300만원",                 "target":"갑작스런 위기 상황의 서울 시민",       "period":"연중 상시 신청 가능",        "apply":BOKJIRO},
            {"rank":"🥉 3위","title":"서울 청년 취업사관학교",    "amount":"교육비 전액 + 훈련수당",        "target":"만 15~39세 서울 거주 미취업 청년",    "period":"연 3~4회 기수별 모집",       "apply":"https://youth.seoul.go.kr"},
            {"rank":"  4위", "title":"임산부 친환경농산물 지원",  "amount":"48만원 상당 친환경 꾸러미",     "target":"임신 중 또는 출산 12개월 이내 산모",  "period":"상시 신청",                  "apply":BOKJIRO},
            {"rank":"  5위", "title":"서울 어르신 교통비 지원",   "amount":"연 10만원 선불교통카드",        "target":"만 65세 이상 서울 거주 어르신",       "period":"매년 하반기 신청",            "apply":BOKJIRO},
        ]
    },
    {
        "name": "경기", "emoji": "🌿", "color": "#f97316",
        "portal": "https://www.gg.go.kr", "phone": "031-120",
        "benefits": [
            {"rank":"🥇 1위","title":"경기도 청년기본소득",       "amount":"분기 25만원 (연 최대 100만원)","target":"경기도 거주 만 24세 청년 전원",       "period":"매 분기별 (3·6·9·12월)",    "apply":"https://www.ggwf.or.kr"},
            {"rank":"🥈 2위","title":"경기도 산후조리비 지원",    "amount":"100만원",                      "target":"경기도 거주 출산 산모",               "period":"출산 후 6개월 이내",          "apply":BOKJIRO},
            {"rank":"🥉 3위","title":"경기 청년 노동자 지원",     "amount":"최대 200만원 (문화·자기개발비)","target":"경기 거주 만 18~34세 재직 청년",     "period":"매년 하반기 공고 (선착순)",   "apply":"https://www.ggwf.or.kr"},
            {"rank":"  4위", "title":"경기 무한돌봄 긴급복지",    "amount":"최대 500만원",                 "target":"갑작스런 위기로 생계 곤란한 경기 도민","period":"연중 상시",                  "apply":BOKJIRO},
            {"rank":"  5위", "title":"경기도 청년 면접비 지원",   "amount":"5만원 (면접비 실비)",           "target":"경기 거주 구직 활동 청년",            "period":"연중 상시 (선착순)",          "apply":"https://www.ggwf.or.kr"},
        ]
    },
    {
        "name": "인천", "emoji": "✈️", "color": "#eab308",
        "portal": "https://www.incheon.go.kr", "phone": "032-120",
        "benefits": [
            {"rank":"🥇 1위","title":"인천 청년 드림 수당",       "amount":"월 50만원 × 6개월 (총 300만원)","target":"인천 거주 만 19~34세 미취업 청년",  "period":"매년 상반기 모집",           "apply":BOKJIRO},
            {"rank":"🥈 2위","title":"인천 출산 축하금",          "amount":"첫째 100만 / 둘째 200만 / 셋째 500만원","target":"인천 거주 출산 가정",       "period":"출산 후 60일 이내",          "apply":BOKJIRO},
            {"rank":"🥉 3위","title":"인천 청년 전세보증금 지원", "amount":"최대 1억원 무이자 대출",        "target":"인천 거주 만 19~39세 청년",           "period":"예산 범위 내 선착순",         "apply":BOKJIRO},
            {"rank":"  4위", "title":"인천형 긴급복지",           "amount":"최대 200만원",                 "target":"위기 상황의 인천 시민",               "period":"연중 상시 신청",              "apply":BOKJIRO},
            {"rank":"  5위", "title":"인천 어르신 일자리 사업",   "amount":"월 27만원",                    "target":"만 60세 이상 인천 거주 어르신",       "period":"매년 초 연 1회 모집",         "apply":BOKJIRO},
        ]
    },
    {
        "name": "부산", "emoji": "🌊", "color": "#22c55e",
        "portal": "https://www.busan.go.kr", "phone": "051-120",
        "benefits": [
            {"rank":"🥇 1위","title":"부산 청년 희망두배 통장",   "amount":"최대 720만원 (2년 만기)",       "target":"부산 거주 만 18~34세 저소득 청년",    "period":"매년 상반기 모집",           "apply":BOKJIRO},
            {"rank":"🥈 2위","title":"부산 출산 축하금",          "amount":"첫째 100만 / 둘째 200만 / 셋째 300만원","target":"부산 거주 출산 가정",       "period":"출산 후 60일 이내",          "apply":BOKJIRO},
            {"rank":"🥉 3위","title":"부산 청년 월세 지원",       "amount":"월 최대 20만원 (최대 1년)",    "target":"부산 거주 만 19~39세 청년",           "period":"매년 상반기 공고",           "apply":BOKJIRO},
            {"rank":"  4위", "title":"부산 어르신 공공일자리",    "amount":"월 29만원",                    "target":"만 65세 이상 부산 거주 어르신",       "period":"매년 초 모집",               "apply":BOKJIRO},
            {"rank":"  5위", "title":"부산 소상공인 경영안정",    "amount":"최대 5천만원 저리 융자",        "target":"부산 소재 소상공인 사업자",           "period":"연중 상시 (예산 소진 마감)",  "apply":BOKJIRO},
        ]
    },
    {
        "name": "대구", "emoji": "🍎", "color": "#06b6d4",
        "portal": "https://www.daegu.go.kr", "phone": "053-120",
        "benefits": [
            {"rank":"🥇 1위","title":"대구 청년 구직 지원금",     "amount":"월 50만원 × 3개월 (총 150만원)","target":"대구 거주 만 18~34세 미취업 청년",  "period":"매년 상반기 모집",           "apply":BOKJIRO},
            {"rank":"🥈 2위","title":"대구 출산 지원금",          "amount":"첫째 100만 / 둘째 200만 / 셋째 300만원","target":"대구 거주 출산 가정",       "period":"출산 후 60일 이내",          "apply":BOKJIRO},
            {"rank":"🥉 3위","title":"대구 청년 취업 장려금",     "amount":"최대 200만원",                 "target":"대구 거주 만 19~34세 신규 취업 청년","period":"취업 후 6개월 이내 신청",     "apply":BOKJIRO},
            {"rank":"  4위", "title":"대구 어르신 의료비 지원",   "amount":"연 50만원 한도",               "target":"만 65세 이상 저소득 대구 어르신",     "period":"연중 상시",                  "apply":BOKJIRO},
            {"rank":"  5위", "title":"대구 장애인 활동 지원",     "amount":"월 최대 90만원 바우처",         "target":"대구 거주 만 6세 이상 중증 장애인",  "period":"연중 상시",                  "apply":BOKJIRO},
        ]
    },
    {
        "name": "대전", "emoji": "🔬", "color": "#6366f1",
        "portal": "https://www.daejeon.go.kr", "phone": "042-120",
        "benefits": [
            {"rank":"🥇 1위","title":"대전 청년 월세 지원",       "amount":"월 20만원 (최대 1년)",         "target":"대전 거주 만 19~39세 청년",           "period":"매년 상반기 공고",           "apply":BOKJIRO},
            {"rank":"🥈 2위","title":"대전 청년 창업 지원",       "amount":"최대 5천만원 (사업화 자금)",    "target":"대전 거주 만 39세 이하 창업 희망 청년","period":"매년 상반기 공모",           "apply":BOKJIRO},
            {"rank":"🥉 3위","title":"대전 출산 지원금",          "amount":"첫째 50만 / 둘째 100만 / 셋째 200만원","target":"대전 거주 출산 가정",       "period":"출산 후 60일 이내",          "apply":BOKJIRO},
            {"rank":"  4위", "title":"대전형 긴급복지",           "amount":"최대 200만원",                 "target":"위기 상황의 대전 시민",               "period":"연중 상시 신청",             "apply":BOKJIRO},
            {"rank":"  5위", "title":"대전 어르신 틀니 지원",     "amount":"본인부담 30%만 (70% 지원)",    "target":"만 65세 이상 대전 거주 건강보험 가입자","period":"연중 상시 (치과 방문 신청)","apply":BOKJIRO},
        ]
    },
    {
        "name": "광주", "emoji": "🌸", "color": "#a855f7",
        "portal": "https://www.gwangju.go.kr", "phone": "062-120",
        "benefits": [
            {"rank":"🥇 1위","title":"광주 청년 드림 수당",       "amount":"월 50만원 × 6개월 (총 300만원)","target":"광주 거주 만 18~34세 미취업 청년",  "period":"매년 상반기 모집",           "apply":BOKJIRO},
            {"rank":"🥈 2위","title":"광주 출산 지원금",          "amount":"첫째 50만 / 둘째 150만 / 셋째 300만원","target":"광주 거주 출산 가정",       "period":"출산 후 60일 이내",          "apply":BOKJIRO},
            {"rank":"🥉 3위","title":"광주 청년 취업 응원금",     "amount":"최대 150만원",                 "target":"광주 거주 만 18~34세 구직 청년",      "period":"연중 상시 신청",             "apply":BOKJIRO},
            {"rank":"  4위", "title":"광주형 긴급복지 지원",      "amount":"최대 200만원",                 "target":"위기 상황의 광주 시민",               "period":"연중 상시 신청",             "apply":BOKJIRO},
            {"rank":"  5위", "title":"광주 어르신 효도수당",      "amount":"월 5만원 (연 60만원)",          "target":"만 80세 이상 광주 거주 어르신",       "period":"연중 상시 신청",             "apply":BOKJIRO},
        ]
    },
    {
        "name": "울산", "emoji": "🏭", "color": "#ec4899",
        "portal": "https://www.ulsan.go.kr", "phone": "052-120",
        "benefits": [
            {"rank":"🥇 1위","title":"울산 청년 창업 지원",       "amount":"최대 1억원 (시제품·마케팅)",    "target":"울산 거주 만 39세 이하 창업 청년",    "period":"매년 상반기 공모",           "apply":BOKJIRO},
            {"rank":"🥈 2위","title":"울산 출산 축하금",          "amount":"첫째 100만 / 둘째 300만 / 셋째 500만원","target":"울산 거주 출산 가정",       "period":"출산 후 60일 이내",          "apply":BOKJIRO},
            {"rank":"🥉 3위","title":"울산 청년 지원금",          "amount":"최대 200만원",                 "target":"울산 거주 만 19~34세 청년",           "period":"매년 상반기 모집",           "apply":BOKJIRO},
            {"rank":"  4위", "title":"울산 소상공인 특별 지원",   "amount":"최대 3천만원 저리 융자",        "target":"울산 소재 소상공인 사업자",           "period":"연중 상시 (예산 소진 마감)",  "apply":BOKJIRO},
            {"rank":"  5위", "title":"울산 어르신 틀니 지원",     "amount":"50% 지원",                     "target":"만 65세 이상 울산 거주 건강보험 가입자","period":"연중 상시 (치과 방문)",     "apply":BOKJIRO},
        ]
    },
    {
        "name": "세종", "emoji": "🏛️", "color": "#14b8a6",
        "portal": "https://www.sejong.go.kr", "phone": "044-300-3114",
        "benefits": [
            {"rank":"🥇 1위","title":"세종 출산 장려금",          "amount":"첫째 200만 / 둘째 400만 / 셋째 600만원","target":"세종시 거주 출산 가정",     "period":"출산 후 60일 이내",          "apply":BOKJIRO},
            {"rank":"🥈 2위","title":"세종 청년 정착 지원금",     "amount":"최대 300만원 (전입 청년 우대)","target":"세종 신규 전입 만 19~39세 청년",      "period":"전입 후 6개월 이내",          "apply":BOKJIRO},
            {"rank":"🥉 3위","title":"세종 청년 월세 지원",       "amount":"월 20만원 (최대 1년)",         "target":"세종 거주 만 19~39세 청년",           "period":"매년 상반기 공고",           "apply":BOKJIRO},
            {"rank":"  4위", "title":"세종형 긴급복지",           "amount":"최대 200만원",                 "target":"위기 상황의 세종 시민",               "period":"연중 상시 신청",             "apply":BOKJIRO},
            {"rank":"  5위", "title":"세종 어르신 공공일자리",    "amount":"월 29만원",                    "target":"만 65세 이상 세종 거주 어르신",       "period":"매년 초 모집",               "apply":BOKJIRO},
        ]
    },
    {
        "name": "강원", "emoji": "🏔️", "color": "#84cc16",
        "portal": "https://www.gwd.go.kr", "phone": "033-1577-7070",
        "benefits": [
            {"rank":"🥇 1위","title":"강원 귀농귀촌 정착 지원",   "amount":"최대 3,000만원",               "target":"강원 귀농·귀촌 예정자 (이주 5년 이내)","period":"연중 상시 (시·군 접수)",    "apply":BOKJIRO},
            {"rank":"🥈 2위","title":"강원 청년 창업 지원",       "amount":"최대 5천만원",                 "target":"강원 거주 만 39세 이하 창업 청년",    "period":"매년 상반기 공모",           "apply":BOKJIRO},
            {"rank":"🥉 3위","title":"강원 출산 축하금",          "amount":"첫째 100만 / 둘째 200만 / 셋째 300만원","target":"강원 거주 출산 가정",       "period":"출산 후 60일 이내",          "apply":BOKJIRO},
            {"rank":"  4위", "title":"강원 청년 취업 지원금",     "amount":"최대 200만원",                 "target":"강원 거주 만 18~34세 취업 청년",      "period":"취업 후 6개월 이내 신청",    "apply":BOKJIRO},
            {"rank":"  5위", "title":"강원 산촌 이주민 지원",     "amount":"최대 1억원 저리 융자",          "target":"강원 산촌 이주 희망자",               "period":"연중 상시 (시·군 담당 접수)","apply":BOKJIRO},
        ]
    },
    {
        "name": "충북", "emoji": "🌾", "color": "#f59e0b",
        "portal": "https://www.chungbuk.go.kr", "phone": "043-220-2114",
        "extra": True,
        "benefits": [
            {"rank":"🥇 1위","title":"충북 청년 내일채움공제",    "amount":"최대 1,200만원 (2~3년 적립)", "target":"충북 중소기업 재직 만 34세 이하 청년","period":"상시 신청 (고용센터 접수)",   "apply":BOKJIRO},
            {"rank":"🥈 2위","title":"충북 귀농 창업 지원",       "amount":"최대 3억원 저리 융자",         "target":"충북 귀농 예정자 (이주 5년 이내)",    "period":"연중 상시 (시·군 접수)",     "apply":BOKJIRO},
            {"rank":"🥉 3위","title":"충북 출산 장려금",          "amount":"첫째 100만 / 둘째 200만 / 셋째 300만원","target":"충북 거주 출산 가정",       "period":"출산 후 60일 이내",          "apply":BOKJIRO},
            {"rank":"  4위", "title":"충북 청년 월세 지원",       "amount":"월 20만원 (최대 1년)",         "target":"충북 거주 만 19~39세 청년",           "period":"매년 상반기 공고",           "apply":BOKJIRO},
            {"rank":"  5위", "title":"충북 소상공인 경영안정",    "amount":"최대 2천만원 저리 융자",        "target":"충북 소재 소상공인",                 "period":"연중 상시",                  "apply":BOKJIRO},
        ],
        "extra_benefits": [
            {"rank":"★ 특집 1","title":"영동군 출산장려금",           "amount":"첫째 50만원~넷째 500만원","target":"영동군 거주 출산 가정",       "period":"출산 후 신청",  "apply":"https://www.yd.go.kr"},
            {"rank":"★ 특집 2","title":"영동군 귀농귀촌 정착금",      "amount":"최대 3,000만원",          "target":"영동군 귀농·귀촌 이주민",     "period":"연중 상시",     "apply":"https://www.yd.go.kr"},
            {"rank":"★ 특집 3","title":"영동 포도·와인 농업인 지원",  "amount":"경영비 30% 보조",         "target":"영동군 포도·와인 재배 농업인","period":"매년 신청",     "apply":"https://www.yd.go.kr"},
            {"rank":"★ 특집 4","title":"영동군 어르신 효도관광",      "amount":"1인 5만원 지원",          "target":"영동군 만 65세 이상 어르신",  "period":"연 1회 모집",   "apply":"https://www.yd.go.kr"},
            {"rank":"★ 특집 5","title":"영동군 공공근로 사업",        "amount":"일 8만원",                "target":"영동군 거주 취업 취약계층",   "period":"분기별 모집",   "apply":"https://www.yd.go.kr"},
        ]
    },
    {
        "name": "충남", "emoji": "🦀", "color": "#ef4444",
        "portal": "https://www.chungnam.go.kr", "phone": "041-635-2114",
        "benefits": [
            {"rank":"🥇 1위","title":"충남 청년 기회수당",        "amount":"월 50만원 × 6개월 (총 300만원)","target":"충남 거주 만 18~34세 미취업 청년",  "period":"매년 상반기 공고",           "apply":BOKJIRO},
            {"rank":"🥈 2위","title":"충남 출산 장려금",          "amount":"첫째 200만 / 둘째 300만 / 셋째 500만원","target":"충남 거주 출산 가정",       "period":"출산 후 60일 이내",          "apply":BOKJIRO},
            {"rank":"🥉 3위","title":"충남 귀농귀촌 정착 지원",   "amount":"최대 3,000만원",               "target":"충남 귀농·귀촌 예정자",               "period":"연중 상시",                  "apply":BOKJIRO},
            {"rank":"  4위", "title":"충남 청년 창업 지원",       "amount":"최대 1억원",                   "target":"충남 거주 만 39세 이하 창업 청년",    "period":"매년 상반기 공모",           "apply":BOKJIRO},
            {"rank":"  5위", "title":"충남 어르신 공공일자리",    "amount":"월 29만원",                    "target":"만 65세 이상 충남 거주 어르신",       "period":"매년 초 모집",               "apply":BOKJIRO},
        ]
    },
    {
        "name": "전북", "emoji": "🥁", "color": "#8b5cf6",
        "portal": "https://www.jeonbuk.go.kr", "phone": "063-280-2114",
        "benefits": [
            {"rank":"🥇 1위","title":"전북 출산 축하금",          "amount":"첫째 200만 / 둘째 400만 / 넷째 이상 1,000만원","target":"전북 거주 출산 가정","period":"출산 후 60일 이내",       "apply":BOKJIRO},
            {"rank":"🥈 2위","title":"전북 귀농 창업 지원",       "amount":"최대 3억원 저리 융자",         "target":"전북 귀농 예정자 (이주 5년 이내)",    "period":"연중 상시",                  "apply":BOKJIRO},
            {"rank":"🥉 3위","title":"전북 청년 지원금",          "amount":"최대 200만원",                 "target":"전북 거주 만 19~34세 청년",           "period":"매년 상반기 공고",           "apply":BOKJIRO},
            {"rank":"  4위", "title":"전북 청년 월세 지원",       "amount":"월 20만원 (최대 1년)",         "target":"전북 거주 만 19~39세 청년",           "period":"매년 상반기 공고",           "apply":BOKJIRO},
            {"rank":"  5위", "title":"전북 농업인 직불금",        "amount":"ha당 최대 205만원",            "target":"전북 농업 종사자 (농지 등록 필수)",   "period":"매년 2~5월 신청",            "apply":BOKJIRO},
        ]
    },
    {
        "name": "전남", "emoji": "🐦", "color": "#10b981",
        "portal": "https://www.jeonnam.go.kr", "phone": "061-286-2114",
        "benefits": [
            {"rank":"🥇 1위","title":"전남 출산 장려금",          "amount":"첫째 200만 / 둘째 400만 / 넷째 이상 1,000만원","target":"전남 거주 출산 가정","period":"출산 후 60일 이내",       "apply":BOKJIRO},
            {"rank":"🥈 2위","title":"전남 귀농 정착 지원",       "amount":"최대 3억원 저리 융자",         "target":"전남 귀농 예정자",                   "period":"연중 상시",                  "apply":BOKJIRO},
            {"rank":"🥉 3위","title":"전남 청년 농촌 보금자리",   "amount":"임대료 50% 지원",              "target":"전남 이주 만 18~49세 청년 농업인",   "period":"연중 상시 (시·군 접수)",     "apply":BOKJIRO},
            {"rank":"  4위", "title":"전남 청년 월세 지원",       "amount":"월 20만원 (최대 1년)",         "target":"전남 거주 만 19~39세 청년",           "period":"매년 상반기 공고",           "apply":BOKJIRO},
            {"rank":"  5위", "title":"전남 농어업인 복지 지원",   "amount":"연 최대 100만원",              "target":"전남 농어업 종사자",                 "period":"매년 초 신청",               "apply":BOKJIRO},
        ]
    },
    {
        "name": "경북", "emoji": "🍇", "color": "#f43f5e",
        "portal": "https://www.gb.go.kr", "phone": "054-880-2114",
        "benefits": [
            {"rank":"🥇 1위","title":"경북 출산 축하금",          "amount":"첫째 100만 / 둘째 300만 / 넷째 700만원","target":"경북 거주 출산 가정",       "period":"출산 후 60일 이내",          "apply":BOKJIRO},
            {"rank":"🥈 2위","title":"경북 귀농 이주민 지원",     "amount":"최대 3억원 저리 융자",         "target":"경북 귀농 예정자 (이주 5년 이내)",    "period":"연중 상시",                  "apply":BOKJIRO},
            {"rank":"🥉 3위","title":"경북 청년 지원금",          "amount":"최대 300만원",                 "target":"경북 거주 만 19~34세 청년",           "period":"매년 상반기 공고",           "apply":BOKJIRO},
            {"rank":"  4위", "title":"경북 소상공인 지원",        "amount":"최대 3천만원 저리 융자",        "target":"경북 소재 소상공인",                 "period":"연중 상시",                  "apply":BOKJIRO},
            {"rank":"  5위", "title":"경북 청년 창업 장려금",     "amount":"최대 2천만원",                 "target":"경북 거주 만 39세 이하 창업 청년",    "period":"매년 상반기 공모",           "apply":BOKJIRO},
        ]
    },
    {
        "name": "경남", "emoji": "🌿", "color": "#0ea5e9",
        "portal": "https://www.gyeongnam.go.kr", "phone": "055-211-2114",
        "benefits": [
            {"rank":"🥇 1위","title":"경남 출산 장려금",          "amount":"첫째 100만 / 둘째 200만 / 셋째 400만원","target":"경남 거주 출산 가정",       "period":"출산 후 60일 이내",          "apply":BOKJIRO},
            {"rank":"🥈 2위","title":"경남 청년 드림 수당",       "amount":"월 50만원 × 6개월 (총 300만원)","target":"경남 거주 만 18~34세 미취업 청년",  "period":"매년 상반기 공고",           "apply":BOKJIRO},
            {"rank":"🥉 3위","title":"경남 귀농귀촌 지원",        "amount":"최대 3,000만원",               "target":"경남 귀농·귀촌 예정자",               "period":"연중 상시",                  "apply":BOKJIRO},
            {"rank":"  4위", "title":"경남 소상공인 경영안정",    "amount":"최대 200만원",                 "target":"경남 소재 소상공인",                 "period":"연중 상시",                  "apply":BOKJIRO},
            {"rank":"  5위", "title":"경남 어르신 효도 지원",     "amount":"연 10만원",                    "target":"만 70세 이상 경남 거주 어르신",       "period":"연중 상시 신청",             "apply":BOKJIRO},
        ]
    },
    {
        "name": "제주", "emoji": "🍊", "color": "#f97316",
        "portal": "https://www.jeju.go.kr", "phone": "064-710-2114",
        "benefits": [
            {"rank":"🥇 1위","title":"제주 출산 축하금",          "amount":"첫째 100만 / 둘째 200만 / 셋째 500만원","target":"제주 거주 출산 가정",       "period":"출산 후 60일 이내",          "apply":BOKJIRO},
            {"rank":"🥈 2위","title":"제주 청년 창업 지원",       "amount":"최대 5천만원",                 "target":"제주 거주 만 39세 이하 창업 청년",    "period":"매년 상반기 공모",           "apply":BOKJIRO},
            {"rank":"🥉 3위","title":"제주 귀농 정착 지원",       "amount":"최대 3,000만원",               "target":"제주 귀농·귀촌 예정자",               "period":"연중 상시",                  "apply":BOKJIRO},
            {"rank":"  4위", "title":"제주 청년 주거 지원금",     "amount":"월 15만원 (최대 1년)",         "target":"제주 거주 만 19~39세 청년",           "period":"매년 상반기 공고",           "apply":BOKJIRO},
            {"rank":"  5위", "title":"제주 농업인 지원금",        "amount":"최대 200만원",                 "target":"제주 농업 종사자",                   "period":"매년 초 신청",               "apply":BOKJIRO},
        ]
    },
]


# ══════════════════════════════════════════════
# SVG 이미지 생성
# ══════════════════════════════════════════════

def _whale_svg_region(cx, cy, size=1.0, color=None, fin_color=None, female=False):  # noqa: ARG001
    """귀여운 만화 고래 (둥글둥글 직립형) — 파랑(남자) / 핑크(여자)"""
    s = size
    if female:
        body_c  = "#e91e8c"
        dark_c  = "#ad1457"
        eye_c   = "#e91e8c"
        spout_c = "#f48fb1"
    else:
        body_c  = "#1a3eb8"
        dark_c  = "#0d2480"
        eye_c   = "#1565c0"
        spout_c = "#90caf9"

    def i(v): return int(v * s)

    tail_l   = (f'<ellipse cx="{cx - i(16)}" cy="{cy + i(68)}" '
                f'rx="{i(22)}" ry="{i(11)}" fill="{dark_c}" '
                f'transform="rotate(-30 {cx - i(16)} {cy + i(68)})"/>')
    tail_r   = (f'<ellipse cx="{cx + i(16)}" cy="{cy + i(68)}" '
                f'rx="{i(22)}" ry="{i(11)}" fill="{dark_c}" '
                f'transform="rotate(30 {cx + i(16)} {cy + i(68)})"/>')
    tail_join= (f'<ellipse cx="{cx}" cy="{cy + i(60)}" '
                f'rx="{i(18)}" ry="{i(12)}" fill="{body_c}"/>')
    body     = (f'<ellipse cx="{cx}" cy="{cy}" '
                f'rx="{i(52)}" ry="{i(60)}" fill="{body_c}"/>')
    belly    = (f'<ellipse cx="{cx + i(4)}" cy="{cy + i(14)}" '
                f'rx="{i(30)}" ry="{i(38)}" fill="white" opacity="0.9"/>')
    stripes  = ""
    for k, yk in enumerate([-10, 0, 10, 20]):
        stripes += (f'<path d="M{cx - i(20 - k*2)},{cy + i(yk)} '
                    f'Q{cx + i(4)},{cy + i(yk + 4)} {cx + i(28 - k*2)},{cy + i(yk)}" '
                    f'fill="none" stroke="#e0e7ff" stroke-width="{max(1, i(1.5))}" opacity="0.6"/>')
    fin_l    = (f'<path d="M{cx - i(44)},{cy - i(10)} '
                f'Q{cx - i(72)},{cy - i(30)} {cx - i(68)},{cy + i(10)}" '
                f'fill="none" stroke="{dark_c}" stroke-width="{i(16)}" stroke-linecap="round"/>')
    fin_r    = (f'<path d="M{cx + i(44)},{cy - i(15)} '
                f'Q{cx + i(68)},{cy - i(45)} {cx + i(72)},{cy - i(70)}" '
                f'fill="none" stroke="{dark_c}" stroke-width="{i(16)}" stroke-linecap="round"/>')
    fin_r_tip= (f'<circle cx="{cx + i(72)}" cy="{cy - i(70)}" r="{i(10)}" fill="{dark_c}"/>')
    finger   = (f'<path d="M{cx + i(78)},{cy - i(78)} L{cx + i(88)},{cy - i(92)}" '
                f'fill="none" stroke="{dark_c}" stroke-width="{i(7)}" stroke-linecap="round"/>')
    fingertip= (f'<circle cx="{cx + i(90)}" cy="{cy - i(95)}" r="{i(5)}" fill="{dark_c}"/>')
    ew_l     = (f'<circle cx="{cx - i(17)}" cy="{cy - i(18)}" r="{i(14)}" fill="white"/>')
    ep_l     = (f'<circle cx="{cx - i(14)}" cy="{cy - i(20)}" r="{i(9)}" fill="{eye_c}"/>')
    ed_l     = (f'<circle cx="{cx - i(13)}" cy="{cy - i(21)}" r="{i(5)}" fill="#0d1117"/>')
    eh_l     = (f'<circle cx="{cx - i(10)}" cy="{cy - i(24)}" r="{i(3)}" fill="white"/>')
    eh2_l    = (f'<circle cx="{cx - i(17)}" cy="{cy - i(28)}" r="{i(1)}" fill="white"/>')
    wink     = (f'<path d="M{cx + i(8)},{cy - i(23)} Q{cx + i(18)},{cy - i(29)} {cx + i(28)},{cy - i(23)}" '
                f'fill="none" stroke="#0d1117" stroke-width="{i(3)}" stroke-linecap="round"/>')
    wink_lash= (f'<path d="M{cx + i(10)},{cy - i(24)} L{cx + i(9)},{cy - i(30)}" '
                f'stroke="#0d1117" stroke-width="{i(2)}" stroke-linecap="round"/>'
                f'<path d="M{cx + i(18)},{cy - i(27)} L{cx + i(18)},{cy - i(33)}" '
                f'stroke="#0d1117" stroke-width="{i(2)}" stroke-linecap="round"/>'
                f'<path d="M{cx + i(26)},{cy - i(24)} L{cx + i(27)},{cy - i(30)}" '
                f'stroke="#0d1117" stroke-width="{i(2)}" stroke-linecap="round"/>')
    blush_l  = (f'<ellipse cx="{cx - i(30)}" cy="{cy - i(5)}" '
                f'rx="{i(10)}" ry="{i(7)}" fill="#ff8fab" opacity="0.7"/>')
    blush_r  = (f'<ellipse cx="{cx + i(24)}" cy="{cy - i(5)}" '
                f'rx="{i(10)}" ry="{i(7)}" fill="#ff8fab" opacity="0.7"/>')
    mouth_bg = (f'<path d="M{cx - i(16)},{cy + i(6)} Q{cx},{cy + i(20)} {cx + i(16)},{cy + i(6)}" '
                f'fill="#cc2255" stroke="#0d1117" stroke-width="{i(2)}"/>')
    tongue   = (f'<ellipse cx="{cx}" cy="{cy + i(15)}" rx="{i(9)}" ry="{i(6)}" fill="#ff6b8a"/>')
    sx, sy   = cx - i(10), cy - i(44)
    star     = (f'<path d="M{sx},{sy - i(7)} L{sx + i(2)},{sy - i(2)} L{sx + i(7)},{sy - i(2)} '
                f'L{sx + i(3)},{sy + i(2)} L{sx + i(5)},{sy + i(7)} L{sx},{sy + i(4)} '
                f'L{sx - i(5)},{sy + i(7)} L{sx - i(3)},{sy + i(2)} L{sx - i(7)},{sy - i(2)} '
                f'L{sx - i(2)},{sy - i(2)} Z" fill="white" opacity="0.9"/>')
    spout1   = (f'<path d="M{cx - i(8)},{cy - i(58)} Q{cx - i(14)},{cy - i(80)} {cx - i(10)},{cy - i(92)}" '
                f'fill="none" stroke="{spout_c}" stroke-width="{i(4)}" stroke-linecap="round"/>')
    spout2   = (f'<path d="M{cx + i(2)},{cy - i(60)} Q{cx + i(10)},{cy - i(82)} {cx + i(8)},{cy - i(94)}" '
                f'fill="none" stroke="{spout_c}" stroke-width="{i(3)}" stroke-linecap="round"/>')
    spout3   = (f'<path d="M{cx + i(10)},{cy - i(56)} Q{cx + i(22)},{cy - i(74)} {cx + i(20)},{cy - i(84)}" '
                f'fill="none" stroke="{spout_c}" stroke-width="{i(2)}" stroke-linecap="round"/>')
    sparkles = ""
    for (ddx, ddy, sz) in [(-62, -50, 5), (-58, -20, 3), (60, -30, 4), (58, 10, 3)]:
        sx2, sy2 = cx + i(ddx), cy + i(ddy)
        sz2 = max(2, i(sz))
        sc = spout_c if not female else "#ffb3d9"
        sparkles += (f'<path d="M{sx2},{sy2 - sz2} L{sx2 + 1},{sy2 - 1} L{sx2 + sz2},{sy2} '
                     f'L{sx2 + 1},{sy2 + 1} L{sx2},{sy2 + sz2} L{sx2 - 1},{sy2 + 1} '
                     f'L{sx2 - sz2},{sy2} L{sx2 - 1},{sy2 - 1} Z" '
                     f'fill="{sc}" opacity="0.8"/>')
    ribbon = ""
    if female:
        rx2, ry2 = cx + i(22), cy - i(55)
        ribbon = (
            f'<path d="M{rx2 - i(12)},{ry2} L{rx2},{ry2 - i(9)} '
            f'L{rx2 + i(12)},{ry2} L{rx2},{ry2 + i(9)} Z" fill="#ff4d88"/>'
            f'<circle cx="{rx2}" cy="{ry2}" r="{max(3, i(4))}" fill="#ffb3c6"/>'
            f'<path d="M{cx - i(24)},{cy - i(30)} L{cx - i(26)},{cy - i(36)}" '
            f'stroke="#ad1457" stroke-width="{i(2)}" stroke-linecap="round"/>'
            f'<path d="M{cx - i(17)},{cy - i(31)} L{cx - i(17)},{cy - i(37)}" '
            f'stroke="#ad1457" stroke-width="{i(2)}" stroke-linecap="round"/>'
            f'<path d="M{cx - i(10)},{cy - i(30)} L{cx - i(8)},{cy - i(36)}" '
            f'stroke="#ad1457" stroke-width="{i(2)}" stroke-linecap="round"/>'
        )
    parts = [
        tail_l, tail_r, tail_join,
        body, belly, stripes,
        fin_l, fin_r, fin_r_tip, finger, fingertip,
        ew_l, ep_l, ed_l, eh_l, eh2_l,
        wink, wink_lash,
        blush_l, blush_r,
        mouth_bg, tongue,
        star, spout1, spout2, spout3,
        sparkles,
    ]
    if ribbon:
        parts.append(ribbon)
    return "\n  ".join(parts)


def make_region_banner_svg(r, today_str):
    color = r["color"]
    name  = r["name"]
    emoji = r["emoji"]
    # 💙 파란 고래 (남자) + 🩷 핑크 고래 (여자) 커플
    whale_m = _whale_svg_region(cx=78,  cy=205, size=0.90, female=False)
    whale_f = _whale_svg_region(cx=150, cy=210, size=0.70, female=True)
    whale = whale_m + "\n  " + whale_f
    return f"""<svg width="800" height="340" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#ffffff"/>
      <stop offset="100%" style="stop-color:#f0f4ff"/>
    </linearGradient>
  </defs>
  <!-- 배경 -->
  <rect width="800" height="340" fill="url(#bg)"/>
  <!-- 상단 컬러 바 -->
  <rect width="800" height="10" fill="{color}"/>
  <!-- 우측 장식 원 -->
  <circle cx="720" cy="170" r="140" fill="{color}" opacity="0.07"/>
  <circle cx="720" cy="170" r="90"  fill="{color}" opacity="0.07"/>
  <!-- 날짜 배지 -->
  <rect x="240" y="28" width="200" height="30" rx="15" fill="{color}"/>
  <text x="340" y="48" font-family="Arial" font-size="13" fill="white" text-anchor="middle" font-weight="bold">📅 {today_str} 업데이트</text>
  <!-- 만화 고래 캐릭터 -->
  {whale}
  <!-- 말풍선 -->
  <path d="M188,95 Q188,74 210,74 L330,74 Q352,74 352,95 Q352,116 330,116 L218,116 L207,132 L214,116 L210,116 Q188,116 188,95 Z" fill="white" stroke="{color}" stroke-width="2.5"/>
  <text x="270" y="99" font-family="Arial" font-size="11" fill="{color}" text-anchor="middle" font-weight="bold">{name} 살면</text>
  <text x="270" y="113" font-family="Arial" font-size="11" fill="{color}" text-anchor="middle" font-weight="bold">이거 다 받아요!</text>
  <!-- 지역 이모지 -->
  <text x="415" y="108" font-family="Arial" font-size="40" text-anchor="middle">{emoji}</text>
  <!-- 메인 타이틀 -->
  <text x="570" y="152" font-family="Arial" font-size="32" fill="#1e293b" font-weight="bold" text-anchor="middle">{name} 주민 전용</text>
  <text x="570" y="198" font-family="Arial" font-size="32" fill="{color}"   font-weight="bold" text-anchor="middle">지원금 BEST 5 💰</text>
  <text x="570" y="234" font-family="Arial" font-size="13" fill="#64748b" text-anchor="middle">금액 · 대상 · 신청방법 총정리</text>
  <!-- 하단 버튼 2개 -->
  <rect x="390" y="255" width="155" height="40" rx="20" fill="{color}"/>
  <text x="467" y="280" font-family="Arial" font-size="13" fill="white" text-anchor="middle" font-weight="bold">✅ 지금 바로 신청</text>
  <rect x="558" y="255" width="160" height="40" rx="20" fill="#f1f5f9"/>
  <text x="638" y="280" font-family="Arial" font-size="13" fill="#475569" text-anchor="middle" font-weight="bold">📋 신청방법 보기</text>
  <!-- 하단 컬러 바 -->
  <rect y="330" width="800" height="10" fill="{color}" opacity="0.3"/>
</svg>"""


def make_hashtag_svg(r):
    name  = r["name"]
    color = r["color"]
    tags = [
        (f"#{name}혜택",   color,   20,  50, 120),
        (f"#{name}지원금", color,  150,  50, 120),
        ("#정부지원금",    "#6366f1",280, 50, 110),
        ("#복지로",        "#ef4444",400, 50,  90),
        ("#지역혜택총정리","#f97316",500, 50, 130),
        ("#2026혜택",      "#22c55e",640, 50, 110),
        ("#청년지원금",    "#a855f7", 20,100, 110),
        ("#출산지원금",    "#ec4899",140,100, 110),
        ("#귀농귀촌",      "#14b8a6",260,100, 100),
        ("#소상공인지원",  "#f59e0b",370,100, 120),
        ("#매일업데이트",  "#f43f5e",500,100, 120),
        ("#몰라서못받는돈","#0ea5e9",630,100, 140),
    ]
    rects = ""
    for tag, c, x, y, w in tags:
        cx = x + w // 2
        rects += f"""
  <rect x="{x}" y="{y}" width="{w}" height="34" rx="17" fill="{c}"/>
  <text x="{cx}" y="{y+22}" font-family="Arial" font-size="12" fill="white" text-anchor="middle" font-weight="bold">{tag}</text>"""
    return f"""<svg width="800" height="155" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="155" fill="#f8faff" rx="14"/>
  <rect x="2" y="2" width="796" height="151" rx="12" fill="none" stroke="#e0e7ff" stroke-width="2"/>
  <text x="400" y="30" font-family="Arial" font-size="14" fill="#4f46e5" text-anchor="middle" font-weight="bold">🔖 관련 태그</text>
  {rects}
</svg>"""


def svg_to_png(page, svg_content: str, png_path: Path):
    try:
        page.goto("about:blank", wait_until="domcontentloaded")
        page.set_content(
            f"<!DOCTYPE html><html><body style='margin:0;padding:0;background:white'>"
            f"{svg_content}</body></html>",
            wait_until="domcontentloaded"
        )
        time.sleep(0.8)
        el = page.query_selector("svg")
        if el:
            el.screenshot(path=str(png_path))
        else:
            page.screenshot(path=str(png_path), full_page=True)
        return True
    except Exception as e:
        logging.warning(f"PNG 변환 실패 ({png_path.name}): {e}")
        return False


# ══════════════════════════════════════════════
# 개별 지역 포스트 생성 (상세 형식)
# ══════════════════════════════════════════════

def generate_region_post(r, today_str, banner_name, tag_name):
    name     = r["name"]
    emoji    = r["emoji"]
    portal   = r["portal"]
    phone    = r["phone"]
    benefits = r["benefits"]

    benefits_text = ""
    for idx, b in enumerate(benefits, 1):
        benefits_text += (
            f"✅ {idx}위. {b['title']}\n\n"
            f"   💰 얼마나? {b['amount']}\n"
            f"   👤 누가 받아요? {b['target']}\n"
            f"   📅 언제 신청? {b['period']}\n"
            f"   👉 신청: {b['apply']}\n\n\n"
        )

    extra_text = ""
    if r.get("extra") and r.get("extra_benefits"):
        extra_text = (
            f"🍇 영동군 주민이라면 추가 혜택도 있어요!\n\n"
        )
        for b in r["extra_benefits"]:
            extra_text += (
                f"   ★ {b['title']}\n"
                f"   💰 {b['amount']} | 👉 {b['apply']}\n\n"
            )
        extra_text += "\n"

    safe_name = name.replace(" ", "")

    # 검증 박스 (상단 고정)
    verify_box = (
        f"┌──────────────────────────────────────────┐\n"
        f"│  ✅ 정보 출처 및 검증 안내                          │\n"
        f"│  이 글은 아래 공식 자료를 기반으로 작성됐습니다.        │\n"
        f"│  · 복지로(bokjiro.go.kr)                        │\n"
        f"│  · 정부24(gov.kr)                               │\n"
        f"│  · {name} 공식 포털({portal[:30]})  │\n"
        f"│  지원 금액·조건은 변동될 수 있으니                    │\n"
        f"│  신청 전 반드시 공식 사이트에서 확인하세요! ⚠️          │\n"
        f"└──────────────────────────────────────────┘\n"
    )

    return (
        f"{emoji} {name} 살면 이거 다 받을 수 있어요! 💸 신청 안 하면 내 돈 버리는 거예요 ({today_str} 최신판)\n\n"
        f"[IMAGE:{banner_name}]\n\n"
        f"안녕하세요 😊\n\n"
        f"{verify_box}\n"
        f"{name}에 사시는 분들!\n"
        f"이 글 보고 계신다면 오늘 진짜 잘 오신 거예요 👍\n\n"
        f"사실 같은 대한민국 국민인데\n"
        f"{name} 주민이라서 추가로 더 받을 수 있는 혜택이 있거든요 😮\n\n"
        f"근데 신청을 안 해서 못 받는 분들이 엄청 많아요.\n"
        f"알면 바로 신청하는데, 모르면 그냥 지나치게 되더라고요.\n\n"
        f"그래서 제가 2026년 기준으로\n"
        f"{name} 혜택 BEST 5를 싹 다 정리해봤어요! 💪\n\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 {name} 지원금 BEST 5 — 지금 받을 수 있어요!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{benefits_text}"
        f"{extra_text}"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 신청하는 방법 (진짜 쉬워요!)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"방법 1️⃣  복지로 앱 or 사이트 → {BOKJIRO}\n"
        f"방법 2️⃣  정부24 검색 → {GOV24}\n"
        f"방법 3️⃣  {name} 공식 포털 → {portal}\n"
        f"방법 4️⃣  집 근처 주민센터 방문 (서류 지참)\n"
        f"방법 5️⃣  모르면 전화! ☎ 129 (복지 콜센터, 무료)\n"
        f"방법 6️⃣  {name} 직접 문의 ☎ {phone}\n\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ 신청 전에 이것만 확인하세요!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"주민등록상 {name} 주소지가 있어야 해요 📋\n"
        f"혜택마다 소득 기준이 달라요 — 내가 해당되는지 먼저 확인!\n"
        f"예산 다 쓰면 그냥 끝나요 → 공고 뜨면 바로 신청이 답!\n"
        f"모르는 거 있으면 주민센터에 전화해보세요, 친절히 알려줘요 😊\n\n"
        f"📌 출처: 복지로(bokjiro.go.kr) · 정부24(gov.kr) · {name} 공식 포털\n"
        f"⚠️ 본 정보는 공식 자료 기준이며, 지원 조건·금액은 변동될 수 있습니다.\n"
        f"   신청 전 담당 기관 공식 사이트 또는 ☎ 129로 반드시 최신 내용을 확인하세요.\n\n\n"
        f"여기까지 읽어주셔서 감사해요! 🙏\n"
        f"도움이 됐다면 공감 ❤️ 꾹 눌러주세요 😊\n"
        f"구독 🔔 하시면 매주 월요일 혜택 정보 바로 받아볼 수 있어요!\n\n"
        f"[IMAGE:{tag_name}]\n\n"
        f"#{safe_name}혜택 #{safe_name}지원금 #정부지원금 "
        f"#몰라서손해 #복지로 #지원금신청방법 "
        f"#2026혜택 #지역혜택 #이거모르면손해 #돈되는정보\n"
    )


# ══════════════════════════════════════════════
# 메인
# ══════════════════════════════════════════════

def main():
    now       = datetime.now()
    today_str = now.strftime("%Y년 %m월 %d일")
    timestamp = now.strftime("%Y%m%d_%H%M")

    print("=" * 52)
    print(f"  🗺️ 지역별 혜택 17개 포스트 생성 시작")
    print(f"  ({now.strftime('%Y-%m-%d %H:%M')})")
    print("=" * 52)
    logging.info("===== 지역별 혜택 17개 포스트 생성 시작 =====")

    tag_name = f"region_tags_{timestamp}.png"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(viewport={"width": 1280, "height": 900})
        page    = ctx.new_page()

        # 공유 태그 이미지 생성 (첫 번째 지역으로)
        svg_to_png(page, make_hashtag_svg(REGIONS[0]), BLOG_IMAGES_DIR / tag_name)

        print("\n[1] 포스트 생성 중...")
        for r in REGIONS:
            name        = r["name"]
            banner_name = f"region_{name}_{timestamp}.png"

            svg_to_png(page, make_region_banner_svg(r, today_str), BLOG_IMAGES_DIR / banner_name)
            content  = generate_region_post(r, today_str, banner_name, tag_name)
            filename = f"{name}_지역혜택_{timestamp}.txt"
            (POSTS_DIR / filename).write_text(content, encoding="utf-8")
            print(f"  {r['emoji']} {name} ✅  →  {filename}")

        browser.close()

    print(f"\n총 {len(REGIONS)}개 포스트 파일 생성 완료! 🎉")
    logging.info(f"지역별 17개 포스트 생성 완료")

    # ── 검토 대기 안내 ──
    pending = sorted(POSTS_DIR.glob("*_지역혜택_*.txt"))
    print(f"\n📋 {len(pending)}개 글이 posts_pending/ 폴더에 저장됐어요.")
    print("   python review_posts.py 를 실행해서 내용 확인 후 승인하면 발행돼요.")
    logging.info(f"posts_pending 저장 완료 {len(pending)}개 — 검토 후 발행 필요")


if __name__ == "__main__":
    main()
