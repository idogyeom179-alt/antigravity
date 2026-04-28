import yfinance as yf
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

class StockAnalyzer:
    def __init__(self, stocks_config: Dict[str, Any]):
        self.stocks = stocks_config.get('stocks', [])

    def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """주식의 현재 정보를 가져옵니다."""
        try:
            stock = yf.Ticker(ticker)

            # 현재 가격 정보
            info = stock.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))

            # 전일 대비 변동률 계산
            hist = stock.history(period='2d')
            if len(hist) >= 2:
                prev_close = hist.iloc[-2]['Close']
                change_percent = ((current_price - prev_close) / prev_close) * 100
            else:
                change_percent = 0

            return {
                'current_price': current_price,
                'change_percent': change_percent,
                'market_cap': info.get('marketCap', 0),
                'volume': info.get('volume', 0),
                'success': True
            }
        except Exception as e:
            return {
                'error': str(e),
                'success': False
            }

    def analyze_portfolio(self) -> List[Dict[str, Any]]:
        """보유 주식 포트폴리오를 분석합니다."""
        results = []

        for stock in self.stocks:
            ticker = stock['ticker']
            name = stock['name']
            quantity = stock['quantity']
            avg_price = stock['avg_price']

            # 주식 정보 가져오기
            stock_info = self.get_stock_info(ticker)

            if stock_info['success']:
                current_price = stock_info['current_price']
                change_percent = stock_info['change_percent']

                # 수익률 계산
                total_investment = quantity * avg_price
                current_value = quantity * current_price
                profit_loss = current_value - total_investment
                profit_loss_percent = (profit_loss / total_investment) * 100

                results.append({
                    'name': name,
                    'ticker': ticker,
                    'quantity': quantity,
                    'avg_price': avg_price,
                    'current_price': current_price,
                    'change_percent': change_percent,
                    'total_investment': total_investment,
                    'current_value': current_value,
                    'profit_loss': profit_loss,
                    'profit_loss_percent': profit_loss_percent,
                    'success': True
                })
            else:
                results.append({
                    'name': name,
                    'ticker': ticker,
                    'error': stock_info.get('error', 'Unknown error'),
                    'success': False
                })

        return results

    def generate_report(self) -> str:
        """분석 결과를 바탕으로 보고서를 생성합니다."""
        results = self.analyze_portfolio()

        report = f"📊 {datetime.now().strftime('%Y년 %m월 %d일')} 주식 포트폴리오 분석\n\n"

        total_investment = 0
        total_current_value = 0

        for result in results:
            if result['success']:
                name = result['name']
                current_price = result['current_price']
                change_percent = result['change_percent']
                profit_loss = result['profit_loss']
                profit_loss_percent = result['profit_loss_percent']

                # 가격 변동 표시
                change_symbol = "📈" if change_percent > 0 else "📉" if change_percent < 0 else "➡️"
                profit_symbol = "💰" if profit_loss > 0 else "❌" if profit_loss < 0 else "➡️"

                report += f"🏢 {name}\n"
                report += f"   현재가: {current_price:,.0f}원 ({change_symbol} {change_percent:+.2f}%)\n"
                report += f"   평가손익: {profit_loss:,.0f}원 ({profit_symbol} {profit_loss_percent:+.2f}%)\n\n"

                total_investment += result['total_investment']
                total_current_value += result['current_value']
            else:
                report += f"🏢 {result['name']}\n"
                report += f"   ❌ 데이터 조회 실패: {result.get('error', 'Unknown error')}\n\n"

        # 총합 계산
        total_profit_loss = total_current_value - total_investment
        total_profit_loss_percent = (total_profit_loss / total_investment) * 100 if total_investment > 0 else 0

        profit_symbol = "💰" if total_profit_loss > 0 else "❌" if total_profit_loss < 0 else "➡️"

        report += "📈 전체 포트폴리오 요약\n"
        report += f"   총 투자금액: {total_investment:,.0f}원\n"
        report += f"   현재 평가액: {total_current_value:,.0f}원\n"
        report += f"   총 손익: {total_profit_loss:,.0f}원 ({profit_symbol} {total_profit_loss_percent:+.2f}%)"

        return report

def load_stocks_config() -> Dict[str, Any]:
    """주식 설정 파일을 로드합니다."""
    try:
        with open('my_stocks.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("my_stocks.json 파일을 찾을 수 없습니다.")
        return {}
    except json.JSONDecodeError:
        print("my_stocks.json 파일 형식이 잘못되었습니다.")
        return {}

if __name__ == "__main__":
    config = load_stocks_config()
    analyzer = StockAnalyzer(config)
    report = analyzer.generate_report()
    print(report)