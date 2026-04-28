"""
festival_collect.py
전국 행사·축제 날짜별 × 지역별 포스팅 자동 생성 + 네이버 업로드
실행하면 현재 날짜 기준 가장 가까운 미래 기간 포스트를 자동 생성합니다.
※ 출처: 문화체육관광부 / 한국관광공사 / 각 지자체 공식 행사 정보 기반
"""
import sys, time, json, logging, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, date
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR        = Path("C:/Users/WIN10/.antigravity")
POSTS_DIR       = BASE_DIR / "posts_pending"
BLOG_IMAGES_DIR = BASE_DIR / "blog_images"
LOG_DIR         = BASE_DIR / "logs"
CONFIG_PATH     = BASE_DIR / "config.json"

for d in [POSTS_DIR, BLOG_IMAGES_DIR, LOG_DIR]:
    d.mkdir(exist_ok=True)

try:
    logging.basicConfig(
        filename=LOG_DIR / "festival_collect.log",
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8"
    )
except Exception:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# ══════════════════════════════════════════════════════════════
# Pixabay 이미지 다운로드
# ══════════════════════════════════════════════════════════════
def get_pixabay_image(query: str, save_path: Path) -> bool:
    try:
        cfg     = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        api_key = cfg.get("pixabay_key", "")
        if not api_key:
            return False
        encoded = urllib.parse.quote(query)
        url = (f"https://pixabay.com/api/?key={api_key}"
               f"&q={encoded}&image_type=photo&orientation=horizontal"
               f"&per_page=5&safesearch=true")
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        hits = data.get("hits", [])
        if not hits:
            return False
        img_url = hits[0]["largeImageURL"]
        req = urllib.request.Request(img_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            save_path.write_bytes(resp.read())
        print(f"   📸 Pixabay 이미지: {save_path.name}")
        return True
    except Exception as e:
        logging.warning(f"Pixabay 실패: {e}")
        return False


# ══════════════════════════════════════════════════════════════
# 전국 축제·행사 데이터 (날짜별 기간 단위)
# ══════════════════════════════════════════════════════════════
FESTIVAL_PERIODS = [

    # ─────────────────────────────────────────────────────
    # 2026년 4월 3~4주차
    # ─────────────────────────────────────────────────────
    {
        "period_id":    "2026_04_3w",
        "period_label": "2026년 4월 3~4주차",
        "date_range":   "4월 19일(일) ~ 4월 30일(목)",
        "date_start":   "2026-04-19",
        "date_end":     "2026-04-30",
        "month_emoji":  "🌸",
        "season":       "봄",
        "theme":        "봄꽃·나비·유채꽃 절정 시즌!",
        "pixabay":      "spring festival korea flowers",
        "regions": [
            {
                "name": "수도권 (서울·경기·인천)", "emoji": "🏙️", "color": "#ef4444",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "고양 국제꽃박람회",
                        "city": "경기 고양시 킨텍스·일산호수공원",
                        "period": "4월 25일(토) ~ 5월 11일(일)",
                        "highlight": "200만 송이 꽃의 향연! 국내 최대 꽃 전시회. 튤립·장미·수국 총출동",
                        "admission": "성인 8,000원 / 청소년 5,000원 / 어린이 3,000원",
                        "tip": "💡 평일 오전 9~11시 방문 시 줄 없이 한산해요",
                        "website": "https://www.goyang.go.kr",
                    },
                    {
                        "rank": "🥈",
                        "name": "서울 선유도공원 봄꽃 산책",
                        "city": "서울 영등포구 선유도공원",
                        "period": "4월 중순 ~ 5월 초 (상시)",
                        "highlight": "한강변 유채꽃·튤립 포토존, 무료 개방. 자전거 라이딩과 함께!",
                        "admission": "무료",
                        "tip": "💡 63빌딩 뷰 + 유채꽃 조합 = 인생샷 보장",
                        "website": "https://parks.seoul.go.kr",
                    },
                    {
                        "rank": "🥉",
                        "name": "수원 화성 봄 야경 행사",
                        "city": "경기 수원시 화성행궁 일원",
                        "period": "4월 중 주말 (야간 조명)",
                        "highlight": "유네스코 세계문화유산 화성에 펼쳐지는 봄밤 조명 쇼",
                        "admission": "성인 1,500원 (화성행궁 입장료)",
                        "tip": "💡 저녁 7시 이후 조명 켜질 때 방문하세요",
                        "website": "https://www.suwon.go.kr",
                    },
                ]
            },
            {
                "name": "강원", "emoji": "🏔️", "color": "#22c55e",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "춘천 봄꽃 페스티벌",
                        "city": "강원 춘천시 공지천유원지",
                        "period": "4월 18일(토) ~ 4월 27일(일)",
                        "highlight": "의암호 배경 벚꽃·개나리·철쭉 동시 개화! 강원 최대 봄 축제",
                        "admission": "무료",
                        "tip": "💡 공지천 자전거 대여(1시간 3,000원) 후 호수 한 바퀴 추천",
                        "website": "https://www.chuncheon.go.kr",
                    },
                    {
                        "rank": "🥈",
                        "name": "속초 설악산 봄 트레킹",
                        "city": "강원 속초시 설악산국립공원",
                        "period": "4월 ~ 5월 (상시)",
                        "highlight": "진달래·철쭉 피는 설악산 봄 트레킹. 비선대 코스 강력 추천",
                        "admission": "무료 (국립공원 입장료 없음)",
                        "tip": "💡 주말 교통체증 심해요 → 평일 또는 이른 아침 출발 추천",
                        "website": "https://seorak.knps.or.kr",
                    },
                ]
            },
            {
                "name": "충청 (충북·충남·대전·세종)", "emoji": "🔬", "color": "#f59e0b",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "청주 무심천 벚꽃 행사",
                        "city": "충북 청주시 무심천 일원",
                        "period": "4월 중순 (무료)",
                        "highlight": "무심천 5km 벚꽃 터널! 낮에는 꽃놀이, 밤엔 야간 조명 산책",
                        "admission": "무료",
                        "tip": "💡 저녁 조명 시간대(오후 7~10시)가 가장 아름다워요",
                        "website": "https://www.cheongju.go.kr",
                    },
                    {
                        "rank": "🥈",
                        "name": "영동군 난계국악축제",
                        "city": "충북 영동군 난계사·영동역 일원",
                        "period": "4월 말 ~ 5월 초 (매년 개최)",
                        "highlight": "한국 음악의 성인 박연 선생 기념 국악 공연·체험. 영동 와인 시음도!",
                        "admission": "무료 (일부 공연 유료)",
                        "tip": "💡 영동 포도밭 드라이브 + 와이너리 투어와 함께 묶어요",
                        "website": "https://www.yd.go.kr",
                    },
                    {
                        "rank": "🥉",
                        "name": "대전 엑스포과학공원 봄 행사",
                        "city": "대전시 유성구 엑스포과학공원",
                        "period": "4월 ~ 5월 (주말 행사)",
                        "highlight": "과학과 예술의 만남! 봄 시즌 특별 체험 부스 운영",
                        "admission": "성인 3,000원 / 어린이 2,000원",
                        "tip": "💡 아이와 함께라면 엑스포과학공원 1일 코스 추천",
                        "website": "https://www.daejeon.go.kr",
                    },
                ]
            },
            {
                "name": "전라 (전북·전남·광주)", "emoji": "🌾", "color": "#a855f7",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "함평 나비대축제",
                        "city": "전남 함평군 함평엑스포공원",
                        "period": "4월 24일(금) ~ 5월 4일(월)",
                        "highlight": "나비 10만 마리 방사! 국내 최대 나비 생태 체험 축제",
                        "admission": "성인 8,000원 / 청소년 6,000원 / 어린이 5,000원",
                        "tip": "💡 나비 방사는 오전 11시·오후 2시 하루 2회 (놓치지 마세요!)",
                        "website": "https://www.hampyeong.go.kr",
                    },
                    {
                        "rank": "🥈",
                        "name": "고창 청보리밭축제",
                        "city": "전북 고창군 공음면 학원농장",
                        "period": "4월 중순 ~ 5월 중순",
                        "highlight": "100만평 청보리밭 초록 물결! 드라마·광고 촬영지. 전국 인생샷 명소",
                        "admission": "성인 5,000원 / 청소년 4,000원 / 어린이 3,000원",
                        "tip": "💡 동쪽 언덕 전망대가 최고 포토 포인트! 오전 빛이 예뻐요",
                        "website": "https://www.gochang.go.kr",
                    },
                    {
                        "rank": "🥉",
                        "name": "담양 메타세콰이아길 봄 나들이",
                        "city": "전남 담양군 메타세콰이아 가로수길",
                        "period": "4월 ~ 5월 (상시)",
                        "highlight": "드라마 속 그 길! 8.5m 높이 메타세콰이아 나무 터널 2km",
                        "admission": "성인 2,000원 / 청소년 1,000원",
                        "tip": "💡 죽녹원 → 메타길 → 관방제림 당일 코스 완성!",
                        "website": "https://www.damyang.go.kr",
                    },
                ]
            },
            {
                "name": "경상 (경북·경남·부산·대구·울산)", "emoji": "🍇", "color": "#f97316",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "경주 벚꽃 보문단지 행사",
                        "city": "경북 경주시 보문단지·대릉원 일원",
                        "period": "4월 초~중순",
                        "highlight": "천년고도에 피어나는 벚꽃! 대릉원 고분군 + 벚꽃 조합은 세계 최고 경치",
                        "admission": "무료 (대릉원 입장료 3,000원 별도)",
                        "tip": "💡 야간 조명 켜지는 저녁 6시 이후가 낭만 최고",
                        "website": "https://www.gyeongju.go.kr",
                    },
                    {
                        "rank": "🥈",
                        "name": "하동 화개장터 벚꽃 십리길",
                        "city": "경남 하동군 화개장터 ~ 쌍계사",
                        "period": "4월 초~중순 (무료)",
                        "highlight": "드라마 속 그 벚꽃 터널! 화개장터에서 쌍계사까지 4km 벚꽃 십리길",
                        "admission": "무료",
                        "tip": "💡 이곳에서 만나는 연인은 백년해로! 전설의 명소",
                        "website": "https://www.hadong.go.kr",
                    },
                    {
                        "rank": "🥉",
                        "name": "부산 갈맷길 봄꽃 트레킹",
                        "city": "부산시 해운대·이기대 해안길",
                        "period": "4월 ~ 5월 (상시, 무료)",
                        "highlight": "부산 바다 + 봄꽃! 해운대부터 광안리까지 걷는 갈맷길 봄 코스",
                        "admission": "무료",
                        "tip": "💡 이기대 해안 산책로 → 오륙도 스카이워크 연계 코스 추천",
                        "website": "https://www.busan.go.kr",
                    },
                ]
            },
            {
                "name": "제주", "emoji": "🍊", "color": "#14b8a6",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "제주 유채꽃 & 왕벚꽃 축제",
                        "city": "제주특별자치도 제주시 일원",
                        "period": "4월 중순 ~ 5월 초 (무료)",
                        "highlight": "노란 유채꽃 + 핑크 벚꽃 동시 개화! 한국에서만 볼 수 있는 봄 경치",
                        "admission": "무료 (성산일출봉 5,000원 별도)",
                        "tip": "💡 동부 성산읍~표선 유채꽃 드라이브 코스가 최고 포인트",
                        "website": "https://www.jeju.go.kr",
                    },
                ]
            },
        ]
    },

    # ─────────────────────────────────────────────────────
    # 2026년 5월 1~2주차 (황금연휴 포함)
    # ─────────────────────────────────────────────────────
    {
        "period_id":    "2026_05_1w",
        "period_label": "2026년 5월 1~2주차",
        "date_range":   "5월 1일(금) ~ 5월 15일(금)",
        "date_start":   "2026-05-01",
        "date_end":     "2026-05-15",
        "month_emoji":  "🌿",
        "season":       "봄",
        "theme":        "황금연휴 전국 축제 총출동! 어린이날 특집",
        "pixabay":      "children day festival korea spring",
        "regions": [
            {
                "name": "수도권 (서울·경기·인천)", "emoji": "🏙️", "color": "#ef4444",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "서울 어린이날 특별행사",
                        "city": "서울 어린이대공원·서울대공원",
                        "period": "5월 5일(화) 어린이날 특별 개방",
                        "highlight": "어린이날 각종 무료 체험·공연. 어린이대공원 동물 먹이주기 행사",
                        "admission": "어린이대공원 무료 / 서울대공원 성인 3,000원",
                        "tip": "💡 오전 10시 이전 입장해야 줄 없이 즐길 수 있어요",
                        "website": "https://www.sisul.or.kr",
                    },
                    {
                        "rank": "🥈",
                        "name": "고양 국제꽃박람회 황금연휴",
                        "city": "경기 고양시 킨텍스·일산호수공원",
                        "period": "4월 25일(토) ~ 5월 11일(일) 계속",
                        "highlight": "200만 송이 꽃 전시회 황금연휴 절정! 장미·수국 추가 개화",
                        "admission": "성인 8,000원 / 청소년 5,000원 / 어린이 3,000원",
                        "tip": "💡 5월 1~5일 황금연휴 기간 특히 인기 → 셔틀버스 이용 권장",
                        "website": "https://www.goyang.go.kr",
                    },
                    {
                        "rank": "🥉",
                        "name": "이천 도자기축제",
                        "city": "경기 이천시 설봉공원",
                        "period": "5월 초 (매년 5월 개최)",
                        "highlight": "한국 도자기 1번지 이천! 도자기 직접 만들기 체험 + 전국 공모전",
                        "admission": "성인 5,000원 / 청소년 3,000원 / 어린이 2,000원",
                        "tip": "💡 직접 만든 도자기 구워서 집으로 가져갈 수 있어요",
                        "website": "https://www.icheon.go.kr",
                    },
                ]
            },
            {
                "name": "강원", "emoji": "🏔️", "color": "#22c55e",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "철원 한탄강 물윗길 트레킹",
                        "city": "강원 철원군 한탄강",
                        "period": "5월 (상시, 무료)",
                        "highlight": "DMZ 근처 한탄강 주상절리·물윗길 트레킹. 5월 신록이 가장 아름다워요",
                        "admission": "물윗길 입장료 별도",
                        "tip": "💡 한탄강 물윗길 — 물 위를 걷는 독특한 탐방로 꼭 체험!",
                        "website": "https://www.cwg.go.kr",
                    },
                ]
            },
            {
                "name": "충청 (충북·충남·대전·세종)", "emoji": "🔬", "color": "#f59e0b",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "보령 무창포 어촌 봄 체험",
                        "city": "충남 보령시 무창포해수욕장",
                        "period": "5월 ~ 6월 (어촌체험)",
                        "highlight": "신비의 바닷길 체험! 물이 갈라지는 무창포 바닷길 맨손 조개잡이",
                        "admission": "무료 (체험 프로그램 별도)",
                        "tip": "💡 물때표 확인 필수! 간조 시간 2시간 전 도착 권장",
                        "website": "https://www.boryeong.go.kr",
                    },
                    {
                        "rank": "🥈",
                        "name": "세종 호수공원 봄 페스티벌",
                        "city": "세종특별자치시 세종호수공원",
                        "period": "5월 주말 (무료)",
                        "highlight": "국내 최대 인공호수공원에서 펼쳐지는 봄 문화 행사. 플리마켓·공연",
                        "admission": "무료",
                        "tip": "💡 자전거로 호수 한 바퀴(약 4km) 돌면 딱 좋아요",
                        "website": "https://www.sejong.go.kr",
                    },
                ]
            },
            {
                "name": "전라 (전북·전남·광주)", "emoji": "🌾", "color": "#a855f7",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "전주 한지문화축제",
                        "city": "전북 전주시 전주한옥마을",
                        "period": "5월 초 (매년 개최)",
                        "highlight": "1,000년 전통 한지의 모든 것! 한지 만들기 체험·패션쇼·공예전시",
                        "admission": "무료",
                        "tip": "💡 한옥마을 막걸리·전주비빔밥과 함께 즐기면 완벽한 하루",
                        "website": "https://www.jeonju.go.kr",
                    },
                    {
                        "rank": "🥈",
                        "name": "남원 춘향제",
                        "city": "전북 남원시 광한루원",
                        "period": "5월 중 (매년 음력 4~5월)",
                        "highlight": "춘향과 이몽룡의 사랑 이야기! 전국 판소리·국악 공연, 미인대회",
                        "admission": "광한루원 입장료 3,000원",
                        "tip": "💡 광한루원 야경이 너무 예뻐요. 낮+밤 두 번 방문 추천",
                        "website": "https://www.namwon.go.kr",
                    },
                    {
                        "rank": "🥉",
                        "name": "진도 신비의 바닷길 축제",
                        "city": "전남 진도군 고군면 회동마을",
                        "period": "5월 초 (음력 2월 말일 전후)",
                        "highlight": "신비의 바닷길이 열리는 기적! 2.8km 바다가 갈라지는 세계 불가사의",
                        "admission": "무료",
                        "tip": "💡 물이 완전히 갈라지는 시간은 1~2시간뿐 → 시간표 확인 필수!",
                        "website": "https://www.jindo.go.kr",
                    },
                ]
            },
            {
                "name": "경상 (경북·경남·부산·대구·울산)", "emoji": "🍇", "color": "#f97316",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "청도 소싸움축제",
                        "city": "경북 청도군 청도소싸움경기장",
                        "period": "5월 초 (매년 5월 개최)",
                        "highlight": "한국 전통 소싸움! 국내 유일 상설 소싸움 경기장. 농촌 체험도 함께",
                        "admission": "성인 5,000원 / 청소년 3,000원",
                        "tip": "💡 와인터널(청도 특산 감와인) 시음 코스 함께 즐기세요",
                        "website": "https://www.cheongdo.go.kr",
                    },
                    {
                        "rank": "🥈",
                        "name": "통영 케이블카 & 봄 나들이",
                        "city": "경남 통영시 미륵산 케이블카",
                        "period": "5월 (상시)",
                        "highlight": "한려해상 국립공원 절경! 미륵산 정상에서 보는 남해 다도해 뷰",
                        "admission": "케이블카 왕복 성인 15,000원",
                        "tip": "💡 통영 케이블카 → 동피랑 벽화마을 → 중앙시장 당일 코스 완성",
                        "website": "https://www.tongyeong.go.kr",
                    },
                ]
            },
            {
                "name": "제주", "emoji": "🍊", "color": "#14b8a6",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "제주 세계유산축전",
                        "city": "제주특별자치도 한라산·용암동굴·성산일출봉",
                        "period": "5월 ~ 6월 (매년 개최)",
                        "highlight": "유네스코 세계자연유산 3곳 연계 특별 탐방 프로그램",
                        "admission": "성산일출봉 5,000원 / 만장굴 4,000원",
                        "tip": "💡 관음사 코스 야간 등반은 사전 예약 필수 (인기 폭발!)",
                        "website": "https://www.jeju.go.kr",
                    },
                ]
            },
        ]
    },

    # ─────────────────────────────────────────────────────
    # 2026년 5월 3~4주차
    # ─────────────────────────────────────────────────────
    {
        "period_id":    "2026_05_3w",
        "period_label": "2026년 5월 3~4주차",
        "date_range":   "5월 16일(토) ~ 5월 31일(일)",
        "date_start":   "2026-05-16",
        "date_end":     "2026-05-31",
        "month_emoji":  "🌹",
        "season":       "봄·초여름",
        "theme":        "장미·대나무·녹차 가득한 5월의 마지막!",
        "pixabay":      "rose festival garden korea",
        "regions": [
            {
                "name": "수도권 (서울·경기·인천)", "emoji": "🏙️", "color": "#ef4444",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "중랑 서울장미축제",
                        "city": "서울 중랑구 중랑천 장미광장",
                        "period": "5월 중순 ~ 6월 초 (무료)",
                        "highlight": "한국 최대 장미 축제! 중랑천 2.5km 장미 길 + 420만 송이 장미",
                        "admission": "무료",
                        "tip": "💡 야간 9시까지 조명 운영. 낮보다 밤 장미길이 더 낭만적!",
                        "website": "https://www.jungnang.go.kr",
                    },
                    {
                        "rank": "🥈",
                        "name": "과천 서울대공원 장미원",
                        "city": "경기 과천시 서울대공원",
                        "period": "5월 ~ 6월 (상시)",
                        "highlight": "1,000종 이상 장미 30,000그루! 장미원 내 향기 체험 구간",
                        "admission": "성인 3,000원 / 청소년 2,000원",
                        "tip": "💡 동물원+장미원+코끼리열차 하루 코스 가족 나들이 완성",
                        "website": "https://grandpark.seoul.go.kr",
                    },
                ]
            },
            {
                "name": "강원", "emoji": "🏔️", "color": "#22c55e",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "강릉 단오문화제",
                        "city": "강원 강릉시 남대천 단오장",
                        "period": "5월 하순 ~ 6월 초 (음력 5월 5일 기준)",
                        "highlight": "유네스코 세계무형문화유산! 씨름·그네타기·신통대길 퍼레이드",
                        "admission": "무료",
                        "tip": "💡 창포물에 머리 감기 체험 → 오전 10~11시 참여하세요",
                        "website": "https://www.gangneung.go.kr",
                    },
                ]
            },
            {
                "name": "충청 (충북·충남·대전·세종)", "emoji": "🔬", "color": "#f59e0b",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "공주 백제문화유산 탐방",
                        "city": "충남 공주시 공산성·송산리 고분군",
                        "period": "5월 (상시 개방)",
                        "highlight": "유네스코 세계유산 백제 역사 탐방. 공산성 성곽 걷기 + 무령왕릉",
                        "admission": "통합권 성인 3,000원 / 청소년 2,000원",
                        "tip": "💡 공산성 야경이 절경! 저녁 방문을 강력 추천해요",
                        "website": "https://www.gongju.go.kr",
                    },
                ]
            },
            {
                "name": "전라 (전북·전남·광주)", "emoji": "🌾", "color": "#a855f7",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "담양 대나무축제",
                        "city": "전남 담양군 관방제림·죽녹원",
                        "period": "5월 중순 ~ 하순 (매년 개최)",
                        "highlight": "울창한 대나무 숲 속 축제! 대나무 공예 체험·음식 체험·공연",
                        "admission": "죽녹원 입장료 성인 3,000원",
                        "tip": "💡 죽로차(대나무 이슬 녹차) 시음은 꼭 해보세요. 정말 특별해요",
                        "website": "https://www.damyang.go.kr",
                    },
                    {
                        "rank": "🥈",
                        "name": "보성 녹차밭 체험 (세계차엑스포)",
                        "city": "전남 보성군 보성녹차밭",
                        "period": "5월 중순 ~ 6월 초",
                        "highlight": "드라마 촬영지로 유명한 보성 녹차밭! 차 따기 체험·녹차 요리 체험",
                        "admission": "녹차밭 입장 성인 4,000원",
                        "tip": "💡 이른 아침 안개 낀 녹차밭이 최고 포토 타임!",
                        "website": "https://www.boseong.go.kr",
                    },
                ]
            },
            {
                "name": "경상 (경북·경남·부산·대구·울산)", "emoji": "🍇", "color": "#f97316",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "안동 하회마을 봄 체험",
                        "city": "경북 안동시 하회마을",
                        "period": "5월 (상시)",
                        "highlight": "유네스코 세계문화유산 하회마을! 봄 특별 체험 및 하회별신굿탈놀이",
                        "admission": "하회마을 입장료 성인 4,000원",
                        "tip": "💡 하회마을 → 병산서원 코스 전통문화 당일 여행 강력 추천",
                        "website": "https://www.andong.go.kr",
                    },
                ]
            },
            {
                "name": "제주", "emoji": "🍊", "color": "#14b8a6",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "한라산 영실 철쭉 시즌",
                        "city": "제주특별자치도 한라산 영실 코스",
                        "period": "5월 중순 (철쭉 개화 시즌)",
                        "highlight": "한라산 영실 코스 100만 그루 철쭉 대군락! 세계 최고 봄 트레킹",
                        "admission": "무료 (탐방 예약제)",
                        "tip": "💡 국립공원 탐방 예약 사이트에서 사전 예약 필수!",
                        "website": "https://hallasan.go.kr",
                    },
                ]
            },
        ]
    },

    # ─────────────────────────────────────────────────────
    # 2026년 7~8월 여름 시즌
    # ─────────────────────────────────────────────────────
    {
        "period_id":    "2026_07_summer",
        "period_label": "2026년 7~8월 여름 시즌",
        "date_range":   "7월 1일(수) ~ 8월 31일(월)",
        "date_start":   "2026-07-01",
        "date_end":     "2026-08-31",
        "month_emoji":  "🌊",
        "season":       "여름",
        "theme":        "바다·머드·불꽃! 여름 축제 총집합!",
        "pixabay":      "summer beach festival korea ocean",
        "regions": [
            {
                "name": "수도권 (서울·경기·인천)", "emoji": "🏙️", "color": "#ef4444",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "인천 펜타포트 록 페스티벌",
                        "city": "인천시 송도달빛축제공원",
                        "period": "8월 초 (3일간 개최, 연도별 날짜 확인)",
                        "highlight": "국내 최대 록 음악 축제! 국내외 유명 밴드 총출동. 야외 캠핑 존 운영",
                        "admission": "1일권 99,000원 내외 / 3일권 별도 (사전 구매 할인)",
                        "tip": "💡 텐트+침낭 준비하면 현장 캠핑도 가능. 여벌 옷 필수",
                        "website": "https://www.pentaportrock.com",
                    },
                ]
            },
            {
                "name": "강원", "emoji": "🏔️", "color": "#22c55e",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "화천 쏘가리 낚시 축제",
                        "city": "강원 화천군 화천천",
                        "period": "7~8월 여름 시즌",
                        "highlight": "화천군의 여름판 축제! 쏘가리 낚시·래프팅·계곡 물놀이",
                        "admission": "래프팅 1인 40,000원 내외",
                        "tip": "💡 화천 계곡물은 한여름에도 시원해요. 수영복 필참!",
                        "website": "https://www.hwacheon.go.kr",
                    },
                ]
            },
            {
                "name": "충청 (충북·충남·대전·세종)", "emoji": "🔬", "color": "#f59e0b",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "보령 머드축제",
                        "city": "충남 보령시 대천해수욕장",
                        "period": "7월 중순 ~ 하순 (약 10일간, 매년 개최)",
                        "highlight": "세계 4대 축제 중 하나! 천연 갯벌 머드로 온몸 도배하는 유일무이 체험",
                        "admission": "무료 (머드 체험장 입장 별도)",
                        "tip": "💡 흰 옷 입고 가면 머드 더 잘 보여요. 여벌 옷 필수!",
                        "website": "https://www.boryeong.go.kr",
                    },
                ]
            },
            {
                "name": "전라 (전북·전남·광주)", "emoji": "🌾", "color": "#a855f7",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "장흥 정남진 물축제",
                        "city": "전남 장흥군 탐진강 일원",
                        "period": "7월 말 ~ 8월 초",
                        "highlight": "탐진강에서 즐기는 물싸움·래프팅·튜브 타기! 무더위 탈출 최고 축제",
                        "admission": "무료 (일부 체험 유료)",
                        "tip": "💡 장흥 키조개·한우와 함께 즐기는 미식 여행도 추천",
                        "website": "https://www.jangheung.go.kr",
                    },
                ]
            },
            {
                "name": "경상 (경북·경남·부산·대구·울산)", "emoji": "🍇", "color": "#f97316",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "부산 바다축제",
                        "city": "부산시 해운대·광안리·송정 해수욕장",
                        "period": "8월 초 (약 1주일)",
                        "highlight": "대한민국 최대 해수욕장 축제! 해변 공연·불꽃쇼·서핑 대회",
                        "admission": "무료",
                        "tip": "💡 광안리 불꽃쇼는 연 1회! 날짜 미리 확인 후 자리 잡으세요",
                        "website": "https://www.busan.go.kr",
                    },
                ]
            },
            {
                "name": "제주", "emoji": "🍊", "color": "#14b8a6",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "제주 해녀축제",
                        "city": "제주특별자치도 구좌읍 해녀박물관",
                        "period": "9월 중순 ~ 하순",
                        "highlight": "유네스코 인류무형문화유산 해녀 문화! 해녀 물질 시연·해산물 직판",
                        "admission": "무료",
                        "tip": "💡 갓 잡은 성게·전복 현장에서 바로 먹는 게 진짜 제주 맛",
                        "website": "https://www.jeju.go.kr",
                    },
                ]
            },
        ]
    },

    # ─────────────────────────────────────────────────────
    # 2026년 9~10월 가을 시즌
    # ─────────────────────────────────────────────────────
    {
        "period_id":    "2026_09_autumn",
        "period_label": "2026년 9~10월 가을 시즌",
        "date_range":   "9월 1일(화) ~ 10월 31일(토)",
        "date_start":   "2026-09-01",
        "date_end":     "2026-10-31",
        "month_emoji":  "🍁",
        "season":       "가을",
        "theme":        "단풍·억새·탈춤! 가을 여행 최고 시즌",
        "pixabay":      "autumn festival korea maple leaves",
        "regions": [
            {
                "name": "수도권 (서울·경기·인천)", "emoji": "🏙️", "color": "#ef4444",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "수원 화성문화제",
                        "city": "경기 수원시 화성행궁·장안문 일원",
                        "period": "10월 초 (매년 개최)",
                        "highlight": "유네스코 세계유산 수원 화성! 정조대왕 능행차 재현 퍼레이드",
                        "admission": "화성행궁 1,500원 (행사 구역 무료)",
                        "tip": "💡 능행차 퍼레이드는 장안문→팔달문 코스. 길 옆에서 무료 관람",
                        "website": "https://www.suwon.go.kr",
                    },
                    {
                        "rank": "🥈",
                        "name": "서울 한강 불꽃축제",
                        "city": "서울 여의도 한강공원",
                        "period": "10월 초 (매년 개최)",
                        "highlight": "서울 하늘 가득 10만 발 불꽃! 대한민국 최대 무료 야외 행사",
                        "admission": "무료",
                        "tip": "💡 여의나루역 3~4시간 전 자리 선점 필수! 돗자리+간식 지참",
                        "website": "https://www.seoul.go.kr",
                    },
                    {
                        "rank": "🥉",
                        "name": "이천 쌀문화축제",
                        "city": "경기 이천시 설봉공원",
                        "period": "10월 중순 (매년 개최)",
                        "highlight": "이천 쌀 직거래 장터! 쌀 막걸리 시음·떡 체험·쌀 요리 대회",
                        "admission": "무료",
                        "tip": "💡 이천 쌀 10kg 현장 구매하면 서울 마트보다 훨씬 저렴해요",
                        "website": "https://www.icheon.go.kr",
                    },
                ]
            },
            {
                "name": "강원", "emoji": "🏔️", "color": "#22c55e",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "설악산 단풍 시즌",
                        "city": "강원 속초·인제·양양 설악산",
                        "period": "10월 초~중순 (단풍 절정)",
                        "highlight": "전국 최고의 단풍! 설악산 케이블카 + 비선대 코스 단풍 절정 기간",
                        "admission": "무료 (케이블카 왕복 15,000원)",
                        "tip": "💡 10월 5~15일이 단풍 절정. 평일 새벽 6시 입장 추천",
                        "website": "https://seorak.knps.or.kr",
                    },
                    {
                        "rank": "🥈",
                        "name": "강릉 커피축제",
                        "city": "강원 강릉시 녹색도시체험센터",
                        "period": "10월 말 (매년 개최)",
                        "highlight": "커피 도시 강릉의 커피 축제! 전국 바리스타 대회·커피 체험·시음",
                        "admission": "무료",
                        "tip": "💡 강릉 안목해변 커피거리에서 컵 들고 바다 보며 마시는 것도 필수!",
                        "website": "https://www.gangneung.go.kr",
                    },
                ]
            },
            {
                "name": "충청 (충북·충남·대전·세종)", "emoji": "🔬", "color": "#f59e0b",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "천안 흥타령 춤축제",
                        "city": "충남 천안시 천안삼거리공원",
                        "period": "9월 말 ~ 10월 초",
                        "highlight": "유네스코 창의도시 문화 축제! 흥타령 민요에 맞춘 전통 춤 경연",
                        "admission": "무료",
                        "tip": "💡 천안삼거리 능수버들 단풍과 함께 즐기면 더 좋아요",
                        "website": "https://www.cheonan.go.kr",
                    },
                ]
            },
            {
                "name": "전라 (전북·전남·광주)", "emoji": "🌾", "color": "#a855f7",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "전주 비빔밥축제",
                        "city": "전북 전주시 한옥마을",
                        "period": "10월 중순 (매년 개최)",
                        "highlight": "전통 비빔밥 거대 솥 비비기 체험! 전국 비빔밥 레시피 대회",
                        "admission": "무료",
                        "tip": "💡 한옥마을 막걸리 골목 + 비빔밥 + 가맥집이 전주 3대 코스",
                        "website": "https://www.jeonju.go.kr",
                    },
                ]
            },
            {
                "name": "경상 (경북·경남·부산·대구·울산)", "emoji": "🍇", "color": "#f97316",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "안동 국제탈춤페스티벌",
                        "city": "경북 안동시 하회마을·탈춤공원",
                        "period": "9월 말 ~ 10월 초 (매년 개최)",
                        "highlight": "유네스코 세계무형유산! 세계 27개국 탈춤 경연. 하회별신굿탈놀이",
                        "admission": "무료 (하회마을 입장료 별도)",
                        "tip": "💡 하회마을 야간 탈춤 공연은 반드시 예약! 매진 빠름",
                        "website": "https://www.maskdance.com",
                    },
                    {
                        "rank": "🥈",
                        "name": "부산 불꽃축제",
                        "city": "부산시 광안리해수욕장",
                        "period": "10월 말 (매년 개최)",
                        "highlight": "광안대교를 배경으로 펼쳐지는 불꽃쇼! 부산 최대 무료 야외 행사",
                        "admission": "무료",
                        "tip": "💡 광안리 맞은편 민락수변공원이 가장 좋은 관람 포인트",
                        "website": "https://www.busan.go.kr",
                    },
                ]
            },
            {
                "name": "제주", "emoji": "🍊", "color": "#14b8a6",
                "events": [
                    {
                        "rank": "🥇",
                        "name": "제주 억새·단풍 시즌",
                        "city": "제주특별자치도 한라산·오름 일원",
                        "period": "10월 ~ 11월",
                        "highlight": "한라산 억새 + 단풍 + 오름! 새별오름 억새 은빛 물결이 절정",
                        "admission": "무료 (한라산 탐방 예약제)",
                        "tip": "💡 새별오름 해질녘 억새밭이 SNS 최강 포토스팟",
                        "website": "https://www.jeju.go.kr",
                    },
                ]
            },
        ]
    },
]


