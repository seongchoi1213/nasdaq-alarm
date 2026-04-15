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
    seoul_tz = pytz.timezone('Asia/Seoul')
    now_dt = datetime.now(seoul_tz)
    now_str = now_dt.strftime('%Y-%m-%d %H:%M')
    is_morning = now_dt.hour < 10

    divider = "━━━━━━━━━━━━━━━━━━\n"

    if is_morning:
        try:
            # 1. 국장 전일 데이터
            ks = yf.Ticker("^KS11").history(period="7d")
            ks_curr, ks_diff = ks['Close'].iloc[-1], ks['Close'].iloc[-1] - ks['Close'].iloc[-2]
            
            # 2. 미장/비트/환율 데이터
            nq = yf.Ticker("NQ=F").history(period="2d")
            nq_curr = nq['Close'].iloc[-1]
            nq_diff = nq_curr - nq['Open'].iloc[-1]
            
            btc_h = yf.Ticker("BTC-USD").history(period="2d")
            btc_curr = btc_h['Close'].iloc[-1]
            btc_diff = btc_curr - btc_h['Close'].iloc[-2]
            
            fx_h = yf.Ticker("USDKRW=X").history(period="2d")
            fx_curr = fx_h['Close'].iloc[-1]
            fx_diff = fx_curr - fx_h['Close'].iloc[-2]

            # --- 데이터 분석 (이모지 로직) ---
            # 비트코인 수급 추정 (가격 상승 시 유입세로 판단)
            btc_flow = "🟢 유입 우세" if btc_diff > 0 else "🔴 유출/관망"
            # 환율 변동 이모지
            fx_emoji = "▲" if fx_diff > 0 else "▼"

            header = f"🚀 <b>아침 시장 리포트 ({now_str})</b>\n"
            ks_ui = f"🇰🇷 <b>KOSPI (전일마감)</b>\n┗ <b>{ks_curr:,.2f}</b> ({ks_diff:+.2f})\n┗ <b>상태:</b> {'🔴 매도 우위' if ks_diff < 0 else '🟢 매수 우위'}\n\n"
            nq_ui = f"🇺🇸 <b>NASDAQ 100 (선물)</b>\n┗ <b>{nq_curr:,.2f}</b> ({nq_diff:+.2f})\n┗ <b>라스트아워:</b> {'⬆️ 상방' if nq_diff > 0 else '⬇️ 하방'}\n\n"
            
            # 비트코인 ETF/고래 수급 및 환율 변동 보강
            etc_ui = f"💰 <b>BTC & FX</b>\n┗ <b>BTC:</b> ${btc_curr:,.0f}\n┗ <b>ETF/고래:</b> {btc_flow}\n┗ <b>환율:</b> {fx_curr:,.2f}원 ({fx_emoji})\n\n"
            
            summary = f"<b>☀️ 아침 시장 요약</b>\n┗ 나스닥: {nq_curr:,.2f}\n┗ 비트코인: {btc_flow}\n┗ 환율: {fx_curr:,.2f}원 ({fx_emoji})\n"

            msg = f"{header}{divider}{ks_ui}{nq_ui}{etc_ui}{divider}{summary}{divider}<i>* 모든 데이터는 Yahoo Finance 실시간 기준입니다.</i>"
        except Exception as e:
            msg = f"⚠️ 아침 데이터 수집 지연 ({str(e)})"
        
    else:
        try:
            ks_h = yf.Ticker("^KS11").history(period="1d", interval="15m")
            curr, op = ks_h['Close'].iloc[-1], ks_h['Open'].iloc[0]
            diff = curr - op
            diff_pct = (diff / op) * 100
            
            header = f"🚀 <b>오전 수급 브리핑 ({now_str})</b>\n"
            ks_ui = f"🇰🇷 <b>KOSPI MARKET (장중)</b>\n┗ <b>{curr:,.2f}</b> ({diff:+.2f})\n┗ <b>변동폭:</b> {diff_pct:+.2f}%\n┗ <b>수급 에너지:</b> {'🟢 매수 우위' if diff > 0 else '🔴 매도 우위'}\n\n"
            summary = f"<b>📊 수급 요약</b>\n┗ 현재가: {curr:,.2f}\n┗ 시초가 대비: {diff:+.2f}\n"

            msg = f"{header}{divider}{ks_ui}{divider}{summary}{divider}<i>* 개장 이후 11:30까지의 실시간 흐름입니다.</i>"
        except Exception as e:
            msg = f"⚠️ 오전 데이터 수집 지연 ({str(e)})"

    send_msg(msg)

if __name__ == "__main__":
    run()
