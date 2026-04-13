import yfinance as yf
import requests
import os
from datetime import datetime
import pytz

def get_combined_analysis():
    # 한국 시간 설정
    korea_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(korea_tz)
    
    # 1. 비트코인 고래 분석 (거래량 급증 구간 추출)
    btc = yf.Ticker("BTC-USD")
    df_btc = btc.history(period="1d", interval="5m")
    avg_vol = df_btc['Volume'].mean()
    whale_activity = df_btc[df_btc['Volume'] > avg_vol * 3]
    btc_buy = len(whale_activity[whale_activity['Close'] > whale_activity['Open']])
    btc_sell = len(whale_activity[whale_activity['Close'] < whale_activity['Open']])

    # 2. 시장 분석 (시간대에 따라 모드 변경)
    if now.hour < 10: # 오전 10시 이전: 미국장 마감 분석 모드
        mode = "🇺🇸 미국장 마감 & 코인 수급"
        nq = yf.Ticker("NQ=F")
        df_nq = nq.history(period="2d", interval="1m")
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        
        change_val = ((df_nq['Close'].iloc[-1] - df_nq['Close'].iloc[-60]) / df_nq['Close'].iloc[-60]) * 100
        market_info = f" - 나스닥 마감 1시간 변동: {change_val:+.2f}%\n - 공포지수(VIX): {vix:.2f}"
    else: # 오전 10시 이후: 국장 실시간 수급 분석 모드
        mode = "🇰🇷 코스피 실시간 & 코인 수급"
        ks = yf.Ticker("^KS11")
        df_ks = ks.history(period="1d", interval="1m")
        
        if not df_ks.empty:
            change_val = ((df_ks['Close'].iloc[-1] - df_ks['Open'].iloc[0]) / df_ks['Open'].iloc[0]) * 100
            market_info = f" - 코스피 시초가 대비: {change_val:+.2f}%\n - 현재 지수: {df_ks['Close'].iloc[-1]:,.2f}"
        else:
            market_info = " - 국장 데이터 휴장 또는 집계 중"

    # 메시지 조립
    msg = (
        f"🚀 **{mode}**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📈 **시장 지표**\n{market_info}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🐳 **BTC 고래 활동 (최근)**\n"
        f" - 대량 매수: {btc_buy}회 / 매도: {btc_sell} ; {btc_sell}회\n"
        f" - 수급 판단: {'매수 우위 🚀' if btc_buy > btc_sell else '매도 우위 📉'}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💡 **종합 분석:** "
    )
    
    # 종합 판단 로직
    if btc_buy > btc_sell and "매수 우위" in market_info or (now.hour < 10 and change_val > 0.3):
        msg += "위험자산 선호 심리가 강합니다. 공격적 대응 가능!"
    else:
        msg += "시장 참여자들이 신중합니다. 분할 매수로 접근하세요."

    return msg

def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_msg(get_combined_analysis())
