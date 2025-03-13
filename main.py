from flask import Flask
import os
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
import holidays
from pykrx import stock
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


print("✅ Cloud Run 자동 실행 시작!")

# ✅ API 키 및 이메일 비밀번호 환경 변수에서 불러오기
API_KEY = os.getenv("API_KEY")  # Seibro API Key
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Gmail 앱 비밀번호

# ✅ 오늘 날짜 설정
today = pd.Timestamp.today().strftime("%Y%m%d")

# ✅ 한국 공휴일 정보 가져오기
current_year = pd.Timestamp.today().year
next_year = current_year + 1
kr_holidays = holidays.Korea(years=[current_year, next_year])

# ✅ KRX 기준 N영업일 후 날짜 반환 함수
def get_nth_business_day(start_date: str, n: int) -> str:
    count = 0
    next_date = pd.Timestamp(start_date)

    while count < n:
        next_date += pd.Timedelta(days=1)
        next_date_str = next_date.strftime("%Y%m%d")

        if next_date.weekday() >= 5 or next_date in kr_holidays:
            continue

        if stock.get_market_ticker_list(next_date_str):
            count += 1

    return next_date.strftime("%Y%m%d")

# ✅ 1영업일 후 & 4영업일 후 계산
one_bd_later = get_nth_business_day(today, 1)
four_bd_later = get_nth_business_day(today, 4)

# ✅ Seibro 지급 일정 조회 함수
def getCostPaySchedule(pay_term_begin_dt: str, pay_cost_tpcd: list = None, count: int = 100) -> pd.DataFrame:
    url = "http://seibro.or.kr/OpenPlatform/callOpenAPI.jsp"

    pay_cost_tpcd_param = ",".join(map(str, pay_cost_tpcd)) if pay_cost_tpcd else ""
    params = f"TH1_PAY_TERM_BEGIN_DT:{pay_term_begin_dt}"
    if pay_cost_tpcd_param:
        params += f",PAY_COST_TPCD:{pay_cost_tpcd_param}"

    full_url = f"{url}?key={API_KEY}&apiId=getCostPaySchedul&params={params}"
    response = requests.get(full_url)
    xml = BeautifulSoup(response.text, "lxml")

    item_list = []
    results = xml.find_all("result")

    for result in results:
        item_dict = {
            '발행회사고객번호': result.find("issuco_custno")["value"] if result.find("issuco_custno") else "없음",
            '종목번호': result.find("isin")["value"] if result.find("isin") else "없음",
            '한글종목명': result.find("kor_secn_nm")["value"] if result.find("kor_secn_nm") else "없음",
            '종목종류코드': result.find("secn_kacd")["value"] if result.find("secn_kacd") else "없음",
            '권리기준일자': result.find("rgt_std_dt")["value"] if result.find("rgt_std_dt") else "없음",
            '배당구분': result.find("rgt_racd_nm")["value"] if result.find("rgt_racd_nm") else "없음",
            '권리사유세부유형코드': result.find("rgt_rsn_dtail_sort_cd")["value"] if result.find("rgt_rsn_dtail_sort_cd") else "없음"
        }
        item_list.append(item_dict)

    return pd.DataFrame(item_list)

# ✅ 배당 내역 조회
df_1bd = getCostPaySchedule(one_bd_later, [1, 2], 10)
df_4bd = getCostPaySchedule(four_bd_later, [1, 2], 10)

# ✅ 수신자 목록
recipient_list = ["realsheep@kdblife.co.kr", "woori08@kdblife.co.kr", "afterglow3178@gmail.com", "huh1234@kdblife.co.kr"]

# ✅ 이메일 전송 함수 (로그 추가)
def send_email(subject, body, to_emails):
    sender_email = "jinyang7798@gmail.com"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        print("📨 SMTP 서버 연결 시도 중...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, EMAIL_PASSWORD)
            print("✅ SMTP 서버 로그인 성공!")
            server.sendmail(sender_email, to_emails, msg.as_string())
            print("✅ 이메일 전송 성공!")
    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP 인증 오류: 이메일 비밀번호가 올바른지 확인하세요.")
    except smtplib.SMTPException as e:
        print(f"❌ SMTP 오류 발생: {e}")

try:
    print("📨 이메일 전송 시작...")
    email_body = f"""
    <h2>📢 배당 내역 알림</h2>
    <h3>1영업일 후({one_bd_later}) 배당 내역</h3>
    {df_1bd.to_html()}
    <h3>4영업일 후({four_bd_later}) 배당 내역</h3>
    {df_4bd.to_html()}
    """
    send_email("📢 배당 내역 알림", email_body, recipient_list)
except Exception as e:
    print(f"❌ 오류 발생: {e}")  # 👉 **except 블록 추가**

# ✅ Flask 서버 실행 코드 (여기서부터 Flask 코드가 실행됨)
app = Flask(__name__)

@app.route("/")
def home():
    return "Cloud Run is running!"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))  # Cloud Run에서 제공하는 포트 사용
    print(f"✅ Flask 서버 실행 시작! PORT={port}")
    app.run(host="0.0.0.0", port=port)  # Flask 서버 실행
