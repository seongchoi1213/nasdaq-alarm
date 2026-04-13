import yfinance as yf
import requests
import os
from datetime import datetime
import pytz

def get_combined_analysis():
    # 1. 나스닥 선물 & VIX (미국장 심리)
    nq = yf.Ticker("NQ=F")
    df_nq = nq.history(period="2d", interval="1m")
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    
    nq_last = df_nq['Close'].iloc[-1]
    nq_one_hour_ago = df_nq['Close'].iloc[-60]
    nq_change_pct = ((nq_last - nq_one_hour_ago) / nq_one_hour_ago) * 100

    # 2. 비트코인 고래 분석 (최근 24시간 중 거래량 급증 구간 추출)
    btc = yf.Ticker("BTC-USD")
    df_btc = btc.history(period="1d", interval="5m")
    avg_vol = df_btc['Volume'].mean()
    whale_activity = df_btc[df_btc['Volume'] > avg_vol * 3] # 평균 거래량 3배 이상
    btc_buy = len(whale_activity[whale_activity['Close'] > whale_activity['Open']])
    btc_sell = len(whale_activity[whale_activity['Close'] < whale_activity['Open']])

    # 3. 코스피 분석 (전일 종가 및 시초가 대비 변동)
    ks = yf.Ticker("^KS11")
    df_ks = ks.history(period="2d")
    ks_last = df_ks['Close'].iloc[-1]
    ks_prev = df_ks['Close'].iloc[-2]
    ks_change_pct = ((ks_last - ks_prev) / ks_prev) * 100

    # 메시지 구성
    msg = (
        f"🚀 **오늘의 시장 통합 보고서**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🇺🇸 **나스닥 마감 심리**\n"
        f" - 마감 1시간 변동: {nq_change_pct:+.2f}%\n"
        f" - 공포지수(VIX): {vix:.2f}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🐳 **비트코인 고래 움직임**\n"
        f" - 대량 매수: {btc_buy}회 / 매도: {btc_sell}회\n"
        f" - 판단: {'매수 우위' if btc_buy > btc_sell else '매도 우위'}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🇰🇷 **코스피 전일 현황**\n"
        f" - 종가: {ks_last:,.2f} ({ks_change_pct:+.2f}%)\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💡 **종합 판단:** "
    )

    if nq_change_pct > 0.3 and btc_buy > btc_sell:
        msg += "미국장 마감 심리와 코인 수급이 모두 좋습니다. 불장이 예상됩니다!"
    elif nq_change_pct < -0.3:
        msg += "미국장 마감 심리가 불안합니다. 국장 개장 후 보수적 대응이 필요합니다."
    else:
        msg += "혼조세입니다. 장 초반 외국인 수급을 확인하며 대응하세요."

    return msg

def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_msg(get_combined_analysis())
