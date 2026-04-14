import yfinance as yf
import requests
import os
from datetime import datetime, time
import pytz

def get_combined_analysis():
    try:
        seoul_tz = pytz.timezone('Asia/Seoul')
        now_seoul = datetime.now(seoul_tz)
        
        # 1. 나스닥 (당일 장중 변동성 & 시장 심리)
        nq = yf.Ticker("NQ=F")
        df_nq = nq.history(period="2d", interval="5m")
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1] # 공포지수
        
        if len(df_nq) < 15:
            nq_report, nq_status = " - 나스닥: 데이터 수신 지연 또는 휴장", "NEUTRAL"
        else:
            last_date = df_nq.index[-1].date()
            today_nq = df_nq[df_nq.index.date == last_date]
            nq_open = today_nq['Open'].iloc[0]
            nq_last = today_nq['Close'].iloc[-1]
            nq_change = ((nq_last - nq_open) / nq_open) * 100
            
            # 폴리마켓을 대체하는 스마트머니 심리 지표
            sentiment = "🔥 강세 우위" if vix < 20 and nq_change > 0.5 else "⚠️ 관망/공포"
            nq_report = f" - 장중 변동: {nq_change:+.2f}%\n - 시장 심리(VIX): {vix:.2f} ({sentiment})"
            nq_status = "BULL" if nq_change > 0.7 else ("BEAR" if nq_change < -0.7 else "NEUTRAL")

        # 2. 원/달러 환율 (외인 수급의 핵심)
        usdkrw = yf.Ticker("USDKRW=X")
        df_fx = usdkrw.history(period="2d")
        fx_now = df_fx['Close'].iloc[-1]
        fx_prev = df_fx['Close'].iloc[-2]
        fx_diff = fx_now - fx_prev
        fx_report = f" - 현재 환율: {fx_now:,.2f}원 ({fx_diff:+.2f}원)"

        # 3. 비트코인 (디지털 금 & 위험자산 선행)
        btc = yf.Ticker("BTC-USD")
        df_btc = btc.history(period="1d", interval="5m")
        if not df_btc.empty:
            btc_change = ((df_btc['Close'].iloc[-1] - df_btc['Open'].iloc[0]) / df_btc['Open'].iloc[0]) * 100
            btc_report = f" - 현재 수익률: {btc_change:+.2f}%\n └ 고래 동향: {'🐳 매집 중' if btc_change > 2 else '🔍 탐색 중'}"
        else:
            btc_report = " - 비트코인: 데이터 수신 불가"

        # 4. 코스피 (09:00~11:00 수급 정밀 분석)
        ks = yf.Ticker("^KS11")
        df_ks = ks.history(period="1d", interval="5m")
        if not df_ks.empty:
            df_ks.index = df_ks.index.tz_convert('Asia/Seoul')
            morning_df = df_ks[df_ks.index.time <= time(11, 5)]
            if not morning_df.empty:
                ks_open = morning_df['Open'].iloc[0]
                ks_1100 = morning_df['Close'].iloc[-1]
                ks_change = ((ks_1100 - ks_open) / ks_open) * 100
                
                # 수급 판정 (환율과 지수 변동 결합)
                if ks_change > 0.3 and fx_diff < 0:
                    ks_flow = "🚀 외인/기관 공격적 순매수"
                elif ks_change < -0.3 and fx_diff > 0:
                    ks_flow = "📉 외인/기관 동반 이탈"
                else:
                    ks_flow = "⚖️ 개인 위주 수급 혼조"
                
                ks_report = f" - [09~11시] 변동: {ks_change:+.2f}%\n - 수급 판정: {ks_flow}"
            else:
                ks_report = " - 코스피: 오전 데이터 집계 중"
        else:
            ks_report = " - 코스피: 휴장 또는 데이터 없음"

        # 5. 최종 종합 판단 (나스닥 + 환율 + 코스피 수급)
        if nq_status == "BULL" and fx_diff < 0:
            summary = "🔥 [강력 매수] 모든 지표 상방. 적극적 수익 극대화."
        elif nq_status == "BEAR" or fx_diff > 5:
            summary = "🚨 [현금 확보] 환율 급등 및 미 증시 불안. 방어적 태세."
        else:
            summary = "🧐 [선별 대응] 지수 정체기. 수급이 쏠리는 개별주 집중."

        return (
            f"📊 **{now_seoul.strftime('%m/%d')} 실전 통합 리포트**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💵 **원/달러 환율 (FX)**\n{fx_report}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🇺🇸 **나스닥 (Market Sentiment)**\n{nq_report}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🐳 **BTC (Crypto High-Low)**\n{btc_report}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🇰🇷 **코스피 (09-11시 수급)**\n{ks_report}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 **종합 판단:**\n {summary}"
        )
    except Exception as e:
        return f"❌ 시스템 오류 발생: {str(e)}"

def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_msg(get_combined_analysis())
    
