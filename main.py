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
    
    # 1. 사용 가능한 모델 리스트 먼저 조회
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        models_resp = requests.get(list_url).json()
        # 사용 가능한 모델 중 'generateContent'를 지원하는 첫 번째 모델 찾기
        available_models = [m['name'] for m in models_resp.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
        print(f"✅ 사용 가능 모델: {available_models}")
    except:
        available_models = ["models/gemini-1.5-flash", "models/gemini-pro"]

    # 2. 리스트에 있는 모델 순서대로 시도
    for model_path in available_models:
        # 모델 경로가 이미 'models/'를 포함하고 있으므로 그대로 사용
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{"parts": [{"text": f"투자 분석가로서 다음 데이터를 3문장 이내로 요약해줘: {market_data}"}]}]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            result = response.json()
            if 'candidates' in result:
                return f"({model_path.split('/')[-1]} 분석) " + result['candidates'][0]['content']['parts'][0]['text']
        except:
            continue
            
    return f"❌ 지원 모델 없음. 서버응답: {models_resp.get('error', {}).get('message', '알 수 없는 상태')}"

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
