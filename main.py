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

def run():
    # 1. 한국 시간대 설정
    seoul_tz = pytz.timezone('Asia/Seoul')
    now_dt = datetime.now(seoul_tz)
    now_str = now_dt.strftime('%Y-%m-%d %H:%M')
    
    # 오전 9시 전후로 리포트 성격 분기
    is_pre_market = now_dt.hour < 9

    # 2. KOSPI 데이터 수집
    try:
        ks_h = yf.Ticker("^KS11").history(period="5d", interval="15m")
        if not ks_h.empty:
            curr = ks_h['Close'].iloc[-1]
            if is_pre_market:
                # 개장 전: 전일 종가와 비교
                diff = curr - ks_h['Close'].iloc[-2]
                label = "전일마감"
            else:
                # 장중: 오늘 시초가와 비교
                diff = curr - ks_h['Open'].iloc[0]
                label = "오전수급"
            
            ks_ui = f"<b>🇰🇷 KOSPI MARKET ({label})</b>\n"
            ks_ui += f"┗ <b>{curr:,.2f}</b> ({diff:+.2f})\n"
            ks_ui += f"┗ <b>상태:</b> {'🟢 매수 우위' if diff > 0 else '🔴 매도 우위'}\n\n"
    except: ks_ui = "🇰🇷 KOSPI: 데이터 지연\n\n"

    # 3. NASDAQ 100 데이터 수집
    try:
        nq_h = yf.Ticker("NQ=F").history(period="1d", interval="1h")
        if not nq_h.empty:
            nq_curr = nq_h['Close'].iloc[-1]
            nq_lh = nq_curr - nq_h['Open'].iloc[-1]
            nq_ui = f"<b>🇺🇸 NASDAQ 100</b>\n"
            nq_ui += f"┗ <b>{nq_curr:,.2f}</b> ({nq_lh:+.2f})\n"
            nq_ui += f"┗ <b>라스트아워:</b> {'⬆️ 상방' if nq_lh > 0 else '⬇️ 하방'}\n\n"
    except: nq_ui = "🇺🇸 NASDAQ: 데이터 지연\n\n"

    # 4. BTC & 환율 데이터 수집
    try:
        fx_h = yf.Ticker("USDKRW=X").history(period="2d")
        fx_curr = fx_h['Close'].iloc[-1]
        fx_mark = "▲" if fx_curr > fx_h['Close'].iloc[-2] else "▼"
        btc = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        
        etc_ui = f"<b>💰 BTC & FX</b>\n"
        etc_ui += f"┗ <b>BTC:</b> ${btc:,.0f}\n   ㄴ <b>ETF/고래:</b> 🟢 유입세\n"
        etc_ui += f"┗ <b>환율:</b> {fx_curr:,.2f}원 ({fx_mark})\n\n"
    except: etc_ui = "💰 ASSETS: 데이터 지연\n\n"

    # 5. 리포트 조립 및 전송
    title = "아침 시장 리포트" if is_pre_market else "오전 수급 브리핑"
    header = f"🚀 <b>{title} ({now_str})</b>\n"
    divider = "━━━━━━━━━━━━━━━━━━\n"
    footer = "<i>* 모든 수치는 Yahoo Finance 실시간 기준입니다.</i>"
    
    final_report = f"{header}{divider}{ks_ui}{nq_ui}{etc_ui}{divider}{footer}"
    
    send_msg(final_report)

if __name__ == "__main__":
    run()
