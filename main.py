import yfinance as yf
import requests
import os
from datetime import datetime
import pytz
from google import genai  # 최신 라이브러리 방식

# 1. 텔레그램 전송 함수
def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat_id: return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"전송 오류: {e}")

# 2. AI 분석 함수 (최신 google.genai 방식)
def get_ai_analysis(market_data):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key: return "API 키 미설정"
    
    try:
        # 최신 SDK 클라이언트 생성
        client = genai.Client(api_key=api_key)
        
        prompt = f"투자 분석가로서 다음 지표를 바탕으로 오늘 시장 전략을 짧게 분석해줘. 기호 없이 텍스트로만: {market_data}"
        
        # 모델 호출 (v1beta 등의 경로 문제 해결)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        
        return response.text if response.text else "코멘트를 생성할 수 없습니다."
    except Exception as e:
        return f"AI 분석 실패: {str(e)}"

# 3. 메인 실행 로직
def run():
    seoul_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M')
    
    report = f"📊 [마켓 리포트 {now}]\n\n"
    market_summary = ""
    
    # 데이터 수집
    try:
        fx = yf.Ticker("USDKRW=X").history(period="1d")['Close'].iloc[-1]
        report += f"💵 환율: {fx:,.2f}원\n"
        market_summary += f"환율 {fx}원, "
    except: report += "💵 환율: 수집지연\n"

    try:
        nq = yf.Ticker("NQ=F").history(period="1d")['Close'].iloc[-1]
        report += f"🇺🇸 나스닥: {nq:,.2f}\n"
        market_summary += f"나스닥 {nq}, "
    except: report += "🇺🇸 나스닥: 수집지연\n"

    # AI 브리핑 추가
    report += "\n🤖 [AI 비서 브리핑]\n"
    report += get_ai_analysis(market_summary)

    # 최종 전송
    send_msg(report)

if __name__ == "__main__":
    run()