# ══════════════════════════════════════════════════════════════
# 지역별 × 시즌별 Pixabay 사진 검색어
# ══════════════════════════════════════════════════════════════
REGION_PHOTO_QUERIES = {
    # 지역명 키워드 → (봄, 봄·초여름, 여름, 가을) 쿼리
    "수도권": {
        "봄":        "Seoul Korea spring cherry blossom festival",
        "봄·초여름": "Seoul Korea rose garden spring",
        "여름":      "Seoul Korea city summer night",
        "가을":      "Seoul Korea autumn leaves palace",
    },
    "강원": {
        "봄":        "Korea mountain spring flowers nature",
        "봄·초여름": "Korea mountain green forest spring",
        "여름":      "Korea river rafting summer nature",
        "가을":      "Korea mountain autumn maple forest",
    },
    "충청": {
        "봄":        "Korea countryside village spring nature",
        "봄·초여름": "Korea traditional village spring green",
        "여름":      "Korea beach ocean summer festival",
        "가을":      "Korea traditional culture autumn festival",
    },
    "전라": {
        "봄":        "Korea butterfly flowers spring festival",
        "봄·초여름": "Korea bamboo forest green nature",
        "여름":      "Korea river water festival summer",
        "가을":      "Korea traditional food culture autumn",
    },
    "경상": {
        "봄":        "Korea cherry blossom traditional temple spring",
        "봄·초여름": "Korea traditional culture UNESCO spring",
        "여름":      "Korea ocean beach summer festival",
        "가을":      "Korea UNESCO cultural heritage autumn festival",
    },
    "제주": {
        "봄":        "Jeju island Korea rapeseed flower spring",
        "봄·초여름": "Jeju island Korea azalea mountain spring",
        "여름":      "Jeju island Korea beach ocean summer",
        "가을":      "Jeju island Korea autumn scenic landscape",
    },
}

