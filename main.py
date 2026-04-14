import yfinance as yf
import requests
import os
from datetime import datetime
import pytz
from google import genai
from google.genai import types

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

def get_ai_analysis(market_data):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key: return "API 키 없음"
    
    try:
        # 1. 클라이언트 생성
        client = genai.Client(api_key=api_key)
        
        # 2. 분석 요청 (api_version을 v1으로 강제 지정)
        # 이 부분이 v1beta로 접속해서 생기는 404 에러를 해결하는 핵심입니다.
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"투자 분석가로서 다음 지표를 바탕으로 오늘 전략을 짧게 분석해줘. 기호 없이 텍스트로만: {market_data}",
            config=types.GenerateContentConfig(
                api_version="v1"
            )
        )
        
        if response and response.text:
            return response.text
        return "분석 내용 생성 실패"
        
    except Exception as e:
        return f"AI 분석 최종 실패: {str(e)}"

def run():
    seoul_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M')
    
    report = f"📊 [마켓 리포트 {now}]\n\n"
    summary = ""
    
    try:
        fx = yf.Ticker("USDKRW=X").history(period="1d")['Close'].iloc[-1]
        report += f"💵 환율: {fx:,.2f}원\n"
        summary += f"환율 {fx}원, "
    except: report += "💵 환율: 수집지연\n"

    try:
        nq = yf.Ticker("NQ=F").history(period="1d")['Close'].iloc[-1]
        report += f"🇺🇸 나스닥: {nq:,.2f}\n"
        summary += f"나스닥 {nq}, "
    except: report += "🇺🇸 나스닥: 수집지연\n"

    report += "\n🤖 [AI 비서 브리핑]\n"
    report += get_ai_analysis(summary)

    send_msg(report)

if __name__ == "__main__":
    run()
