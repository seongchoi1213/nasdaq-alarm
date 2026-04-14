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
    if not api_key: return "API 키 없음"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # 시간대에 따른 프롬프트 분기
    if is_pre_market:
        context = "현재는 코스피 개장 전입니다. 전일 마감된 수급 데이터를 바탕으로 시장의 분위기만 짧게 요약하세요."
    else:
        context = "현재는 코스피 오전장 진행 중입니다. 오늘 아침 시초가 대비 수급 에너지를 분석하세요."

    prompt = f"""
    당신은 수급 분석 전문가입니다. {context}
    1. 환율과 비트코인은 브리핑에서 절대 언급 금지.
    2. 나스닥 라스트아워와 코스피의 수급 흐름만 1~2문장으로 냉철하게 분석하세요.
    데이터: {market_data}
    """
    try:
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except: return "수급 분석 지연"

def run():
    seoul_tz = pytz.timezone('Asia/Seoul')
    now_dt = datetime.now(seoul_tz)
    now_str = now_dt.strftime('%Y-%m-%d %H:%M')
    
    # 개장 전(09:00 이전) 여부 판단
    is_pre_market = now_dt.hour < 9
    
    summary_ai = ""

    # 1. KOSPI 섹션
    try:
        ks_ticker = yf.Ticker("^KS11")
        ks_h = ks_ticker.history(period="2d", interval="15m")
        if not ks_h.empty:
            curr = ks_h['Close'].iloc[-1]
            if is_pre_market:
                # 개장 전에는 전일 등락폭 기준
                prev_close = ks_h['Close'].iloc[-2]
                diff = curr - prev_close
                label = "전일마감"
            else:
                # 개장 후에는 당일 시초가 대비 기준
                diff = curr - ks_h['Open'].iloc[0]
                label = "오전수급"
            
            ks_ui = f"<b>🇰🇷 KOSPI MARKET ({label})</b>\n"
            ks_ui += f"┗ <b>{curr:,.2f}</b> ({diff:+.2f})\n"
            ks_ui += f"┗ <b>상태:</b> {'🟢 매수 우위' if diff > 0 else '🔴 매도 우위'}\n\n"
            summary_ai += f"코스피 {curr}({label} 변동 {diff:+.2f}), "
    except: ks_ui = "🇰🇷 KOSPI: 지연\n\n"

    # 2. NASDAQ 섹션 (라스트아워는 항상 최신 미장 마감 데이터)
    try:
        nq_h = yf.Ticker("NQ=F").history(period="1d", interval="1h")
        if not nq_h.empty:
            curr = nq_h['Close'].iloc[-1]
            lh = curr - nq_h['Open'].iloc[-1]
            nq_ui = f"<b>🇺🇸 NASDAQ 100</b>\n"
            nq_ui += f"┗ <b>{curr:,.2f}</b> ({lh:+.2f})\n"
            nq_ui += f"┗ <b>라스트아워:</b> {'⬆️ 상방' if lh > 0 else '⬇️ 하방'}\n\n"
            summary_ai += f"나스닥 {curr}(라스트 {lh:+.2f}), "
    except: nq_ui = "🇺🇸 NASDAQ: 지연\n\n"

    # 3. BTC & FX (환율 등락만)
    try:
        fx_h = yf.Ticker("USDKRW=X").history(period="2d")
        fx_curr = fx_h['Close'].iloc[-1]
        fx_mark = "▲" if fx_curr > fx_h['Close'].iloc[-2] else "▼"
        btc = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        etc_ui = f"<b>💰 BTC & FX</b>\n"
        etc_ui += f"┗ <b>BTC:</b> ${btc:,.0f}\n   ㄴ <b>ETF/고래:</b> 🟢 유입세\n"
        etc_ui += f"┗ <b>환율:</b> {fx_curr:,.2f}원 ({fx_mark})\n\n"
    except: etc_ui = "💰 ASSETS: 지연\n\n"

    divider = "━━━━━━━━━━━━━━━━━━\n"
    ai_brief = get_ai_analysis(summary_ai, is_pre_market)
    
    title = "아침 시장 리포트" if is_pre_market else "오전 수급 브리핑"
    header = f"🚀 <b>{title} ({now_str})</b>\n"
    
    final_report = f"{header}{divider}{ks_ui}{nq_ui}{etc_ui}{divider}<b>🤖 AI 비서 브리핑</b>\n{ai_brief}"
    send_msg(final_report)

if __name__ == "__main__":
    run()
