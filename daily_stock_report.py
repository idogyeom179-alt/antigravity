#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from datetime import datetime
from stock_analyzer import StockAnalyzer, load_stocks_config
from kakao_message import send_stock_report

def main():
    """매일 주식 분석 보고서를 생성하고 카카오톡으로 전송합니다."""
    print(f"📊 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 주식 분석 시작")

    try:
        # 주식 설정 로드
        config = load_stocks_config()
        if not config:
            print("❌ 주식 설정을 로드할 수 없습니다.")
            return False

        # 주식 분석 수행
        analyzer = StockAnalyzer(config)
        report = analyzer.generate_report()

        print("📝 분석 보고서 생성 완료")
        print(report)

        # 카카오톡으로 보고서 전송
        success = send_stock_report(report)

        if success:
            print("✅ 주식 분석 보고서 전송 완료")
            return True
        else:
            print("❌ 주식 분석 보고서 전송 실패")
            return False

    except Exception as e:
        error_message = f"❌ 주식 분석 중 오류 발생: {str(e)}"
        print(error_message)

        # 오류 메시지도 카카오톡으로 전송
        try:
            send_stock_report(error_message)
        except:
            pass

        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)