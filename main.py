import yfinance as yf
import requests
import os
from datetime import datetime
import pytz

def get_combined_analysis():
    # 1. 미국 나스닥 (시초가 대비 최종 변동성 중심)
    nq = yf.Ticker("NQ=F")
    # 나스닥 개장(한국시간 밤)부터 마감까지를 보기 위해 충분한 데이터 로드
    df_nq = nq.history(period="2d", interval="5m")
    
    nq_open = df_nq['Open'].iloc[-1] # 오늘자 시초가
    nq_last = df_nq['Close'].iloc[-1] # 최종 종가
    nq_total_change = ((nq_last - nq_open) / nq_open) * 100 # 전체 변동폭
    
    # 장 막판 1시간의 의지 (마지막 12개 캔들)
    nq_last_hour_change = ((nq_last - df_nq['Close'].iloc[-12]) / df_nq['Close'].iloc[-12]) * 100
    
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]

    # 2. 비트코인 (나스닥 개장시간 기준 수익률 반영)
    btc = yf.Ticker("BTC-USD")
    # 나스닥 개장 시점(약 10~12시간 전)부터 현재까지의 변화
    df_btc = btc.history(period="1d", interval="5m")
    btc_now = df_btc['Close'].iloc[-1]
    btc_start = df_btc['Open'].iloc[0] # 오늘 시작가
    btc_total_change = ((btc_now - btc_start) / btc_start) * 100

    # 고래 수급 (변동성 보조)
    avg_btc_vol = df_btc['Volume'].mean()
    whale_activity = df_btc[df_btc['Volume'] > avg_btc_vol * 3]
    btc_buy = len(whale_activity[whale_activity['Close'] > whale_activity['Open']])
    btc_sell = len(whale_activity[whale_activity['Close'] < whale_activity['Open']])

    # 3. 코스피 수급 현황 (개장 전후 대응)
    ks = yf.Ticker("^KS11")
    df_ks = ks.history(period="2d")
    ks_prev_close = df_ks['Close'].iloc[-2]
    ks_current = df_ks['Close'].iloc[-1]
    ks_daily_change = ((ks_current - ks_prev_close) / ks_prev_close) * 100

    # 4. 나스닥 최우선 종합 판단 로직 개선
    # 전체 상승폭과 막판 의지를 결합
    if nq_total_change > 0.8:
        if nq_last_hour_change > 0:
            summary = f"🚀 [초강세] 나스닥이 시초가 대비 {nq_total_change:.1f}% 폭등하며 최고의 마감을 기록했습니다. 적극적 매수 구간입니다."
        else:
            summary = f"📈 [상승 마감] 나스닥 전반적으로 강했으나 막판에 일부 차익실현이 있었습니다. 시초가 강세 후 변동성 주의."
    elif nq_total_change < -0.8:
        summary = f"🚨 [폭락 경보] 나스닥 시초가 대비 {nq_total_change:.1f}% 하락하며 심리가 무너졌습니다. 보수적 대응 필수."
    else:
        summary = "⚖️ [방향성 모호] 지수가 박스권에 갇혀 있습니다. 장중 수급 확정 시까지 대기하세요."

    # 최종 메시지 구성
    msg = (
        f"📊 **신뢰도 강화 시장 통합 리포트**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🇺🇸 **나스닥 (시초가 대비 종가)**\n"
        f" - 전체 변동: {nq_total_change:+.2f}%\n"
        f" - 막판 1시간: {nq_last_hour_change:+.2f}%\n"
        f" └ 분석: {'✅ 세력의 강한 밀어올리기' if nq_total_change > 0.5 else '⚖️ 평이한 흐름'}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🐳 **BTC (가격 & 고래 수급)**\n"
        f" - 현재 변동: {btc_total_change:+.2f}%\n"
        f" - 고래 매수: {btc_buy}회 / 매도: {btc_sell}회\n"
        f" └ 분석: {'🔥 강력한 추세 상승' if btc_total_change > 3 else '🔍 수급 탐색 중'}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🇰🇷 **코스피 (전일 대비)**\n"
        f" - 현재 지수: {ks_current:,.2f} ({ks_daily_change:+.2f}%)\n"
        f" └ 개장 전 나스닥/비트코인 훈풍 반영 대기 중\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💡 **나스닥 중심 종합 판단:**\n"
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
    
