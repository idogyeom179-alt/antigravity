import urllib.request
import urllib.parse
import json

TOKEN = '8665339870:AAEHrcfOEO0rEQfbeeiHSFAokIafVs7UMAE'

def send_message():
    get_updates_url = f'https://api.telegram.org/bot{TOKEN}/getUpdates'
    try:
        req = urllib.request.Request(get_updates_url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        print(f'Error getting updates: {e}')
        return

    chat_id = None
    if data.get('ok') and data.get('result'):
        # Get the chat ID of the latest message
        messages = [res for res in data['result'] if 'message' in res]
        if messages:
            chat_id = messages[-1]['message']['chat']['id']

    if chat_id:
        send_url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
        payload = {'chat_id': chat_id, 'text': '자비스 연결 성공!'}
        payload_data = json.dumps(payload).encode('utf-8')
        try:
            req = urllib.request.Request(send_url, data=payload_data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                if result.get('ok'):
                    print('메시지 전송 성공!')
                else:
                    print(f'메시지 전송 실패: {result}')
        except Exception as e:
            print(f'Error sending message: {e}')
    else:
        print('chat_id를 찾을 수 없습니다. 텔레그램에서 봇에게 먼저 아무 메시지나 보내주신 후 다시 실행해주세요.')

if __name__ == '__main__':
    send_message()
