import qrcode
from PIL import Image

# 작업 일지 앱 URL
url = "https://worklog-coral.vercel.app"

# QR 코드 생성
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr.add_data(url)
qr.make(fit=True)

# QR 코드 이미지 생성
img = qr.make_image(fill_color="black", back_color="white")

# 이미지 저장
img.save("worklog_qr.png")
print("QR 코드가 생성되었습니다: worklog_qr.png")