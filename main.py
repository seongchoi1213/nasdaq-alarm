import yfinance as yf
import requests
import os
from datetime import datetime, timedelta
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
    
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        models_resp = requests.get(list_url).json()
        available_models = [m['name'] for m in models_resp.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
    except:
        available_models = ["models/gemini-1.5-flash"]

    for model_path in available_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"전문 투자 분석가로서 다음 시장 흐름(특히 나스닥의 장중 변동성과 폐장 직전 수급)을 분석해줘. 기호 없이 3-4문장: {market_data}"}]}]
        }
        try:
            response = requests.post(url, json=payload)
            result = response.json()
            if 'candidates' in result:
                return result['candidates'][0]['content']['parts'][0]['text']
        except: continue
    return "AI 분석 실패"

def run():
    seoul_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M')
    
    report = f"📊 [마켓 리포트 {now}]\n\n"
    summary_for_ai = ""
    
    # 1. 나스닥 상세 분석 (변동성 및 폐장 전 수급)
    try:
        nq_ticker = yf.Ticker("NQ=F")
        nq_hist = nq_ticker.history(period="2d", interval="1h") # 최근 2일치 1시간 단위 데이터
        
        if len(nq_hist) >= 2:
            current_price = nq_hist['Close'].iloc[-1]
            prev_close = nq_hist['Close'].iloc[-2]
            day_high = nq_hist['High'].max()
            day_low = nq_hist['Low'].min()
            
            # 폐장 전 마지막 1시간 변화 계산 (수급 파악용)
            last_hour_change = current_price - nq_hist['Open'].iloc[-1]
            last_hour_text = "매수 우위" if last_hour_change > 0 else "매도 우위"
            
            report += f"🇺🇸 나스닥: {current_price:,.2f} (변동: {day_low:,.0f} ~ {day_high:,.0f})\n"
            report += f"   ㄴ 폐장 1시간 수급: {last_hour_text} ({last_hour_change:+.2f})\n"
            summary_for_ai += f"나스닥 현재가 {current_price}, 당일 고점 {day_high}, 저점 {day_low}, 폐장전 1시간 변화 {last_hour_change}. "
    except: report += "🇺🇸 나스닥: 데이터 분석 지연\n"

    # 2. 비트코인
    try:
        btc = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        report += f"🐳 비트코인: ${btc:,.0f}\n"
        summary_for_ai += f"비트코인 {btc:.0f}달러, "
    except: report += "🐳 비트코인: 수집지연\n"

    # 3. 환율 및 코스피
    try:
        fx = yf.Ticker("USDKRW=X").history(period="1d")['Close'].iloc[-1]
        ks = yf.Ticker("^KS11").history(period="1d")['Close'].iloc[-1]
        report += f"💵 환율: {fx:,.2f}원 / 🇰🇷 코스피: {ks:,.2f}\n"
        summary_for_ai += f"환율 {fx}원, 코스피 {ks}포인트"
    except: pass

    report += "\n🤖 [AI 비서 브리핑]\n"
    report += get_ai_analysis(summary_for_ai)

    send_msg(report)

if __name__ == "__main__":
    run()
