import yfinance as yf
import requests
import os
from datetime import datetime
import pytz

def get_combined_analysis():
    # 1. 미국 나스닥 & VIX 분석
    nq = yf.Ticker("NQ=F")
    df_nq = nq.history(period="2d", interval="1m")
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    
    # 마감 1시간 변동성 계산
    nq_last = df_nq['Close'].iloc[-1]
    nq_one_hour_ago = df_nq['Close'].iloc[-60]
    nq_change_pct = ((nq_last - nq_one_hour_ago) / nq_one_hour_ago) * 100

    # 2. 비트코인 고래 분석 (최근 24시간 거래량 기준)
    btc = yf.Ticker("BTC-USD")
    df_btc = btc.history(period="1d", interval="5m")
    avg_vol = df_btc['Volume'].mean()
    whale_activity = df_btc[df_btc['Volume'] > avg_vol * 3]
    btc_buy = len(whale_activity[whale_activity['Close'] > whale_activity['Open']])
    btc_sell = len(whale_activity[whale_activity['Close'] < whale_activity['Open']])

    # 3. 코스피 수급 분석
    ks = yf.Ticker("^KS11")
    df_ks = ks.history(period="1d", interval="1m")
    
    if not df_ks.empty:
        ks_start = df_ks['Open'].iloc[0]
        ks_current = df_ks['Close'].iloc[-1]
        ks_change_pct = ((ks_current - ks_start) / ks_start) * 100
        ks_info = f"{ks_current:,.2f} (시초가 대비 {ks_change_pct:+.2f}%)"
    else:
        ks_info = "데이터 집계 중 또는 휴장"

    # 메시지 조립 (모든 정보 포함)
    msg = (
        f"🚀 **글로벌 시장 통합 모니터링**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🇺🇸 **미국 나스닥 (정규장 마감 심리)**\n"
        f" - 마감 1시간 변동: {nq_change_pct:+.2f}%\n"
        f" - 공포지수(VIX): {vix:.2f}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🐳 **비트코인 고래 수급 (Whale Alert)**\n"
        f" - 대량 매수: {btc_buy}회 / 매도: {btc_sell}회\n"
        f" - 수급 판단: {'매수 우위 🚀' if btc_buy > btc_sell else '매도 우위 📉'}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🇰🇷 **코스피 수급 현황**\n"
        f" - 현재 지수: {ks_info}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💡 **종합 판단:** "
    )
    
    if nq_change_pct > 0.3 and btc_buy > btc_sell:
        msg += "시장 전반에 매수세가 강합니다. 긍정적 대응!"
    elif nq_change_pct < -0.3:
        msg += "미국 마감 심리가 좋지 않습니다. 리스크 관리에 유의하세요."
    else:
        msg += "현재 지표들이 혼조세입니다. 개별 종목 장세에 집중하세요."

    return msg

def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_msg(get_combined_analysis())
  