def get_region_photo_query(region_name: str, season: str) -> str:
    """지역명에서 대표 키워드 추출 후 Pixabay 검색어 반환"""
    for key in REGION_PHOTO_QUERIES:
        if key in region_name:
            return REGION_PHOTO_QUERIES[key].get(season, REGION_PHOTO_QUERIES[key].get("봄", "Korea festival"))
    return f"Korea {season} festival travel"


# ══════════════════════════════════════════════════════════════
# SVG 이미지 생성
# ══════════════════════════════════════════════════════════════

def _whale_svg_festival(cx, cy, size=1.0, female=False):
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


def make_festival_banner_svg(fp, today_str):
    color = "#4f46e5"
    emoji = fp["month_emoji"]
    # 💙 파란 고래 (남자) + 🩷 핑크 고래 (여자) 커플
    whale_m = _whale_svg_festival(cx=76,  cy=205, size=0.86, female=False)
    whale_f = _whale_svg_festival(cx=148, cy=210, size=0.68, female=True)
    whale = whale_m + "\n  " + whale_f
    return f"""<svg width="800" height="320" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0f172a"/>
      <stop offset="100%" style="stop-color:#1e3a5f"/>
    </linearGradient>
  </defs>
  <rect width="800" height="320" fill="url(#bg)"/>
  <circle cx="680" cy="60"  r="160" fill="{color}" opacity="0.12"/>
  <circle cx="120" cy="290" r="110" fill="#f59e0b"  opacity="0.06"/>
  <!-- 만화 고래 캐릭터 (어두운 배경용) -->
  {whale}
  <!-- 고래 말풍선 -->
  <path d="M178,95 Q178,74 200,74 L320,74 Q342,74 342,95 Q342,116 320,116 L208,116 L197,132 L204,116 L200,116 Q178,116 178,95 Z" fill="white" opacity="0.92" stroke="#7dd3fc" stroke-width="2"/>
  <text x="260" y="99" font-family="Arial" font-size="11" fill="#1e3a5f" text-anchor="middle" font-weight="bold">이번 주말에</text>
  <text x="260" y="113" font-family="Arial" font-size="11" fill="#1e3a5f" text-anchor="middle" font-weight="bold">어디 가세요? 🎪</text>
  <!-- 날짜 배지 -->
  <rect x="260" y="18" width="280" height="30" rx="15" fill="{color}"/>
  <text x="400" y="38" font-family="Arial" font-size="12" fill="white" text-anchor="middle" font-weight="bold">🗓️ {today_str} | 공식 행사 정보</text>
  <!-- 이모지 -->
  <text x="430" y="100" font-family="Arial" font-size="52" text-anchor="middle">{emoji}</text>
  <!-- 메인 타이틀 -->
  <text x="570" y="155" font-family="Arial" font-size="24" fill="white" text-anchor="middle" font-weight="bold">{fp["period_label"]} 전국 행사·축제</text>
  <text x="570" y="187" font-family="Arial" font-size="16" fill="#fbbf24" text-anchor="middle" font-weight="bold">{fp["theme"]}</text>
  <text x="570" y="213" font-family="Arial" font-size="12" fill="white" text-anchor="middle" opacity="0.8">{fp["date_range"]}</text>
  <rect x="390" y="238" width="175" height="36" rx="12" fill="{color}" opacity="0.5"/>
  <text x="477" y="261" font-family="Arial" font-size="12" fill="white" text-anchor="middle">📍 6개 권역별 정리</text>
  <rect x="578" y="238" width="170" height="36" rx="12" fill="#f59e0b"/>
  <text x="663" y="261" font-family="Arial" font-size="12" fill="white" text-anchor="middle" font-weight="bold">🎫 공식 출처 기반</text>
</svg>"""


