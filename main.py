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
            nq = yf.Ticker("NQ=F").history(period="1d")
            nq_curr, nq_diff = nq['Close'].iloc[-1], nq['Close'].iloc[-1] - nq['Open'].iloc[0]
            btc = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
            fx = yf.Ticker("USDKRW=X").history(period="1d")['Close'].iloc[-1]

            header = f"🚀 <b>아침 시장 리포트 ({now_str})</b>\n"
            nq_ui = f"<b>🇺🇸 NASDAQ 100 (선물)</b>\n┗ <b>{nq_curr:,.2f}</b> ({nq_diff:+.2f})\n┗ <b>상태:</b> {'⬆️ 상방' if nq_diff > 0 else '⬇️ 하방'}\n\n"
            etc_ui = f"<b>💰 BTC & FX</b>\n┗ <b>BTC:</b> ${btc:,.0f}\n┗ <b>환율:</b> {fx:,.2f}원\n\n"
            msg = f"{header}{divider}{nq_ui}{etc_ui}{divider}<i>* 미장 마감 데이터가 반영되었습니다.</i>"
        except: msg = "아침 데이터 수집 지연"
    else:
        try:
            ks_h = yf.Ticker("^KS11").history(period="1d", interval="15m")
            curr, op = ks_h['Close'].iloc[-1], ks_h['Open'].iloc[0]
            diff = curr - op
            
            header = f"🚀 <b>오전 수급 브리핑 ({now_str})</b>\n"
            ks_ui = f"<b>🇰🇷 KOSPI MARKET (장중)</b>\n┗ <b>{curr:,.2f}</b> ({diff:+.2f})\n┗ <b>수급:</b> {'🟢 매수 우위' if diff > 0 else '🔴 매도 우위'}\n\n"
            msg = f"{header}{divider}{ks_ui}{divider}<i>* 개장 이후 11:30까지의 에너지입니다.</i>"
        except: msg = "오후 수급 데이터 수집 지연"

    send_msg(msg)

if __name__ == "__main__":
    run()
