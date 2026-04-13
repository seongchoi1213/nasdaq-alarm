import yfinance as yf
import requests
import os
from datetime import datetime
import pytz

def get_combined_analysis():
    # 1. 미국 나스닥 & 옵션 심리
    nq = yf.Ticker("NQ=F")
    df_nq = nq.history(period="2d", interval="1m")
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    
    nq_last = df_nq['Close'].iloc[-1]
    nq_one_hour_ago = df_nq['Close'].iloc[-60]
    nq_change_pct = ((nq_last - nq_one_hour_ago) / nq_one_hour_ago) * 100

    # 나스닥 옵션 심리 추정 (VIX와 지수 변동성 활용)
    # VIX가 급등하며 지수가 밀리면 풋옵션(하락베팅) 과열로 판단
    if vix > 20 and nq_change_pct < -0.5:
        option_sentiment_us = "🚨 풋옵션 과열 (공포 극대화)"
    elif vix < 15 and nq_change_pct > 0.5:
        option_sentiment_us = "🔥 콜옵션 과열 (낙관 주의)"
    else:
        option_sentiment_us = "⚖️ 옵션 포지션 중립"

    # 2. 비트코인 수급 & 펀딩비 심리 (옵션 대용)
    btc = yf.Ticker("BTC-USD")
    df_btc = btc.history(period="1d", interval="5m")
    avg_btc_vol = df_btc['Volume'].mean()
    whale_activity = df_btc[df_btc['Volume'] > avg_btc_vol * 3]
    btc_buy = len(whale_activity[whale_activity['Close'] > whale_activity['Open']])
    btc_sell = len(whale_activity[whale_activity['Close'] < whale_activity['Open']])
    
    # 가격이 오르는데 거래량이 터지면 롱 포지션 우위로 추정
    btc_pos_sentiment = "📈 롱(상승) 포지션 우세" if btc_buy > btc_sell else "📉 숏(하락) 포지션 우세"

    # 3. 코스피 수급 및 풋/콜 추정
    ks = yf.Ticker("^KS11")
    df_ks = ks.history(period="1d", interval="1m")
    
    ks_info = "데이터 집계 전"
    if not df_ks.empty:
        ks_start = df_ks['Open'].iloc[0]
        ks_current = df_ks['Close'].iloc[-1]
        ks_change_pct = ((ks_current - ks_start) / ks_start) * 100
        
        # 국장 옵션 심리: 지수가 시초가 대비 밀리면서 거래량이 실리면 풋옵션 매수 강세로 추정
        if ks_change_pct < -0.6:
            ks_option_sm = "⚠️ 풋옵션(하락배팅) 우위"
        elif ks_change_pct > 0.6:
            ks_option_sm = "🚀 콜옵션(상승배팅) 우위"
        else:
            ks_option_sm = "⚖️ 옵션 균형 상태"
        
        ks_info = f"{ks_current:,.2f} ({ks_change_pct:+.2f}%)\n └ 심리: {ks_option_sm}"

    # 4. 종합 판단 (나스닥 가중치 + 옵션 심리 결합)
    if nq_change_pct > 0.3:
        if "과열" in option_sentiment_us:
            summary = "⚠️ [추격 금지] 나스닥은 강하나 옵션 심리가 과열권입니다. 눌림목 매수 권장."
        else:
            summary = "🔥 [강력 매수] 수급과 옵션 심리가 모두 상방을 가리키는 건강한 상승입니다."
    elif nq_change_pct < -0.3:
        summary = "🚨 [관망] 나스닥 하락 배팅(풋)이 강합니다. 지지선 확인 전까지 매수 금지."
    else:
        summary = "🧐 [중립] 시장이 방향성을 결정하지 못했습니다. 단기 박스권 매매 유효."

    # 최종 메시지 구성
    msg = (
        f"📊 **옵션 심리 포함 시장 리포트**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🇺🇸 **나스닥 & 옵션 심리**\n"
        f" - 1시간 변동: {nq_change_pct:+.2f}%\n"
        f" └ 분석: {option_sentiment_us}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🐳 **BTC 고래 & 포지션**\n"
        f" - 매수: {btc_buy}회 / 매도: {btc_sell}회\n"
        f" └ 추정: {btc_pos_sentiment}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🇰🇷 **코스피 수급 & 옵션**\n"
        f" - {ks_info}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💡 **종합 판단:**\n"
        f" {summary}"
    )

    return msg

def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_msg(get_combined_analysis())
    
