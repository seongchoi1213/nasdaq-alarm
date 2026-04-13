import yfinance as yf
import requests
import os

def get_analysis():
    # 나스닥 선물 데이터 가져오기 (1분 단위)
    df = yf.Ticker("NQ=F").history(period="2d", interval="1m")
    last_close = df['Close'].iloc[-1]
    one_hour_ago = df['Close'].iloc[-60]
    
    change_pct = ((last_close - one_hour_ago) / one_hour_ago) * 100
    
    # 영상의 핵심 논리: 막판 1시간의 방향성 분석
    if change_pct > 0.3:
        result = f"🚀 **상승 마감 (매수 우위)**\n시장이 주식을 들고 가기로 결정했습니다."
    elif change_pct < -0.3:
        result = f"📉 **하락 마감 (매도 우위)**\n리스크를 피해 투매가 일어났습니다."
    else:
        result = f"⚖️ **보합 마감 (관망세)**\n큰 방향성 없이 마무리되었습니다."

    return (f"📊 **나스닥 마감 1시간 분석**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🏁 최종 종가: {last_close:,.2f}\n"
            f"📈 막판 변동: {change_pct:+.2f}%\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 **판단:** {result}")

def send_msg(text):
    token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_msg(get_analysis())
