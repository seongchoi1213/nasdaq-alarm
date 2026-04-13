import yfinance as yf
import requests
import os
from datetime import datetime
import pytz

def get_analysis():
    korea_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(korea_tz)
    
    if now.hour < 9:
        return analyze_us_market()
    else:
        return analyze_kr_market()

def get_btc_whale_movements():
    """
    나스닥 거래 시간 내 비트코인 대량 매물대 및 고래 움직임 추정
    (실제 온체인 API 대신 거래량 가중 평균 가격 편차를 이용한 수급 분석)
    """
    btc = yf.Ticker("BTC-USD")
    # 나스닥 정규장 시간(미국 기준 09:30 ~ 16:00) 동안의 5분봉 데이터 분석
    df_btc = btc.history(period="1d", interval="5m")
    
    if len(df_btc) < 10: return "데이터 집계 중"

    # 거래량이 평균 대비 3배 이상 터진 지점을 '고래 활동'으로 정의
    avg_vol = df_btc['Volume'].mean()
    whale_activity = df_btc[df_btc['Volume'] > avg_vol * 3]
    
    buy_count = len(whale_activity[whale_activity['Close'] > whale_activity['Open']])
    sell_count = len(whale_activity[whale_activity['Close'] < whale_activity['Open']])
    
    return f"🐳 **고래 활동(대량 거래):** 매수 {buy_count}회 / 매도 {sell_count}회"

def analyze_us_market():
    nq = yf.Ticker("NQ=F")
    df = nq.history(period="2d", interval="1m")
    
    last_close = df['Close'].iloc[-1]
    one_hour_ago = df['Close'].iloc[-60]
    reg_change_pct = ((last_close - one_hour_ago) / one_hour_ago) * 100
    
    # 비트코인 수급 분석 추가
    btc_whale = get_btc_whale_movements()

    return (f"🇺🇸 **미국장 마감 & 코인 수급 보고**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🔍 **나스닥 마감 심리:** {reg_change_pct:+.2f}%\n"
            f"{btc_whale}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 **종합 판단:** " + 
            ("고래 매수세 동반, 위험자산 선호" if reg_change_pct > 0 and "매수" in btc_whale else "신중한 접근 필요"))

def analyze_kr_market():
    # (기존 코스피 분석 로직과 동일)
    ks = yf.Ticker("^KS11")
    df = ks.history(period="1d", interval="1m")
    if df.empty: return "🇰🇷 국장 데이터 휴장"
    change_pct = ((df['Close'].iloc[-1] - df['Open'].iloc[0]) / df['Open'].iloc[0]) * 100
    
    return (f"🇰🇷 **코스피 수급 진단**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📍 시초가 대비: {change_pct:+.2f}%\n"
            f"💡 판단: " + ("외인 주도 상승" if change_pct > 0.5 else "관망세"))

def send_msg(text):
    token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_msg(get_analysis())
