import yfinance as yf
import requests
import os
from datetime import datetime
import pytz

def get_combined_analysis():
    try:
        # 1. 미국 나스닥 (당일 개장 대비 종가/현재가 수익률)
        nq = yf.Ticker("NQ=F")
        df_nq = nq.history(period="2d", interval="5m")
        
        if len(df_nq) < 15:
            nq_report = " - 나스닥: 데이터 부족 또는 휴장"
            nq_status = "NEUTRAL"
        else:
            # 마지막 영업일 데이터만 추출
            last_date = df_nq.index[-1].date()
            today_df = df_nq[df_nq.index.date == last_date]
            
            nq_open = today_df['Open'].iloc[0] 
            nq_last = today_df['Close'].iloc[-1]
            nq_total_change = ((nq_last - nq_open) / nq_open) * 100
            
            # 막판 1시간(12캔들) 변동성
            nq_last_hour = ((nq_last - today_df['Close'].iloc[-12]) / today_df['Close'].iloc[-12]) * 100
            
            nq_report = (
                f" - 오늘 변동(장중): {nq_total_change:+.2f}%\n"
                f" - 막판 1시간: {nq_last_hour:+.2f}%\n"
                f" └ 분석: {'✅ 강력한 원웨이 상승' if nq_total_change > 1.0 else '⚖️ 정상 범위 내 흐름'}"
            )
            nq_status = "BULL" if nq_total_change > 0.8 else ("BEAR" if nq_total_change < -0.8 else "NEUTRAL")

        # 2. 비트코인 (24시간 가격 변동 및 고래 수급)
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

        # 3. 코스피 (개장~현재 수급 정밀 분석)
        ks = yf.Ticker("^KS11")
        df_ks = ks.history(period="1d", interval="5m")
        
        if not df_ks.empty:
            ks_open = df_ks['Open'].iloc[0] # 09:00 시초가
            ks_now = df_ks['Close'].iloc[-1] # 현재가
            ks_change = ((ks_now - ks_open) / ks_open) * 100
            
            # 수급 강도 분석 (거래량 가중)
            avg_vol = df_ks['Volume'].mean()
            current_vol = df_ks['Volume'].iloc[-6:].mean()
            
            if ks_change > 0.4 and current_vol > avg_vol:
                ks_flow = "🚀 외인/기관 동반 순매수 (상승 주도)"
            elif ks_change < -0.4 and current_vol > avg_vol:
                ks_flow = "📉 외인/기관 대량 매도 (하락 압력)"
            else:
                ks_flow = "⚖️ 외인/기관 눈치싸움 (개인 장세)"

            ks_report = (
                f" - 시초가 대비: {ks_change:+.2f}%\n"
                f" - 수급 분석: {ks_flow}\n"
                f" └ 분석: {'✅ 오전 수급 상방 고착' if ks_change > 0.3 else '⚠️ 변동성 확대 주의'}"
            )
        else:
            ks_report = " - 코스피: 휴장 또는 데이터 집계 전입니다."

        # 4. 종합 판단 로직 (나스닥 1순위)
        if nq_status == "BULL":
            summary = "🚀 [매수 우위] 글로벌 수급이 상방입니다. 공격적 대응이 유효합니다."
        elif nq_status == "BEAR":
            summary = "🚨 [리스크 관리] 나스닥 심리 붕괴. 국장 수급에 관계없이 보수적 접근."
        else:
            summary = "🧐 [중립] 방향성이 모호합니다. 철저히 수급이 붙는 종목으로만 대응."

        return (
            f"📊 **시장 통합 실전 리포트**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🇺🇸 **나스닥 (당일 수익률)**\n"
            f"{nq_report}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🐳 **BTC (가격 & 고래)**\n"
            f"{btc_report}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🇰🇷 **코스피 (오전 수급)**\n"
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
