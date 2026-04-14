import yfinance as yf
import requests
import os
from datetime import datetime
import pytz
import google.generativeai as genai
from google.generativeai.types import RequestOptions

# 1. 텔레그램 전송 함수 (마크다운 옵션 제거하여 안정성 확보)
def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        print("❌ 환경변수(Token/ID)가 없습니다.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # parse_mode를 제거하여 특수문자로 인한 전송 실패를 원천 봉쇄합니다.
    payload = {
        "chat_id": chat_id, 
        "text": text
    }
    
    try:
        res = requests.post(url, json=payload)
        print(f"📡 전송 시도 결과: {res.status_code}")
        if res.status_code != 200:
            print(f"❌ 전송 실패 사유: {res.text}")
    except Exception as e:
        print(f"❌ 네트워크 오류: {e}")

# 2. AI 분석 함수
def get_ai_analysis(market_data):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key: return "API 키 미설정"
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        # AI에게 특수문자를 쓰지 말라고 명시합니다.
        prompt = f"금융분석가로서 다음 데이터를 요약해줘. 별표(*)나 언더바(_) 같은 기호는 절대 쓰지 말고 텍스트로만 대답해줘: {market_data}"
        
        response = model.generate_content(
            prompt,
            request_options=RequestOptions(api_version='v1')
        )
        return response.text if response.text else "코멘트 생성 실패"
    except Exception as e:
        return f"AI 분석 오류: {str(e)}"

# 3. 메인 실행 로직
def run():
    seoul_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M')
    
    report = f"📊 [마켓 리포트 {now}]\n\n"
    market_data = ""
    
    # 환율 수집
    try:
        fx = yf.Ticker("USDKRW=X").history(period="1d")['Close'].iloc[-1]
        report += f"💵 환율: {fx:,.2f}원\n"
        market_data += f"환율 {fx}, "
    except: report += "💵 환율: 수신 실패\n"

    # 나스닥 수집
    try:
        nq = yf.Ticker("NQ=F").history(period="1d", interval="5m")['Close'].iloc[-1]
        report += f"🇺🇸 나스닥: {nq:,.2f}\n"
        market_data += f"나스닥 {nq}, "
    except: report += "🇺🇸 나스닥: 수신 실패\n"

    # AI 브리핑 추가
    report += "\n🤖 [AI 비서 브리핑]\n"
    report += get_ai_analysis(market_data)

    # 최종 전송
    send_msg(report)

if __name__ == "__main__":
    run()
