import yfinance as yf
import requests
import os
from datetime import datetime
import pytz

def get_combined_analysis():
    try:
       # 1. 미국 나스닥 (오늘 하루치 변동성 정밀 추출)
        nq = yf.Ticker("NQ=F")
        df_nq = nq.history(period="2d", interval="5m")
        
        if len(df_nq) < 15:
            nq_report = " - 나스닥: 데이터 부족 또는 휴장"
            nq_status = "NEUTRAL"
        else:
            # [수정 포인트] 마지막 데이터의 날짜(오늘)와 같은 데이터들만 필터링
            last_date = df_nq.index[-1].date()
            today_df = df_nq[df_nq.index.date == last_date]
            
            nq_open = today_df['Open'].iloc[0] # 오늘 장 시작가
            nq_last = today_df['Close'].iloc[-1] # 현재(최종) 종가
            nq_total_change = ((nq_last - nq_open) / nq_open) * 100
            
            # 막판 1시간 변동성 (동일)
            nq_last_hour = ((nq_last - today_df['Close'].iloc[-12]) / today_df['Close'].iloc[-12]) * 100
            
            nq_report = (
                f" - 오늘 변동(장중): {nq_total_change:+.2f}%\n"
                f" - 막판 1시간: {nq_last_hour:+.2f}%\n"
                f" └ 분석: {'✅ 강력한 원웨이 상승' if nq_total_change > 1.0 else '⚖️ 정상 범위 내 흐름'}"
            )
            nq_status = "BULL" if nq_total_change > 0.8 else ("BEAR" if nq_total_change < -0.8 else "NEUTRAL")
        # 2. 비트코인 (24시간 수익률 중심)
        btc = yf.Ticker("BTC-USD")
        df_btc = btc.history(period="1d", interval="5m")
        
        if not df_btc.empty:
            btc_start = df_btc['Open'].iloc[0]
            btc_now = df_btc['Close'].iloc[-1]
            btc_total_change = ((btc_now - btc_start) / btc_start) * 100
            
            avg_btc_vol = df_btc['Volume'].mean()
            whale_act = df_btc[df_btc['Volume'] > avg_btc_vol * 3]
            btc_buy = len(whale_act[whale_act['Close'] > whale_act['Open']])
            btc_sell = len(whale_act) - btc_buy
            
            btc_report = (
                f" - 현재 수익률: {btc_total_change:+.2f}%\n"
                f" - 고래 매수: {btc_buy}회 / 매도: {btc_sell}회\n"
                f" └ 분석: {'🔥 강력한 추세 상승' if btc_total_change > 3 else '🔍 수급 탐색 중'}"
            )
        else:
            btc_report = " - 비트코인: 데이터를 불러올 수 없습니다."

        # 3. 코스피 (전일 대비)
        ks = yf.Ticker("^KS11")
        df_ks = ks.history(period="2d")
        if len(df_ks) >= 2:
            ks_prev = df_ks['Close'].iloc[-2]
            ks_now = df_ks['Close'].iloc[-1]
            ks_change = ((ks_now - ks_prev) / ks_prev) * 100
            ks_report = f" - 현재 지수: {ks_now:,.2f} ({ks_change:+.2f}%)\n └ 개장 전 해외 수입 반영 대기"
        else:
            ks_report = " - 코스피: 휴장 또는 데이터 집계 전입니다."

        # 4. 종합 판단 로직 (나스닥 중심)
        if nq_status == "BULL":
            summary = "🚀 [초강세] 나스닥 폭등 및 기관 수급 확인. 적극적 매수 대응 구간."
        elif nq_status == "BEAR":
            summary = "🚨 [폭락 주의] 나스닥 심리 붕괴. 국장 시초가 매수 금지 및 리스크 관리."
        else:
            summary = "⚖️ [방향성 모호] 지수 박스권 정체. 장중 개별 종목 수급 확인 필요."

        # 최종 메시지 구성
        return (
            f"📊 **신뢰도 강화 시장 통합 리포트**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🇺🇸 **나스닥 (Price & Flow)**\n"
            f"{nq_report}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🐳 **BTC (실시간 변동률)**\n"
            f"{btc_report}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🇰🇷 **코스피 (현 위치)**\n"
            f"{ks_report}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 **종합 판단:**\n {summary}"
        )

    except Exception as e:
        return f"❌ 분석 중 오류 발생: {str(e)}"

def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_msg(get_combined_analysis())
    