def make_festival_map_svg(fp):
    title_color = "#1e3a5f"
    rows   = ""
    card_h = 64
    gap    = 10
    for i, region in enumerate(fp["regions"]):
        y    = 56 + i * (card_h + gap)
        rc   = region["color"]
        evts = region["events"]
        names = " · ".join(e["name"] for e in evts[:3])
        rows += f"""
  <rect x="12" y="{y}" width="776" height="{card_h}" rx="12" fill="{rc}" opacity="0.08"/>
  <rect x="12" y="{y}" width="5"   height="{card_h}" rx="2"  fill="{rc}"/>
  <text x="28" y="{y+24}" font-family="Arial" font-size="14" fill="#1e293b" font-weight="bold">{region["emoji"]} {region["name"]}</text>
  <text x="28" y="{y+48}" font-family="Arial" font-size="11" fill="#475569">{names[:75]}{"…" if len(names)>75 else ""}</text>"""

    total_h = 56 + len(fp["regions"]) * (card_h + gap) + 16
    return f"""<svg width="800" height="{total_h}" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="{total_h}" fill="#f8faff"/>
  <text x="400" y="36" font-family="Arial" font-size="15" fill="{title_color}" text-anchor="middle" font-weight="bold">🗺️ {fp["period_label"]} 지역별 행사·축제 한눈에 보기</text>
  {rows}
</svg>"""


