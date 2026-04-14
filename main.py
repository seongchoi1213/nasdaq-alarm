import yfinance as yf
import requests
import os
from datetime import datetime, time
import pytz

def get_combined_analysis():
    try:
        # 시간대 설정
        seoul_tz = pytz.timezone('Asia/Seoul')
        now_seoul = datetime.now(seoul_tz)
        
        # 1. 나스닥 (당일 개장 대비 수익률 정밀 추출)
        nq = yf.Ticker("NQ=F")
        df_nq = nq.history(period="2d", interval="5m")
        
        if len(df_nq) < 15:
            nq_report, nq_status = " - 나스닥: 데이터 부족 또는 휴장", "NEUTRAL"
        else:
            last_date = df_nq.index[-1].date()
            today_df = df_nq[df_nq.index.date == last_date]
            
            nq_open = today_df['Open'].iloc[0] 
            nq_last = today_df['Close'].iloc[-1]
            nq_total_change = ((nq_last - nq_open) / nq_open) * 100
            nq_last_hour = ((nq_last - today_df['Close'].iloc[-12]) / today_df['Close'].iloc[-12]) * 100
            
            nq_report = (
                f" - 오늘 장중 변동: {nq_total_change:+.2f}%\n"
                f" - 막판 1시간: {nq_last_hour:+.2f}%\n"
                f" └ 분석: {'✅ 강력한 상방 의지' if nq_total_change > 0.8 else '⚖️ 평이한 흐름'}"
            )
            nq_status = "BULL" if nq_total_change > 0.8 else ("BEAR" if nq_total_change < -0.8 else "NEUTRAL")

        # 2. 비트코인 (24시간 가격 변동)
        btc = yf.Ticker("BTC-USD")
        df_btc = btc.history(period="1d", interval="5m")
        
        if not df_btc.empty:
            btc_start = df_btc['Open'].iloc[0]
            btc_now = df_btc['Close'].iloc[-1]
            btc_total_change = ((btc_now - btc_start) / btc_start) * 100
            btc_report = f" - 현재 수익률: {btc_total_change:+.2f}%\n └ 분석: {'🔥 강력한 추세 상승' if btc_total_change > 3 else '🔍 수급 탐색 중'}"
        else:
            btc_report = " - 비트코인: 데이터 수신 실패"

        # 3. 코스피 (09:00 ~ 11:00 수급 집중 분석)
        ks = yf.Ticker("^KS11")
        df_ks = ks.history(period="1d", interval="5m")
        
        if not df_ks.empty:
            # 11:00 이전 데이터만 필터링 (안정성을 위해 11:05까지 포함)
            df_ks.index = df_ks.index.tz_convert('Asia/Seoul')
            morning_df = df_ks[df_ks.index.time <= time(11, 5)]
            
            if not morning_df.empty:
                ks_open = morning_df['Open'].iloc[0]
                ks_1100 = morning_df['Close'].iloc[-1]
                ks_change = ((ks_1100 - ks_open) / ks_open) * 100
                
                # 수급 강도 (평균 거래량 대비 11시 직전 거래량)
                avg_vol = morning_df['Volume'].mean()
                final_vol = morning_df['Volume'].iloc[-3:].mean()
                
                if ks_change > 0.4 and final_vol > avg_vol:
                    ks_flow = "🚀 외인/기관 동반 매수 (오전 우위)"
                elif ks_change < -0.4 and final_vol > avg_vol:
                    ks_flow = "📉 외인/기관 동반 매도 (하락 주도)"
                else:
                    ks_flow = "⚖️ 수급 혼조/개인 위주 장세"

                ks_report = (
                    f" - [09:00~11:00] 변동: {ks_change:+.2f}%\n"
                    f" - 11시 수급 판정: {ks_flow}\n"
                    f" └ 분석: {'✅ 오전 수급 상방 고착' if ks_change > 0.3 else '🔍 오후장 변동 대기'}"
                )
            else:
                ks_report = " - 코스피: 11시 데이터 집계 중입니다."
        else:
            ks_report = " - 코스피: 휴장 또는 데이터 없음."

        # 4. 종합 판단
        summary = "🚀 [매수 우위] 글로벌 상방 동조화" if nq_status == "BULL" else \
                  ("🚨 [보수적 대응] 미국발 하락 압력 주의" if nq_status == "BEAR" else "🧐 [관망] 수급 종목별 차별화 장세")

        # 메시지 조립
        msg = (
            f"📊 **{now_seoul.strftime('%m/%d')} 실전 수급 리포트**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🇺🇸 **나스닥 (당일 수익률)**\n{nq_report}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🐳 **BTC (실시간 변동)**\n{btc_report}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🇰🇷 **코스피 (09~11시 수급)**\n{ks_report}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 **종합 판단:**\n {summary}"
        )
        return msg

    except Exception as e:
        return f"❌ 분석 중 오류 발생: {str(e)}"

def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_msg(get_combined_analysis())
    
