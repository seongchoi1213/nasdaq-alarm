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
    
    # 오전 10시 이전이면 '아침 리포트', 이후면 '수급 리포트'로 판정
    is_morning = now_dt.hour < 10

    if is_morning:
        # --- [08:00] 전일 미장 마감 및 비트코인 리포트 ---
        try:
            # 나스닥 선물
            nq = yf.Ticker("NQ=F").history(period="1d")
            nq_curr = nq['Close'].iloc[-1]
            nq_diff = nq_curr - nq['Open'].iloc[0]
            
            # 비트코인
            btc = yf.Ticker("BTC-USD").history(period="1d")
            btc_curr = btc['Close'].iloc[-1]
            
            # 환율
            fx = yf.Ticker("USDKRW=X").history(period="1d")
            fx_curr = fx['Close'].iloc[-1]

            msg = f"<b>☀️ 아침 시장 요약 ({now_str})</b>\n"
            msg += "━━━━━━━━━━━━━━━━━━\n"
            msg += f"<b>🇺🇸 나스닥 선물:</b> {nq_curr:,.2f} ({nq_diff:+.2f})\n"
            msg += f"<b>💰 비트코인:</b> ${btc_curr:,.0f}\n"
            msg += f"<b>💵 원/달러 환율:</b> {fx_curr:,.2f}원\n"
            msg += "━━━━━━━━━━━━━━━━━━\n"
            msg += "<i>미장 마감 데이터를 반영했습니다.</i>"
        except Exception as e:
            msg = f"아침 리포트 데이터 수집 중 오류: {e}"
        
    else:
        # --- [11:30] 코스피 장중 수급 에너지 리포트 ---
        try:
            ks_ticker = yf.Ticker("^KS11")
            # 오늘 하루치 15분 단위 데이터 호출
            ks_h = ks_ticker.history(period="1d", interval="15m")
            
            if not ks_h.empty:
                curr = ks_h['Close'].iloc[-1]
                # 시초가(Open[0]) 대비 현재가(Close[-1]) 비교로 수급 방향성 판단
                open_price = ks_h['Open'].iloc[0]
                diff = curr - open_price
                diff_pct = (diff / open_price) * 100
                
                # 시초가 위면 매수세 우위, 아래면 매도세 우위로 해석
                trend = "🟢 외인/기관 매수 우위" if diff > 0 else "🔴 외인/기관 매도 우위"
                
                msg = f"<b>📊 오전 수급 브리핑 ({now_str})</b>\n"
                msg += "━━━━━━━━━━━━━━━━━━\n"
                msg += f"<b>🇰🇷 코스피 현재가:</b> {curr:,.2f}\n"
                msg += f"<b>📈 시초가 대비:</b> {diff:+.2f} ({diff_pct:+.2f}%)\n"
                msg += f"<b>🔥 수급 에너지:</b> {trend}\n"
                msg += "━━━━━━━━━━━━━━━━━━\n"
                msg += "<i>개장부터 11:30까지의 흐름입니다.</i>"
            else:
                msg = "코스피 장중 데이터를 찾을 수 없습니다."
        except Exception as e:
            msg = f"수급 브리핑 생성 중 오류: {e}"

    send_msg(msg)

if __name__ == "__main__":
    run()
