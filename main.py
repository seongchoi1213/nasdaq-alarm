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

    # 나스닥 코멘트 함축
    if nq_change_pct > 0.3:
        nq_comment = "✅ 세력의 '오버나잇' 의지 강함 (상승 지속형)"
    elif nq_change_pct < -0.3:
        nq_comment = "⚠️ 막판 투매 발생, 불안한 심리 반영 (하락 주의)"
    else:
        nq_comment = "⚖️ 방향성 결정 미루며 눈치보기 중"

    # 2. 비트코인 고래 분석 (거래량 가중)
    btc = yf.Ticker("BTC-USD")
    df_btc = btc.history(period="1d", interval="5m")
    avg_btc_vol = df_btc['Volume'].mean()
    whale_activity = df_btc[df_btc['Volume'] > avg_btc_vol * 3]
    btc_buy = len(whale_activity[whale_activity['Close'] > whale_activity['Open']])
    btc_sell = len(whale_activity[whale_activity['Close'] < whale_activity['Open']])

    # 비트코인 코멘트 함축
    if btc_buy > btc_sell:
        btc_comment = "🐳 고래들의 저가 매수세 포착 (위험자산 선호)"
    elif btc_buy < btc_sell:
        btc_comment = "🚨 큰손들의 탈출 신호 감지 (리스크 오프)"
    else:
        btc_comment = "🔍 고래들이 조용히 숨 고르기 중"

    # 3. 코스피 수급 강도 분석
    ks = yf.Ticker("^KS11")
    df_ks = ks.history(period="1d", interval="1m")
    
    if not df_ks.empty:
        ks_start = df_ks['Open'].iloc[0]
        ks_current = df_ks['Close'].iloc[-1]
        ks_change_pct = ((ks_current - ks_start) / ks_start) * 100
        
        ks_vol_avg = df_ks['Volume'].mean()
        current_vol = df_ks['Volume'].iloc[-10:].mean()
        
        if ks_change_pct > 0.4 and current_vol > ks_vol_avg:
            ks_comment = "🚀 외인/기관의 의도적 상방 배팅 구간"
        elif ks_change_pct < -0.4 and current_vol > ks_vol_avg:
            ks_comment = "📉 외인 이탈 가속화, 현금 비중 확보 권장"
        else:
            ks_comment = "🐌 개인 위주의 탄력 없는 장세"
        ks_info = f"{ks_current:,.2f} ({ks_change_pct:+.2f}%)\n └ {ks_comment}"
    else:
        ks_info = "데이터 집계 전 또는 휴장일입니다."

    # 최종 메시지 조립
    msg = (
        f"📊 **글로벌 수급 & 심리 원샷 보고서**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🇺🇸 **나스닥 마감 심리**\n"
        f" - 1시간 변동: {nq_change_pct:+.2f}%\n"
        f" └ {nq_comment}\n"
        f" - VIX(공포): {vix:.2f}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🐳 **BTC 고래 (Whale Alert)**\n"
        f" - 매수: {btc_buy}회 / 매도: {btc_sell}회\n"
        f" └ {btc_comment}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🇰🇷 **코스피 수급 (추정)**\n"
        f" - {ks_info}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💡 **종합 판단:** "
    )
    
    # 전략 추천 자동 생성
    if "✅" in nq_comment and "🐳" in btc_comment:
        msg += "글로벌 수급 만점! 공격적 매수 타이밍입니다."
    elif "⚠️" in nq_comment or "🚨" in btc_comment:
        msg += "하방 압력이 큽니다. 방어적인 포지션을 유지하세요."
    else:
        msg += "시장 에너지가 분산되어 있습니다. 철저한 종목 장세 대응!"

    return msg

def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_msg(get_combined_analysis())
    