def make_festival_hashtag_svg(fp):
    season_tags = {
        "봄":        ["#봄축제", "#봄여행", "#꽃구경", "#봄나들이", "#벚꽃"],
        "봄·초여름": ["#5월축제", "#봄여행", "#장미축제", "#나들이", "#초여름"],
        "여름":      ["#여름축제", "#바다여행", "#피서지", "#머드축제", "#여름휴가"],
        "가을":      ["#가을축제", "#단풍여행", "#가을나들이", "#억새", "#단풍명소"],
    }
    period_tags = season_tags.get(fp.get("season", "봄"), ["#봄축제"])
    base_tags   = [
        f"#{fp['period_label'].replace(' ', '')}",
        "#전국축제", "#지역행사", "#주말나들이", "#여행정보",
        "#축제일정", "#2026축제", f"#{fp['season']}여행",
        "#무료축제", "#지역행사총정리",
    ]
    all_tags = period_tags + base_tags
    widths   = [len(t) * 11 + 24 for t in all_tags]
    rects    = ""
    colors   = ["#4f46e5","#ef4444","#f97316","#22c55e","#a855f7","#14b8a6","#f59e0b","#ec4899"]
    x, y     = 20, 50
    for i, (tag, w) in enumerate(zip(all_tags, widths)):
        if x + w > 770:
            x = 20; y += 44
        cx = x + w // 2
        c  = colors[i % len(colors)]
        rects += f"""
  <rect x="{x}" y="{y}" width="{w}" height="34" rx="17" fill="{c}"/>
  <text x="{cx}" y="{y+22}" font-family="Arial" font-size="12" fill="white" text-anchor="middle" font-weight="bold">{tag}</text>"""
        x += w + 10
    total_h = y + 60
    return f"""<svg width="800" height="{total_h}" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="{total_h}" fill="#f8faff" rx="14"/>
  <rect x="2" y="2" width="796" height="{total_h-4}" rx="12" fill="none" stroke="#e0e7ff" stroke-width="2"/>
  <text x="400" y="30" font-family="Arial" font-size="14" fill="#4f46e5" text-anchor="middle" font-weight="bold">🔖 관련 태그</text>
  {rects}
</svg>"""


