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
        requests.post(url, json=payload, timeout=10)
    except: pass

def get_ai_analysis(market_data, is_pre_market):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key: return "API 키 설정 확인 필요"
    
    # [핵심 변경] v1beta와 models/gemini-1.5-flash 풀네임 조합
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt = f"전문 투자 분석가로서 다음 주식 데이터를 1~2문장으로 냉철하게 요약하세요(환율/비트코인 언급 금지): {market_data}"

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        # 헤더에 Content-Type 명시하여 더 엄격하게 호출
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        res_json = response.json()
        
        if 'candidates' in res_json and len(res_json['candidates']) > 0:
            return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            # 실패 시 상세 에러를 텔레그램으로 쏴서 끝까지 추적합니다.
            err_msg = res_json.get('error', {}).get('message', 'Unknown Structure')
            return f"AI 분석 지연 (사유: {err_msg})"
    except Exception as e:
        return f"연결 오류 ({str(e)})"

def run():
    seoul_tz = pytz.timezone('Asia/Seoul')
    now_dt = datetime.now(seoul_tz)
    now_str = now_dt.strftime('%Y-%m-%d %H:%M')
    
    is_pre_market = now_dt.hour < 9
    summary_ai = ""

    # 1. KOSPI
    try:
        ks_h = yf.Ticker("^KS11").history(period="5d", interval="15m")
        curr = ks_h['Close'].iloc[-1]
        diff = curr - (ks_h['Close'].iloc[-2] if is_pre_market else ks_h['Open'].iloc[0])
        label = "전일마감" if is_pre_market else "오전수급"
        ks_ui = f"<b>🇰🇷 KOSPI MARKET ({label})</b>\n┗ <b>{curr:,.2f}</b> ({diff:+.2f})\n┗ <b>상태:</b> {'🟢 매수 우위' if diff > 0 else '🔴 매도 우위'}\n\n"
        summary_ai += f"코스피 {curr}({diff:+.2f}), "
    except: ks_ui = "🇰🇷 KOSPI: 지연\n\n"

    # 2. NASDAQ
    try:
        nq_h = yf.Ticker("NQ=F").history(period="1d", interval="1h")
        nq_curr = nq_h['Close'].iloc[-1]
        nq_lh = nq_curr - nq_h['Open'].iloc[-1]
        nq_ui = f"<b>🇺🇸 NASDAQ 100</b>\n┗ <b>{nq_curr:,.2f}</b> ({nq_lh:+.2f})\n┗ <b>라스트아워:</b> {'⬆️ 상방' if nq_lh > 0 else '⬇️ 하방'}\n\n"
        summary_ai += f"나스닥 {nq_curr}(라스트 {nq_lh:+.2f}), "
    except: nq_ui = "🇺🇸 NASDAQ: 지연\n\n"

    # 3. BTC & FX
    try:
        fx_h = yf.Ticker("USDKRW=X").history(period="2d")
        fx_curr = fx_h['Close'].iloc[-1]
        fx_mark = "▲" if fx_curr > fx_h['Close'].iloc[-2] else "▼"
        btc = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        etc_ui = f"<b>💰 BTC & FX</b>\n┗ <b>BTC:</b> ${btc:,.0f}\n   ㄴ <b>ETF/고래:</b> 🟢 유입세\n┗ <b>환율:</b> {fx_curr:,.2f}원 ({fx_mark})\n\n"
    except: etc_ui = "💰 ASSETS: 지연\n\n"

    ai_brief = get_ai_analysis(summary_ai, is_pre_market)
    
    header = f"🚀 <b>{'아침 시장 리포트' if is_pre_market else '오전 수급 브리핑'} ({now_str})</b>\n"
    divider = "━━━━━━━━━━━━━━━━━━\n"
    final_report = f"{header}{divider}{ks_ui}{nq_ui}{etc_ui}{divider}<b>🤖 AI 비서 브리핑</b>\n{ai_brief}"
    
    send_msg(final_report)

if __name__ == "__main__":
    run()
