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
    # HTML 파싱 모드를 활성화하여 굵게(b), 줄바꿈 등을 적용합니다.
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except: pass

def get_ai_analysis(market_data):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key: return "API 키 없음"
    
    # 서버 상황에 맞는 모델 자동 탐색
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        models_resp = requests.get(list_url).json()
        available_models = [m['name'] for m in models_resp.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
    except:
        available_models = ["models/gemini-1.5-flash"]

    for model_path in available_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent?key={api_key}"
        # 사용자 요청 반영: 환율은 기준점으로만 사용, 수급 중심의 2-3문장 요약
        prompt = f"""
        당신은 냉철한 투자 비서입니다. 다음 데이터를 2~3문장으로 분석하세요.
        - 환율 1,450원을 '뉴노멀' 기준선으로 잡고 현재 시장의 유리/불리만 짧게 언급할 것.
        - 코스피와 나스닥의 가격 흐름을 통해 '수급 에너지'가 어디로 쏠리는지 분석할 것.
        - 군더더기 없는 결과 중심의 문체로 작성할 것.
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
    FX_BASE = 1450.0 # 뉴노멀 기준 환율

    # 1. KOSPI 섹션
    try:
        ks_t = yf.Ticker("^KS11")
        ks_h = ks_t.history(period="1d", interval="15m")
        ks_curr = ks_h['Close'].iloc[-1]
        ks_diff = ks_curr - ks_h['Open'].iloc[0]
        ks_ui = f"<b>🇰🇷 KOSPI MARKET</b>\n"
        ks_ui += f"┗ <b>{ks_curr:,.2f}</b> ({ks_diff:+.2f})\n"
        ks_ui += f"┗ <b>수급:</b> {'🟢 매수세' if ks_diff > 0 else '🔴 매도세'}\n"
        summary_ai += f"코스피 {ks_curr}(전일비 {ks_diff:+.2f}), "
    except: ks_ui = "🇰🇷 KOSPI: 지연\n"

    # 2. NASDAQ 섹션
    try:
        nq_t = yf.Ticker("NQ=F")
        nq_h = nq_t.history(period="1d", interval="1h")
        nq_curr = nq_h['Close'].iloc[-1]
        nq_lh = nq_curr - nq_h['Open'].iloc[-1]
        nq_ui = f"<b>🇺🇸 NASDAQ 100</b>\n"
        nq_ui += f"┗ <b>{nq_curr:,.2f}</b> ({nq_lh:+.2f})\n"
        nq_ui += f"┗ <b>마감직전:</b> {'⬆️ 상방' if nq_lh > 0 else '⬇️ 하방'}\n"
        summary_ai += f"나스닥 {nq_curr}(라스트아워 {nq_lh:+.2f}), "
    except: nq_ui = "🇺🇸 NASDAQ: 지연\n"

    # 3. FX & BTC 섹션
    try:
        fx = yf.Ticker("USDKRW=X").history(period="1d")['Close'].iloc[-1]
        btc = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        fx_dir = "▲" if fx > FX_BASE else "▼"
        etc_ui = f"<b>💰 FX & BTC</b>\n"
        etc_ui += f"┗ <b>환율:</b> {fx:,.2f}원 ({fx_dir} {FX_BASE})\n"
        etc_ui += f"┗ <b>BTC:</b> ${btc:,.0f}\n"
        summary_ai += f"환율 {fx}원(뉴노멀 {FX_BASE}), 비트코인 {btc:,.0f}달러."
    except: etc_ui = ""

    # 리포트 조립
    header = f"🚀 <b>시장이 어찌 굴러가나 ({now})</b>\n"
    divider = "━━━━━━━━━━━━━━━━━━\n"
    ai_brief = get_ai_analysis(summary_ai)
    
    final_report = f"{header}{divider}{ks_ui}\n{nq_ui}\n{etc_ui}{divider}<b>🤖 AI 비서 브리핑</b>\n{ai_brief}"
    
    send_msg(final_report)

if __name__ == "__main__":
    run()
