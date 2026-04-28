"""
텔레그램 Chat ID 확인 스크립트
봇에게 메시지를 보낸 후 이 스크립트를 실행하세요.
"""

import requests

# 봇 토큰
TOKEN = '8665339870:AAGpaHf0G-InntYbXTSmDYo9IiWI33Epzlc'

def get_chat_id():
    url = f'https://api.telegram.org/bot{TOKEN}/getUpdates'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data['ok'] and data['result']:
            # 가장 최근 메시지의 chat_id 가져오기
            chat_id = data['result'][-1]['message']['chat']['id']
            print(f"✅ Chat ID: {chat_id}")
            print(f"이 ID를 stock_config.json의 telegram_chat_id에 입력하세요.")
            return chat_id
        else:
            print("❌ 최근 메시지를 찾을 수 없습니다.")
            print("봇 @ttoktte_2026_bot 에게 메시지를 보낸 후 다시 실행하세요.")
    else:
        print(f"❌ API 오류: {response.status_code}")

if __name__ == "__main__":
    print("텔레그램 Chat ID 확인 중...")
    get_chat_id()