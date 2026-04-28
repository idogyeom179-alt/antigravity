"""
주식 분석 및 텔레그램 알림 프로그램
매일 오전 8시에 보유 주식 종목을 분석하여 텔레그램으로 메시지를 보냅니다.
"""

import yfinance as yf
import requests
import json
from datetime import datetime, timedelta
import logging
import sys
from pathlib import Path

# 설정
BASE_DIR = Path("C:/Users/WIN10/.antigravity")
LOG_DIR = BASE_DIR / "logs"
CONFIG_PATH = BASE_DIR / "stock_config.json"

LOG_DIR.mkdir(exist_ok=True)

# 로깅 설정
logging.basicConfig(
    filename=LOG_DIR / "stock_analysis.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

# 보유 주식 종목 (한국 주식 티커)
# yfinance에서는 한국 주식은 .KS를 붙임
STOCKS = {
    "005930.KS": "삼성전자",
    "000660.KS": "SK하이닉스",
    "035420.KS": "NAVER",
    "207940.KS": "삼성바이오로직스",
    "005380.KS": "현대차"
}

def load_config():
    """설정 파일 로드"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "telegram_bot_token": "",
        "telegram_chat_id": ""
    }

def get_stock_data(ticker, name):
    """주식 데이터 가져오기"""
    try:
        # 최근 5일 데이터 가져오기
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")

        if hist.empty:
            return None

        # 최신 데이터
        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else latest

        # 분석 데이터
        current_price = latest['Close']
        prev_price = prev['Close']
        change = current_price - prev_price
        change_percent = (change / prev_price) * 100 if prev_price != 0 else 0

        # 거래량
        volume = latest['Volume']
        avg_volume = hist['Volume'].mean()

        # 분석 결과
        analysis = "🟢 상승" if change > 0 else "🔴 하락" if change < 0 else "⚪ 보합"

        return {
            'name': name,
            'ticker': ticker,
            'current_price': round(current_price, 2),
            'change': round(change, 2),
            'change_percent': round(change_percent, 2),
            'volume': volume,
            'avg_volume': round(avg_volume, 0),
            'analysis': analysis,
            'date': latest.name.strftime('%Y-%m-%d')
        }

    except Exception as e:
        logging.error(f"주식 데이터 가져오기 실패 {ticker}: {e}")
        return None

def analyze_stocks():
    """모든 보유 주식 분석"""
    results = []
    print("📊 주식 데이터 분석 중...")

    for ticker, name in STOCKS.items():
        data = get_stock_data(ticker, name)
        if data:
            results.append(data)
            print(f"✅ {name}: {data['current_price']}원 ({data['change_percent']:+.2f}%)")
        else:
            print(f"❌ {name}: 데이터 가져오기 실패")

    return results

def create_message(results):
    """텔레그램 메시지 생성"""
    today = datetime.now().strftime('%Y년 %m월 %d일')

    message = f"📈 <b>{today} 주식 분석 리포트</b>\n\n"

    total_change = 0
    for stock in results:
        message += f"{stock['analysis']} <b>{stock['name']}</b>\n"
        message += f"💰 {stock['current_price']:,}원 ({stock['change_percent']:+.2f}%)\n"
        message += f"📊 거래량: {stock['volume']:,}\n\n"
        total_change += stock['change_percent']

    avg_change = total_change / len(results) if results else 0
    message += f"📊 <b>평균 변동률: {avg_change:+.2f}%</b>\n"
    message += f"📅 총 {len(results)}개 종목 분석 완료"

    return message

def send_telegram_message(message, config):
    """텔레그램 메시지 전송"""
    bot_token = config.get('telegram_bot_token', '')
    chat_id = config.get('telegram_chat_id', '')

    if not bot_token or not chat_id:
        print("❌ 텔레그램 봇 토큰 또는 채팅 ID가 설정되지 않았습니다.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ 텔레그램 메시지 전송 성공")
            return True
        else:
            print(f"❌ 텔레그램 메시지 전송 실패: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ 텔레그램 API 오류: {e}")
        return False

def main():
    print("=" * 50)
    print("  📈 주식 분석 및 텔레그램 알림")
    print("=" * 50)

    logging.info("주식 분석 시작")

    # 설정 로드
    config = load_config()

    # 주식 분석
    results = analyze_stocks()

    if not results:
        print("❌ 분석할 주식 데이터가 없습니다.")
        return

    # 메시지 생성
    message = create_message(results)
    print("\n" + "=" * 50)
    print("📤 생성된 메시지:")
    print(message)
    print("=" * 50)

    # 텔레그램 전송
    success = send_telegram_message(message, config)

    print("\n" + "=" * 50)
    print(f"  결과: {'✅ 성공' if success else '❌ 실패'}")
    print("=" * 50)

    logging.info(f"주식 분석 완료: {len(results)}개 종목, 텔레그램 전송 {'성공' if success else '실패'}")

if __name__ == "__main__":
    main()