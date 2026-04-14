import yfinance as yf
import requests
import os
from datetime import datetime
import pytz

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

# 2. AI 분석 함수 (REST API 직접 호출 방식)
def get_ai_analysis(market_data):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key: return "API 키 없음"
    
    # 구글 서버 정식 주소 (v1 정식 버전 타격)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": f"투자 분석가로서 다음 지표를 바탕으로 오늘 전략을 짧게 분석해줘. 기호 없이 텍스트로만 3문장 이내: {market_data}"}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        
        # 결과에서 텍스트만 추출
        if 'candidates' in result:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"분석 실패: {result.get('error', {}).get('message', '알 수 없는 오류')}"
    except Exception as e:
        return f"통신 실패: {str(e)}"

# 3. 메인 실행 로직
def run():
    seoul_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M')
    
    report = f"📊 [마켓 리포트 {now}]\n\n"
    summary = ""
    
    # 데이터 수집
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
