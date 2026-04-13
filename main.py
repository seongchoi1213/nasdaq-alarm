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
    
    nq_last = df_nq['Close'].iloc[-1]
    nq_one_hour_ago = df_nq['Close'].iloc[-60]
    nq_change_pct = ((nq_last - nq_one_hour_ago) / nq_one_hour_ago) * 100

    # 2. 비트코인 고래 분석
    btc = yf.Ticker("BTC-USD")
    df_btc = btc.history(period="1d", interval="5m")
    avg_btc_vol = df_btc['Volume'].mean()
    whale_activity = df_btc[df_btc['Volume'] > avg_btc_vol * 3]
    btc_buy = len(whale_activity[whale_activity['Close'] > whale_activity['Open']])
    btc_sell = len(whale_activity[whale_activity['Close'] < whale_activity['Open']])

    # 3. 코스피 수급 강도 추정 (외인/기관 개입 분석)
    ks = yf.Ticker("^KS11")
    df_ks = ks.history(period="1d", interval="1m")
    
    if not df_ks.empty:
        ks_start = df_ks['Open'].iloc[0]
        ks_current = df_ks['Close'].iloc[-1]
        ks_change_pct = ((ks_current - ks_start) / ks_start) * 100
        
        # [수급 분석 로직] 거래량이 실리면서 지수가 시초가 대비 위/아래로 0.5% 이상 밀리면 외인/기관 개입으로 판단
        ks_vol_avg = df_ks['Volume'].mean()
        current_vol = df_ks['Volume'].iloc[-10:].mean() # 최근 10분 평균 거래량
        
        if ks_change_pct > 0.5 and current_vol > ks_vol_avg:
            supply_status = "🚀 외인/기관 강한 매수 유입 중"
        elif ks_change_pct < -0.5 and current_vol > ks_vol_avg:
            supply_status = "📉 외인/기관 물량 투하 중 (주의)"
        elif abs(ks_change_pct) < 0.2:
            supply_status = "⚖️ 외인/기관 관망 (개인 위주 장세)"
        else:
            supply_status = "🔍 수급 방향성 탐색 중"
            
        ks_info = f"{ks_current:,.2f} ({ks_change_pct:+.2f}%)\n - 실시간 수급: {supply_status}"
    else:
        ks_info = "데이터 집계 중 또는 휴장"

    # 메시지 조립
    msg = (
        f"🚀 **글로벌 수급 통합 리포트**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🇺🇸 **나스닥 마감 심리**\n"
        f" - 마감 1시간 변동: {nq_change_pct:+.2f}%\n"
        f" - VIX(공포지수): {vix:.2f}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🐳 **BTC 고래 수급**\n"
        f" - 대량 매수: {btc_buy}회 / 매도: {btc_sell}회\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🇰🇷 **코스피 외인/기관 추정**\n"
        f" - {ks_info}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💡 **종합 분석:** "
    )
    
    # 전략 추천
    if "매수 유입" in ks_info and nq_change_pct > 0:
        msg += "미국장 심리와 국장 수급이 일치합니다. 비중 확대 고려."
    elif "물량 투하" in ks_info:
        msg += "외인 이탈이 의심됩니다. 현금 비중을 확보하세요."
    else:
        msg += "지표가 엇갈리고 있습니다. 장 후반까지 관망이 유리합니다."

    return msg

def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_msg(get_combined_analysis())
    
