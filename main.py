import yfinance as yf
import requests
import os
from datetime import datetime
import pytz

def get_combined_analysis():
    # 1. 미국 나스닥 & VIX 분석 (최우선 지표)
    nq = yf.Ticker("NQ=F")
    df_nq = nq.history(period="2d", interval="1m")
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    
    nq_last = df_nq['Close'].iloc[-1]
    nq_one_hour_ago = df_nq['Close'].iloc[-60]
    nq_change_pct = ((nq_last - nq_one_hour_ago) / nq_one_hour_ago) * 100

    if nq_change_pct > 0.3:
        nq_status = "EXTREME_BULL"
        nq_comment = "✅ 세력의 '오버나잇' 의지 강함 (상승 주도)"
    elif nq_change_pct < -0.3:
        nq_status = "EXTREME_BEAR"
        nq_comment = "⚠️ 막판 투매 발생, 심리적 붕괴 (하락 경계)"
    else:
        nq_status = "NEUTRAL"
        nq_comment = "⚖️ 방향성 탐색 중 (나스닥 관망세)"

    # 2. 비트코인 고래 분석 (보조 지표)
    btc = yf.Ticker("BTC-USD")
    df_btc = btc.history(period="1d", interval="5m")
    avg_btc_vol = df_btc['Volume'].mean()
    whale_activity = df_btc[df_btc['Volume'] > avg_btc_vol * 3]
    btc_buy = len(whale_activity[whale_activity['Close'] > whale_activity['Open']])
    btc_sell = len(whale_activity[whale_activity['Close'] < whale_activity['Open']])
    btc_sentiment = "BULL" if btc_buy > btc_sell else "BEAR"

    # 3. 코스피 수급 강도 분석 (국내 실행 지표)
    ks = yf.Ticker("^KS11")
    df_ks = ks.history(period="1d", interval="1m")
    
    ks_info = "데이터 집계 전"
    ks_sentiment = "NEUTRAL"
    if not df_ks.empty:
        ks_start = df_ks['Open'].iloc[0]
        ks_current = df_ks['Close'].iloc[-1]
        ks_change_pct = ((ks_current - ks_start) / ks_start) * 100
        ks_vol_avg = df_ks['Volume'].mean()
        current_vol = df_ks['Volume'].iloc[-10:].mean()
        
        if ks_change_pct > 0.4 and current_vol > ks_vol_avg:
            ks_sentiment = "BULL"
            ks_comment = "🚀 외인/기관의 의도적 상방 배팅"
        elif ks_change_pct < -0.4 and current_vol > ks_vol_avg:
            ks_sentiment = "BEAR"
            ks_comment = "📉 외인 이탈 가속화, 방어 필요"
        else:
            ks_comment = "🐌 개인 위주의 탄력 없는 장세"
        ks_info = f"{ks_current:,.2f} ({ks_change_pct:+.2f}%)\n └ {ks_comment}"

    # 4. 나스닥 중심의 종합 판단 로직 (Weight: 나스닥 > BTC > 코스피)
    if nq_status == "EXTREME_BULL":
        if btc_sentiment == "BULL":
            summary = "🔥 [강력 매수] 나스닥 마감 심리가 압도적이며 고래 수급이 이를 지지합니다. 국장 시초가 적극 대응."
        else:
            summary = "💪 [매수 우위] 나스닥 의지는 강하나 코인 수급은 신중합니다. 나스닥을 믿고 분할 매수 진행."
    elif nq_status == "EXTREME_BEAR":
        summary = "🚨 [위험 관리] 나스닥 마감 심리가 붕괴되었습니다. 다른 지표와 상관없이 보수적으로 접근하세요."
    else:
        if btc_sentiment == "BULL" and ks_sentiment == "BULL":
            summary = "🧐 [중립 이상] 나스닥은 조용하나 비트코인과 국장 수급이 살아나고 있습니다. 단기 기술적 대응."
        else:
            summary = "☁️ [관망] 나스닥의 방향성이 모호합니다. 무리한 진입보다는 장중 수급 확정 시까지 대기."

    # 최종 메시지 조립
    msg = (
        f"📊 **나스닥 중심 시장 통합 리포트**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🇺🇸 **나스닥 마감 (최우선)**\n"
        f" - 1시간 변동: {nq_change_pct:+.2f}%\n"
        f" └ {nq_comment}\n"
        f" - VIX: {vix:.2f}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🐳 **BTC 고래 수급**\n"
        f" - 매수: {btc_buy}회 / 매도: {btc_sell}회\n"
        f" └ {'고래 매수 우위' if btc_sentiment == 'BULL' else '고래 매도 우위'}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🇰🇷 **코스피 수급 추정**\n"
        f" - {ks_info}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💡 **종합 판단 (나스닥 가중치 적용):**\n"
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
    
