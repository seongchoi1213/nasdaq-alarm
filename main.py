import yfinance as yf
import requests
import os

def get_analysis():
    # 데이터 가져오기 (나스닥 선물 & VIX 공포지수)
    nq = yf.Ticker("NQ=F")
    vix = yf.Ticker("^VIX")
    
    df = nq.history(period="2d", interval="1m")
    vix_data = vix.history(period="1d")['Close'].iloc[-1]
    
    # 1. 마감 1시간 전 분석
    last_close = df['Close'].iloc[-1]
    one_hour_before = df['Close'].iloc[-60]
    reg_change_pct = ((last_close - one_hour_before) / one_hour_before) * 100
    
    # 2. 거래량 분석 (평균 대비 마감 직전 거래량)
    last_hour_vol = df['Volume'].iloc[-60:].sum()
    avg_vol = df['Volume'].mean() * 60  # 1분당 평균 거래량의 60배
    vol_ratio = (last_hour_vol / avg_vol) * 100

    # 3. 야간 선물 실시간 데이터
    current_price = nq.fast_info['last_price']
    overnight_change_pct = ((current_price - last_close) / last_close) * 100

    # 심리 판단 로직
    vol_status = "🔥 대량 거래 동반" if vol_ratio > 150 else "💨 평이한 거래량"
    
    if reg_change_pct > 0.3:
        reg_sentiment = "🚀 매수 우위 (의지 강함)"
    elif reg_change_pct < -0.3:
        reg_sentiment = "📉 매도 우위 (리스크 회피)"
    else:
        reg_sentiment = "⚖️ 보합 (방향성 부재)"

    # 메시지 구성
    message = (
        f"📊 **나스닥 종합 심리 분석 보고서**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔍 **[정규장 마감 심리]**\n"
        f" - 마감 1시간 변동: {reg_change_pct:+.2f}%\n"
        f" - 시장 의지: {reg_sentiment}\n"
        f" - 수급 강도: {vol_status} ({vol_ratio:.1f}%)\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🌙 **[실시간 야간/공포 지표]**\n"
        f" - 현재 선물: {current_price:,.2f} ({overnight_change_pct:+.2f}%)\n"
        f" - VIX(공포지수): {vix_data:.2f}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💡 **종합 분석:** "
    )

    # 수급 기반 종합 판단
    if reg_change_pct > 0.3 and vol_ratio > 130:
        message += "강한 거래량을 동반한 매수세가 확인됩니다. 기관/외인의 '진짜 매수'일 확률이 높습니다."
    elif reg_change_pct < -0.3 and vol_ratio > 130:
        message += "대량 거래를 동반한 투매가 나왔습니다. 하락 압력이 강하니 주의가 필요합니다."
    else:
        message += "거래량이 평소 수준입니다. 개인 위주의 흐름이거나 큰 변화 없는 마감입니다."

    return message

def send_msg(text):
    token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_msg(get_analysis())
