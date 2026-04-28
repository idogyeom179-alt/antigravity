"""
image_uploader.py
네이버 블로그에 이미지 포함 포스팅 + IMAGE 마커 추출
"""

import re
import time
import json
import logging
from pathlib import Path

URL_RE  = re.compile(r'(https?://[^\s\u3000-\u9fff\)]+)')
LINK_RE = re.compile(r'\[LINK:([^\|]+)\|([^\]]+)\]')


def _js_len(text: str) -> int:
    """JS .length 기준 문자 수 (이모지 서로게이트 쌍은 2로 계산)"""
    return len(text.encode('utf-16-le')) // 2


def _insert_hyperlink(page, text: str, url: str):
    """텍스트를 선택 후 Ctrl+K로 하이퍼링크 삽입"""
    # 1. 링크 표시 텍스트 붙여넣기
    page.evaluate(f"navigator.clipboard.writeText({json.dumps(text)})")
    page.keyboard.press("Control+v")
    time.sleep(0.3)
    # 2. 방금 입력한 텍스트 선택 (JS .length 기준 — 이모지 2칸 정확히 처리)
    for _ in range(_js_len(text)):
        page.keyboard.press("Shift+ArrowLeft")
    time.sleep(0.2)
    # 3. Ctrl+K 로 링크 다이얼로그 열기
    page.keyboard.press("Control+k")
    time.sleep(1.5)
    # 4. URL 입력 후 확인
    page.keyboard.type(url)
    time.sleep(0.3)
    page.keyboard.press("Enter")
    time.sleep(0.5)


def _paste_with_links(page, content):
    """[LINK:텍스트|URL] 마커 및 일반 URL을 클릭 가능한 링크로 삽입"""
    _paste_content_smart(page, content)


def _paste_content_smart(page, content):
    """[LINK:] 마커와 URL을 모두 처리하는 스마트 붙여넣기"""
    # [LINK:텍스트|URL] 마커 우선 분리
    tokens = re.split(r'(\[LINK:[^\]]+\])', content)
    for token in tokens:
        if not token:
            continue
        link_match = re.match(r'\[LINK:([^\|]+)\|([^\]]+)\]', token)
        if link_match:
            display_text = link_match.group(1).strip()
            url          = link_match.group(2).strip()
            _insert_hyperlink(page, display_text, url)
        else:
            # 일반 텍스트 안에서 URL 분리
            sub_parts = URL_RE.split(token)
            for sp in sub_parts:
                if not sp:
                    continue
                if URL_RE.match(sp):
                    url = sp.strip()
                    page.evaluate(f"navigator.clipboard.writeText({json.dumps(url)})")
                    page.keyboard.press("Control+v")
                    time.sleep(0.5)
                    try:
                        page.click('button:has-text("확인")', timeout=800)
                        time.sleep(0.2)
                    except:
                        pass
                    page.keyboard.press("Enter")
                    time.sleep(0.3)
                else:
                    page.evaluate(f"navigator.clipboard.writeText({json.dumps(sp)})")
                    page.keyboard.press("Control+v")
                    time.sleep(0.3)

def extract_svg_markers(content: str) -> list:
    pattern = r'\[IMAGE:([^\]]+)\]'
    markers = re.findall(pattern, content)
    return markers


