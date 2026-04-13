import yfinance as yf
import requests
import os

def get_analysis():
    # 나스닥 선물 실시간 데이터 (최근 2일치)
    df = yf.Ticker("NQ=F").history(period="2d", interval="1m")
    
    # 1. 정규장 마감 심리 분석 (장 마감 1시간 전 vs 종가)
    # 미국 장 마감은 한국 시간 기준 보통 오전 5시(서머타임) 또는 6시입니다.
    # 해당 시점의 데이터를 추출하기 위해 인덱스를 조정합니다.
    regular_close = df['Close'].iloc[-1] 
    one_hour_before = df['Close'].iloc[-60]
    reg_change_pct = ((regular_close - one_hour_before) / one_hour_before) * 100

    # 2. 야간 선물(현재 실시간) 흐름 분석
    # 현재 가격이 정규장 종가 대비 얼마나 변했는지 확인
    current_price = ticker_data = yf.Ticker("NQ=F").fast_info['last_price']
    overnight_change_pct = ((current_price - regular_close) / regular_close) * 100

    # 심리 판단 로직
    if reg_change_pct > 0.3:
        reg_sentiment = "🚀 매수 우위 (의지 강함)"
    elif reg_change_pct < -0.3:
        reg_sentiment = "📉 매도 우위 (리스크 회피)"
    else:
        reg_sentiment = "⚖️ 보합 (방향성 부재)"

    # 메시지 구성
    message = (
        f"📊 **나스닥 마감 및 야간 선물 분석**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔍 **[정규장 마감 직전 심리]**\n"
        f" - 마감 1시간 변동: {reg_change_pct:+.2f}%\n"
        f" - 시장의 의지: {reg_sentiment}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🌙 **[실시간 야간 선물 현황]**\n"
        f" - 현재 가격: {current_price:,.2f}\n"
        f" - 종가 대비 변동: {overnight_change_pct:+.2f}%\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💡 **종합 판단:** "
    )

    # 종합 판단 추가
    if reg_change_pct < 0 and overnight_change_pct > 0.3:
        message += "장 막판엔 밀렸으나 야간에 회복 중입니다. 저가 매수세 유입 확인."
    elif reg_change_pct > 0.3 and overnight_change_pct > 0.3:
        message += "마감 심리도 좋았고 야간에도 강세입니다. 매우 긍정적입니다."
    else:
        message += "전반적인 흐름을 주시하며 장 초반 30분 대응이 중요합니다."

    return message

def send_msg(text):
    token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_msg(get_analysis())
