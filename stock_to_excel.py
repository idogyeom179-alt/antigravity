import yfinance as yf
import pandas as pd
from datetime import datetime

def download_stock_data_to_excel(ticker: str, start_date: str, end_date: str, output_filename: str):
    """
    주식 데이터를 야후 파이낸스에서 다운로드하여 엑셀 파일로 저장합니다.
    """
    print(f"[{ticker}] 데이터를 {start_date}부터 {end_date}까지 다운로드 중...")
    
    # yfinance를 사용하여 데이터 다운로드
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    
    if stock_data.empty:
        print("데이터를 찾을 수 없습니다. 티커나 날짜를 확인해주세요.")
        return
        
    # 엑셀 파일에 저장하기 위해 timezone 정보 제거 (엑셀은 datetime timezone을 지원하지 않음)
    if isinstance(stock_data.index, pd.DatetimeIndex) and stock_data.index.tz is not None:
        stock_data.index = stock_data.index.tz_localize(None)
    
    print(f"데이터를 '{output_filename}'에 저장하는 중...")
    
    # 엑셀 파일로 저장
    try:
        stock_data.to_excel(output_filename)
        print("엑셀 저장 완료!")
    except Exception as e:
        print(f"엑셀 저장 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    # 예시: 삼성전자 (한국 주식은 티커 뒤에 .KS를 붙입니다. 미국 주식은 AAPL, TSLA 등 그대로 사용)
    target_ticker = "005930.KS"  # 삼성전자
    
    # 현재 날짜 기준으로 기간 설정 (예: 2023년 1월 1일부터 2023년 12월 31일)
    start = "2023-01-01"
    end = "2023-12-31"
    
    filename = f"stock_data_{target_ticker.replace('.', '_')}.xlsx"
    
    download_stock_data_to_excel(target_ticker, start, end, filename)
