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
        # 환율 뉴노멀 1450원 기준을 프롬프트에 주입
        prompt = f"""
        전문 투자 분석가로서 다음 데이터를 분석해줘.
        1. 환율 뉴노멀 기준점은 1,450원이야. 현재 환율이 이 대비 어떤 리스크가 있는지 언급해줘.
        2. 코스피와 나스닥의 가격 흐름을 통해 세력 수급 강도를 평가해줘.
        3. 3문장 이내로 아주 날카롭게 요약해줘.
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
    NEW_NORMAL_FX = 1450.0 # 사용자 설정 뉴 노멀 환율

    # 1. 코스피 (오전 수급 및 변동성)
    try:
        ks_t = yf.Ticker("^KS11")
        ks_h = ks_t.history(period="1d", interval="15m")
        ks_curr = ks_h['Close'].iloc[-1]
        ks_open = ks_h['Open'].iloc[0]
        ks_diff = ks_curr - ks_open
        ks_low, ks_high = ks_h['Low'].min(), ks_h['High'].max()
        
        ks_ui = f"<b>🇰🇷 KOSPI MARKET</b>\n"
        ks_ui += f"┗ <b>지수:</b> {ks_curr:,.2f} ({ks_diff:+.2f})\n"
        ks_ui += f"┗ <b>범위:</b> {ks_low:,.0f} ~ {ks_high:,.0f}\n"
        ks_ui += f"┗ <b>수급:</b> {'🟢 기관/외인 매수추정' if ks_diff > 0 else '🔴 매물 소화 중'}\n"
        summary_ai += f"코스피 {ks_curr}(시초대비 {ks_diff:+.2f}), 고점 {ks_high}, 저점 {ks_low}. "
    except: ks_ui = "🇰🇷 KOSPI: 데이터 분석 지연\n"

    # 2. 나스닥 (라스트아워 및 변동성)
    try:
        nq_t = yf.Ticker("NQ=F")
        nq_h = nq_t.history(period="1d", interval="1h")
        nq_curr = nq_h['Close'].iloc[-1]
        nq_low, nq_high = nq_h['Low'].min(), nq_h['High'].max()
        nq_last_hour = nq_curr - nq_h['Open'].iloc[-1]
        
        nq_ui = f"<b>🇺🇸 NASDAQ 100</b>\n"
        nq_ui += f"┗ <b>지수:</b> {nq_curr:,.2f}\n"
        nq_ui += f"┗ <b>라스트아워:</b> {'⬆️ 상방압력' if nq_last_hour > 0 else '⬇️ 하방압력'} ({nq_last_hour:+.2f})\n"
        summary_ai += f"나스닥 {nq_curr}, 변동폭 {nq_low}~{nq_high}, 폐장직전 {nq_last_hour:+.2f}. "
    except: nq_ui = "🇺🇸 NASDAQ: 데이터 분석 지연\n"

    # 3. 기타 자산 및 환율 (뉴 노멀 비교)
    try:
        btc = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        fx = yf.Ticker("USDKRW=X").history(period="1d")['Close'].iloc[-1]
        fx_status = "⚠️ 주의" if fx > NEW_NORMAL_FX else "✅ 안정"
        
        etc_ui = f"<b>💰 ASSETS & FX (Target: {NEW_NORMAL_FX:,.0f})</b>\n"
        etc_ui += f"┗ <b>환율:</b> {fx:,.2f}원 ({fx_status})\n"
        etc_ui += f"┗ <b>BTC:</b> ${btc:,.0f}\n"
        summary_ai += f"현재 환율 {fx}원(뉴노멀 기준 1450원 대비 평가 필요), 비트코인 {btc:,.0f}달러."
    except: etc_ui = ""

    # 리포트 조립
    header = f"🚀 <b>시장이 어찌 굴러가나 ({now})</b>\n"
    divider = "━━━━━━━━━━━━━━━━━━\n"
    ai_brief = get_ai_analysis(summary_ai)
    
    final_report = f"{header}{divider}{ks_ui}\n{nq_ui}\n{etc_ui}{divider}<b>🤖 AI 비서 브리핑</b>\n{ai_brief}"
    
    send_msg(final_report)

if __name__ == "__main__":
    run()
