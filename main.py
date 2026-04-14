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
            # [수정] 데이터를 넉넉히 7일치 불러와서 마지막 두 거래일을 비교 (에러 방지)
            ks_ticker = yf.Ticker("^KS11")
            ks_h = ks_ticker.history(period="7d")
            ks_curr = ks_h['Close'].iloc[-1]
            ks_diff = ks_curr - ks_h['Close'].iloc[-2]
            
            nq_h = yf.Ticker("NQ=F").history(period="2d")
            nq_curr = nq_h['Close'].iloc[-1]
            nq_diff = nq_curr - nq_h['Open'].iloc[-1]
            
            btc = yf.Ticker("BTC-USD").history(period="2d")['Close'].iloc[-1]
            fx = yf.Ticker("USDKRW=X").history(period="2d")['Close'].iloc[-1]

            header = f"🚀 <b>아침 시장 리포트 ({now_str})</b>\n"
            ks_ui = f"🇰🇷 <b>KOSPI MARKET (전일마감)</b>\n┗ <b>{ks_curr:,.2f}</b> ({ks_diff:+.2f})\n┗ <b>상태:</b> {'🔴 매도 우위' if ks_diff < 0 else '🟢 매수 우위'}\n\n"
            nq_ui = f"🇺🇸 <b>NASDAQ 100 (선물)</b>\n┗ <b>{nq_curr:,.2f}</b> ({nq_diff:+.2f})\n┗ <b>라스트아워:</b> {'⬆️ 상방' if nq_diff > 0 else '⬇️ 하방'}\n\n"
            etc_ui = f"💰 <b>BTC & FX</b>\n┗ <b>BTC:</b> ${btc:,.0f}\n┗ <b>환율:</b> {fx:,.2f}원\n\n"
            
            summary = f"<b>☀️ 아침 시장 요약</b>\n┗ 나스닥 선물: {nq_curr:,.2f} ({nq_diff:+.2f})\n┗ 비트코인: ${btc:,.0f}\n┗ 환율: {fx:,.2f}원\n"

            msg = f"{header}{divider}{ks_ui}{nq_ui}{etc_ui}{divider}{summary}{divider}<i>* 모든 수치는 Yahoo Finance 기준입니다.</i>"
        except Exception as e:
            # [디버깅용] 에러가 나면 어떤 데이터에서 났는지 텔레그램으로 알려줍니다.
            msg = f"⚠️ 아침 데이터 수집 지연\n(사유: {str(e)})"
        
    else:
        try:
            ks_h = yf.Ticker("^KS11").history(period="1d", interval="15m")
            if not ks_h.empty:
                curr, op = ks_h['Close'].iloc[-1], ks_h['Open'].iloc[0]
                diff = curr - op
                diff_pct = (diff / op) * 100
                
                header = f"🚀 <b>오전 수급 브리핑 ({now_str})</b>\n"
                ks_ui = f"🇰🇷 <b>KOSPI MARKET (장중)</b>\n┗ <b>{curr:,.2f}</b> ({diff:+.2f})\n┗ <b>변동폭:</b> {diff_pct:+.2f}%\n┗ <b>수급 에너지:</b> {'🟢 매수 우위' if diff > 0 else '🔴 매도 우위'}\n\n"
                summary = f"<b>📊 수급 요약</b>\n┗ 현재가: {curr:,.2f}\n┗ 시초가 대비: {diff:+.2f}\n"
                msg = f"{header}{divider}{ks_ui}{divider}{summary}{divider}<i>* 장중 수급 지표입니다.</i>"
            else:
                msg = "현재 장중 데이터를 가져올 수 없습니다."
        except Exception as e:
            msg = f"⚠️ 오전 수급 데이터 수집 지연\n(사유: {str(e)})"

    send_msg(msg)

if __name__ == "__main__":
    run()
