import requests
import json
from typing import Dict, Any, Optional

class KakaoMessenger:
    def __init__(self, access_token: str, channel_id: str):
        self.access_token = access_token
        self.channel_id = channel_id
        self.base_url = "https://kapi.kakao.com"

    def send_message(self, message: str) -> bool:
        """카카오톡 채널로 메시지를 전송합니다."""
        url = f"{self.base_url}/v2/api/talk/memo/default/send"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "template_object": json.dumps({
                "object_type": "text",
                "text": message,
                "link": {
                    "web_url": "https://finance.naver.com/",
                    "mobile_web_url": "https://finance.naver.com/"
                }
            })
        }

        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()

            result = response.json()
            if result.get('result_code') == 0:
                print("✅ 카카오톡 메시지 전송 성공")
                return True
            else:
                print(f"❌ 카카오톡 메시지 전송 실패: {result}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ 카카오톡 API 요청 실패: {e}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ 응답 파싱 실패: {e}")
            return False

    def send_me_message(self, message: str) -> bool:
        """나에게 메시지를 전송합니다 (카카오톡 채널이 아닌 개인 메시지)."""
        url = f"{self.base_url}/v2/api/talk/memo/send"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "template_object": json.dumps({
                "object_type": "text",
                "text": message
            })
        }

        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()

            result = response.json()
            if result.get('result_code') == 0:
                print("✅ 카카오톡 나에게 메시지 전송 성공")
                return True
            else:
                print(f"❌ 카카오톡 나에게 메시지 전송 실패: {result}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ 카카오톡 API 요청 실패: {e}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ 응답 파싱 실패: {e}")
            return False

def load_kakao_config() -> Dict[str, str]:
    """카카오 설정을 로드합니다."""
    try:
        with open('my_stocks.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            kakao_config = config.get('kakao', {})
            return {
                'access_token': kakao_config.get('access_token', ''),
                'channel_id': kakao_config.get('channel_id', '')
            }
    except FileNotFoundError:
        print("my_stocks.json 파일을 찾을 수 없습니다.")
        return {}
    except json.JSONDecodeError:
        print("my_stocks.json 파일 형식이 잘못되었습니다.")
        return {}

def send_stock_report(message: str) -> bool:
    """주식 분석 보고서를 카카오톡으로 전송합니다."""
    config = load_kakao_config()

    if not config.get('access_token'):
        print("❌ 카카오 액세스 토큰이 설정되지 않았습니다.")
        print("my_stocks.json 파일의 kakao.access_token을 설정해주세요.")
        return False

    messenger = KakaoMessenger(
        access_token=config['access_token'],
        channel_id=config.get('channel_id', '')
    )

    # 나에게 메시지 전송 시도
    return messenger.send_me_message(message)

if __name__ == "__main__":
    # 테스트용 메시지
    test_message = "테스트 메시지입니다."
    send_stock_report(test_message)