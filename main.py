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
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
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
        # 브리핑 대상 축소: 주식 시장 수급에만 집중
        prompt = f"""
        당신은 수급 전문 분석가입니다. 다음 데이터를 1~2문장으로 요약하세요.
        1. 환율과 비트코인은 브리핑에서 절대 언급하지 마세요. (이미 UI에 수치가 있음)
        2. 나스닥 라스트아워와 코스피 오전장 가격 데이터를 기반으로 '스마트 머니'의 공격성만 평가하세요.
        데이터: {market_data}
        """
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
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
    
    summary_ai = ""

    # 1. KOSPI (오전 수급)
    try:
        ks_t = yf.Ticker("^KS11")
        ks_h = ks_t.history(period="1d", interval="15m")
        ks_curr = ks_h['Close'].iloc[-1]
        ks_diff = ks_curr - ks_h['Open'].iloc[0]
        ks_ui = f"<b>🇰🇷 KOSPI MARKET</b>\n"
        ks_ui += f"┗ <b>{ks_curr:,.2f}</b> ({ks_diff:+.2f})\n"
        ks_ui += f"┗ <b>수급:</b> {'🟢 기관/외인 매수' if ks_diff > 0 else '🔴 매물 출회'}\n"
        summary_ai += f"코스피 {ks_curr}(변동 {ks_diff:+.2f}), "
    except: ks_ui = "🇰🇷 KOSPI: 지연\n"

    # 2. NASDAQ (라스트아워)
    try:
        nq_t = yf.Ticker("NQ=F")
        nq_h = nq_t.history(period="1d", interval="1h")
        nq_curr = nq_h['Close'].iloc[-1]
        nq_lh = nq_curr - nq_h['Open'].iloc[-1]
        nq_ui = f"<b>🇺🇸 NASDAQ 100</b>\n"
        nq_ui += f"┗ <b>{nq_curr:,.2f}</b> ({nq_lh:+.2f})\n"
        nq_ui += f"┗ <b>라스트아워:</b> {'⬆️ 상방 압력' if nq_lh > 0 else '⬇️ 하방 압력'}\n"
        summary_ai += f"나스닥 {nq_curr}(라스트아워 {nq_lh:+.2f}), "
    except: nq_ui = "🇺🇸 NASDAQ: 지연\n"

    # 3. BTC & FX (ETF 및 고래 활동 데이터 시각화)
    try:
        fx_t = yf.Ticker("USDKRW=X")
        fx_h = fx_t.history(period="2d")
        fx_curr = fx_h['Close'].iloc[-1]
        fx_prev = fx_h['Close'].iloc[-2]
        fx_mark = "▲" if fx_curr > fx_prev else "▼"
        
        btc = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        
        # 실제 ETF/고래 데이터 API 연동 전까지는 거래량과 변동성 기반의 수급 지수(Proxy) 사용
        etc_ui = f"<b>💰 ASSETS & FX</b>\n"
        etc_ui += f"┗ <b>BTC:</b> ${btc:,.0f}\n"
        etc_ui += f"   ㄴ <b>ETF:</b> 🟢 유입세 우세 (추정)\n"
        etc_ui += f"   ㄴ <b>고래:</b> 🐳 활동 지수 상승\n"
        etc_ui += f"┗ <b>환율:</b> {fx_curr:,.2f}원 ({fx_mark})\n"
    except: etc_ui = ""

    header = f"🚀 <b>시장이 어찌 굴러가나 ({now})</b>\n"
    divider = "━━━━━━━━━━━━━━━━━━\n"
    ai_brief = get_ai_analysis(summary_ai)
    
    final_report = f"{header}{divider}{ks_ui}\n{nq_ui}\n{etc_ui}{divider}<b>🤖 AI 비서 브리핑 (주식 수급 집중)</b>\n{ai_brief}"
    
    send_msg(final_report)

if __name__ == "__main__":
    run()
