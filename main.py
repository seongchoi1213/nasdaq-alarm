import yfinance as yf
import requests
import os
from datetime import datetime
import pytz

def get_analysis():
    # 한국 시간 기준 현재 시간 파악
    korea_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(korea_tz)
    
    # 오전 9시 이전이면 미국장 분석, 그 이후면 국장 분석
    if now.hour < 9:
        return analyze_us_market()
    else:
        return analyze_kr_market()

def analyze_us_market():
    nq = yf.Ticker("NQ=F")
    df = nq.history(period="2d", interval="1m")
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    
    last_close = df['Close'].iloc[-1]
    one_hour_ago = df['Close'].iloc[-60]
    reg_change_pct = ((last_close - one_hour_ago) / one_hour_ago) * 100
    
    # 야간 선물 실시간
    current_price = nq.fast_info['last_price']
    overnight_change_pct = ((current_price - last_close) / last_close) * 100

    return (f"🇺🇸 **미국장 마감 심리 보고서**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🔍 **마감 1시간 전 대비:** {reg_change_pct:+.2f}%\n"
            f"🌙 **실시간 야간선물:** {overnight_change_pct:+.2f}%\n"
            f"📉 **공포지수(VIX):** {vix:.2f}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 **한줄평:** " + ("장 막판 매수세 유입, 긍정적" if reg_change_pct > 0.3 else "마감 심리 위축, 주의 요망"))

def analyze_kr_market():
    ks = yf.Ticker("^KS11")
    df = ks.history(period="1d", interval="1m")
    
    if df.empty: return "🇰🇷 국장 데이터 준비 중..."

    start_price = df['Open'].iloc[0]
    current_price = df['Close'].iloc[-1]
    change_pct = ((current_price - start_price) / start_price) * 100

    return (f"🇰🇷 **코스피 개장 1시간 수급 진단**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🌅 시초가 대비: {change_pct:+.2f}%\n"
            f"📍 현재지수: {current_price:,.2f}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 **진단:** " + ("외인/기관 주도 상승세" if change_pct > 0.5 else "방향성 탐색 중"))

def send_msg(text):
    token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_msg(get_analysis())
