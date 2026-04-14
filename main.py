import yfinance as yf
import requests
import os
from datetime import datetime
import pytz

def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except: pass

def get_ai_analysis(market_data):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key: return "API 키 없음"
    
    # 시도할 모델과 API 버전 리스트
    trials = [
        ("v1", "gemini-1.5-flash"),
        ("v1beta", "gemini-1.5-flash"),
        ("v1", "gemini-pro")
    ]
    
    for version, model in trials:
        url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{"parts": [{"text": f"투자 분석가로서 다음 데이터를 요약해줘: {market_data}"}]}]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            result = response.json()
            if 'candidates' in result:
                return f"({model} 분석) " + result['candidates'][0]['content']['parts'][0]['text']
        except:
            continue
            
    return "❌ 구글 서버의 모든 모델 경로가 응답하지 않습니다."

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