def svg_to_png(page, svg_content: str, png_path: Path) -> bool:
    try:
        page.goto("about:blank", wait_until="domcontentloaded")
        page.set_content(
            f"<!DOCTYPE html><html><body style='margin:0;padding:0;background:white'>"
            f"{svg_content}</body></html>", wait_until="domcontentloaded")
        time.sleep(0.1)
        el = page.query_selector("svg")
        if el:
            el.screenshot(path=str(png_path))
        else:
            page.screenshot(path=str(png_path), full_page=True)
        return True
    except Exception as e:
        logging.warning(f"PNG 변환 실패: {e}")
        return False


# ══════════════════════════════════════════════════════════════
# 블로그 포스트 본문 생성
# ══════════════════════════════════════════════════════════════

def generate_festival_post(fp, today_str, banner_name, map_name, tag_name, photo_name,
                           region_photos: dict = None):
    """
    region_photos: {"지역명": "파일명.jpg"} — 지역별 실사진 매핑
    """
    if region_photos is None:
        region_photos = {}

    regions_text = ""
    for region in fp["regions"]:
        regions_text += (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{region['emoji']} {region['name']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        # 지역 실사진 삽입 (있을 때만)
        rp = region_photos.get(region["name"])
        if rp:
            regions_text += f"[IMAGE:{rp}]\n\n"

        for ev in region["events"]:
            regions_text += (
                f"{ev['rank']} {ev['name']}\n\n"
                f"  📍 장소: {ev['city']}\n"
                f"  📅 기간: {ev['period']}\n"
                f"  🎟️ 입장료: {ev['admission']}\n"
                f"  ✨ 볼거리·즐길거리: {ev['highlight']}\n"
                f"  {ev['tip']}\n"
                f"  🔗 공식 안내: {ev['website']}\n\n\n"
            )

    photo_section = f"[IMAGE:{photo_name}]\n\n" if photo_name else ""
    tag_list = (
        f"#{fp['period_label'].replace(' ', '')} "
        f"#전국축제 #전국행사 #지역축제 #주말여행 "
        f"#축제일정 #2026축제 #{fp['season']}여행 "
        f"#무료축제 #지역행사총정리 #여행추천"
    )

    verify_box = (
        f"┌──────────────────────────────────────────┐\n"
        f"│  ✅ 정보 출처 및 검증 안내                          │\n"
        f"│  · 문화체육관광부 공식 행사 정보                     │\n"
        f"│  · 한국관광공사(visitkorea.or.kr)               │\n"
        f"│  · 각 지자체 공식 관광·행정 포털                    │\n"
        f"│  행사 일정·입장료는 변경될 수 있으니                  │\n"
        f"│  방문 전 각 공식 사이트에서 반드시 확인하세요! ⚠️      │\n"
        f"└──────────────────────────────────────────┘\n"
    )

    return (
        f"{fp['month_emoji']} {fp['period_label']} 전국 행사·축제 총정리ㅣ{fp['theme']} 지역별 일정 완벽 가이드 ({fp['date_range']})\n\n"
        f"[IMAGE:{banner_name}]\n\n"
        f"{photo_section}"
        f"{verify_box}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 {today_str} 기준 | {fp['date_range']} 전국 행사·축제 총정리\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n\n"
        f"안녕하세요! 🙌\n\n"
        f"이번 기간 어디 가야 할지 고민이세요? 😊\n\n"
        f"전국 방방곡곡에서 열리는\n"
        f"행사·축제 일정을 한 곳에 다 모았어요! 🗺️\n\n"
        f"수도권부터 제주까지 6개 권역별로 나눠\n"
        f"장소·입장료·꿀팁까지 꼼꼼하게 정리했으니\n"
        f"가고 싶은 곳 미리 찜해두세요 💕\n\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🗺️ 지역별 한눈에 보기\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"[IMAGE:{map_name}]\n\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎪 지역별 행사·축제 상세 정보\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{regions_text}"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧳 여행 전 꼭 확인하세요!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 날씨·현장 상황에 따라 행사가 변경·취소될 수 있어요\n"
        f"📌 입장료·운영 시간은 현장 상황에 따라 다를 수 있어요\n"
        f"📌 인기 축제는 주차 혼잡 → 대중교통 이용 강력 권장!\n"
        f"📌 각 축제 공식 SNS에서 최신 소식 반드시 확인해주세요\n"
        f"📌 어린이 동반 시 행사별 연령 제한 미리 확인하세요\n\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📢 정보 출처 및 유의사항\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"본 포스팅은 아래 공식 자료를 기반으로 작성했어요.\n\n"
        f"  🔍 문화체육관광부 공식 지역 축제 정보\n"
        f"  🔍 한국관광공사 (visitkorea.or.kr)\n"
        f"  🔍 각 지자체 공식 행정·관광 포털\n\n"
        f"⚠️ 축제 일정·입장료는 주최 측 사정에 따라 변경될 수 있습니다.\n"
        f"⚠️ 방문 전 각 공식 사이트에서 최신 일정을 반드시 확인하세요.\n"
        f"⚠️ 본 블로그는 정보 제공 목적이며, 결과를 보장하지 않습니다.\n\n\n"
        f"오늘도 여기까지 읽어주셔서 감사해요! 🙏\n"
        f"이번 주말 좋은 추억 많이 만드세요 😊\n"
        f"공감 ❤️ & 구독 🔔 눌러주시면 매주 축제 정보 드릴게요!\n\n"
        f"[IMAGE:{tag_name}]\n\n"
        f"{tag_list}\n"
    )


# ══════════════════════════════════════════════════════════════
# 메인 — 현재 날짜 기준 가장 가까운 기간들 생성 (최대 3개)
# ══════════════════════════════════════════════════════════════

def main():
    now       = datetime.now()
    today     = now.date()
    today_str = now.strftime("%Y년 %m월 %d일")
    timestamp = now.strftime("%Y%m%d_%H%M")

    print("=" * 56)
    print(f"  🎪 전국 행사·축제 포스팅 생성 시작")
    print(f"  ({now.strftime('%Y-%m-%d %H:%M')})")
    print("=" * 56)

    # 오늘 이후 종료되는 기간만 선택 (최대 3개), 5월만
    targets = []
    for fp in FESTIVAL_PERIODS:
        end_dt = date.fromisoformat(fp["date_end"])
        if "5월" in fp["period_label"] and end_dt >= today:
            targets.append(fp)
        if len(targets) >= 3:
            break

    if not targets:
        print("\n현재 생성할 축제 기간이 없습니다.")
        print("FESTIVAL_PERIODS 데이터를 업데이트해주세요!")
        return

    print(f"\n  → {len(targets)}개 기간 포스트 생성합니다")
    for t in targets:
        print(f"     ∙ {t['period_label']} ({t['date_range']})")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx     = browser.new_context(viewport={"width": 1280, "height": 900})
        page    = ctx.new_page()

        print("\n[1] 포스트 생성 중...")
        for fp in targets:
            pid = fp["period_id"]
            print(f"\n  {fp['month_emoji']} {fp['period_label']}...")

            banner_name = f"festival_{pid}_banner_{timestamp}.png"
            map_name    = f"festival_{pid}_map_{timestamp}.png"
            tag_name    = f"festival_{pid}_tags_{timestamp}.png"
            photo_name  = None

            # SVG → PNG 변환
            svg_to_png(page, make_festival_banner_svg(fp, today_str), BLOG_IMAGES_DIR / banner_name)
            svg_to_png(page, make_festival_map_svg(fp),               BLOG_IMAGES_DIR / map_name)
            svg_to_png(page, make_festival_hashtag_svg(fp),           BLOG_IMAGES_DIR / tag_name)

            # 대표 Pixabay 실사진 (기간 전체 썸네일용)
            photo_file = BLOG_IMAGES_DIR / f"festival_{pid}_photo_{timestamp}.jpg"
            if get_pixabay_image(fp["pixabay"], photo_file):
                photo_name = photo_file.name

            # 지역별 실사진 다운로드 (각 섹션 상단 삽입용)
            region_photos = {}
            season = fp.get("season", "봄")
            print(f"    📸 지역별 사진 다운로드 중...")
            for region in fp["regions"]:
                rname     = region["name"]
                query     = get_region_photo_query(rname, season)
                rp_file   = BLOG_IMAGES_DIR / f"festival_{pid}_{rname[:2]}_{timestamp}.jpg"
                if get_pixabay_image(query, rp_file):
                    region_photos[rname] = rp_file.name

            # 포스트 파일 저장
            content  = generate_festival_post(
                fp, today_str, banner_name, map_name, tag_name, photo_name, region_photos
            )
            filename = f"축제_{fp['period_label'].replace(' ', '_')}_{timestamp}.txt"
            (POSTS_DIR / filename).write_text(content, encoding="utf-8")
            print(f"    ✅ 저장: {filename} (지역사진 {len(region_photos)}개 포함)")

        browser.close()

    print(f"\n총 {len(targets)}개 포스트 파일 생성 완료! 🎉")
    logging.info(f"축제 포스트 {len(targets)}개 생성 완료")

    # ── 검토 대기 안내 ──
    pending = sorted(POSTS_DIR.glob("축제_*.txt"))
    print(f"\n📋 {len(pending)}개 글이 posts_pending/ 폴더에 저장됐어요.")
    print("   python review_posts.py 를 실행해서 내용 확인 후 승인하면 발행돼요.")
    logging.info(f"posts_pending 저장 완료 {len(pending)}개 — 검토 후 발행 필요")


if __name__ == "__main__":
    main()