def _upload_image_to_naver(page, image_path: Path) -> bool:
    """네이버 SE3 편집기에 이미지 파일 업로드"""
    try:
        # SE3 툴바에서 이미지 버튼 클릭 → 파일 다이얼로그 열기
        with page.expect_file_chooser(timeout=10000) as fc_info:
            page.evaluate("""
                () => {
                    // SE3 툴바 이미지 버튼 찾기 (다양한 방법 시도)
                    const selectors = [
                        'button[class*="image"]',
                        '.se-toolbar button[title*="사진"]',
                        '.se-toolbar button[title*="이미지"]',
                        '.se-toolbar button[data-name*="image"]',
                        '.se-toolbar-item--image button',
                        '[class*="se-toolbar"] [class*="image"] button',
                    ];
                    for (const sel of selectors) {
                        try {
                            const btn = document.querySelector(sel);
                            if (btn) { btn.click(); return true; }
                        } catch(e) {}
                    }
                    // 폴백: 모든 툴바 버튼 순회
                    const allBtns = document.querySelectorAll('.se-toolbar button');
                    for (const btn of allBtns) {
                        const cls = (btn.className || '') + (btn.getAttribute('title') || '');
                        if (/image|사진|photo|img/i.test(cls)) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
        file_chooser = fc_info.value
        file_chooser.set_files(str(image_path))
        time.sleep(4)
        return True

    except Exception as e1:
        # 폴백: 파일 입력에 직접 설정
        try:
            page.evaluate("""
                () => {
                    document.querySelectorAll('input[type="file"]').forEach(el => {
                        el.style.display = 'block';
                        el.style.opacity = '1';
                        el.style.position = 'fixed';
                        el.style.zIndex = '9999';
                    });
                }
            """)
            page.set_input_files('input[type="file"]', str(image_path))
            time.sleep(4)
            return True
        except Exception as e2:
            logging.warning(f"이미지 업로드 실패 ({image_path.name}): {e1} / {e2}")
            return False


def post_to_naver_with_images(page, config, title: str, content: str) -> bool:
    try:
        BASE_DIR = Path("C:/Users/WIN10/.antigravity")
        blog_images_dir = BASE_DIR / "blog_images"
        blog_id = config["naver"]["blog_id"]

        page.goto(
            f"https://blog.naver.com/PostWriteForm.naver?blogId={blog_id}",
            wait_until="domcontentloaded"
        )
        page.bring_to_front()
        time.sleep(6)

        try:
            page.click(".se-help-panel-close-button", timeout=3000)
            time.sleep(0.5)
        except:
            pass

        # 제목 입력
        try:
            page.click(".se-documentTitle")
            time.sleep(0.5)
            page.keyboard.press("Control+a")
            page.keyboard.press("Delete")
            page.evaluate(f"navigator.clipboard.writeText({json.dumps(title)})")
            time.sleep(0.3)
            page.keyboard.press("Control+v")
            time.sleep(0.5)
        except Exception as e:
            logging.warning(f"네이버 제목 입력 실패: {e}")

        # 본문 클릭
        try:
            page.wait_for_selector(".se-content", timeout=5000)
            page.click(".se-content")
            time.sleep(0.5)
        except Exception as e:
            logging.error(f"네이버 본문 클릭 실패: {e}")
            return False

        # 이미지 마커 기준으로 분할
        pattern = r'(\[IMAGE:[^\]]+\])'
        parts = re.split(pattern, content)

        img_ok = 0
        img_fail = 0

        for part in parts:
            marker_match = re.match(r'\[IMAGE:([^\]]+)\]', part)
            if marker_match:
                image_filename = marker_match.group(1).strip()
                image_path = blog_images_dir / image_filename

                if image_path.exists():
                    if _upload_image_to_naver(page, image_path):
                        img_ok += 1
                        print(f"   이미지 업로드: {image_filename} ✅")
                    else:
                        img_fail += 1
                        print(f"   이미지 업로드 실패: {image_filename} ❌")
                else:
                    img_fail += 1
                    logging.warning(f"이미지 파일 없음: {image_path}")
                    print(f"   이미지 파일 없음: {image_filename} ⚠️")
            else:
                text = part.strip()
                if text:
                    try:
                        _paste_with_links(page, text)
                        page.keyboard.press("Enter")
                        time.sleep(0.3)
                    except Exception as e:
                        logging.warning(f"텍스트 입력 실패: {e}")

        time.sleep(2)

        # 발행 버튼
        page.evaluate("""
            () => {
                const btn = Array.from(document.querySelectorAll('button'))
                    .find(b => b.className.includes('publish_btn'));
                if (btn) btn.click();
            }
        """)
        time.sleep(3)

        page.evaluate("""
            () => {
                const btn = Array.from(document.querySelectorAll('button'))
                    .find(b => b.className.includes('confirm_btn'));
                if (btn) btn.click();
            }
        """)
        time.sleep(4)

        if img_fail == 0:
            print(f"   네이버 ✅ (이미지 {img_ok}개 포함)")
        else:
            print(f"   네이버 ✅ (이미지 {img_ok}개 성공 / {img_fail}개 실패)")
        logging.info(f"네이버 이미지 포스팅 완료: {title} (이미지 {img_ok}/{img_ok+img_fail})")
        return True

    except Exception as e:
        logging.error(f"네이버 이미지 포스팅 실패: {e}")
        print(f"   네이버 ❌ {e}")
        return False
