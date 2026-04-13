import yfinance as yf
import requests
import os
from datetime import datetime
import pytz

def get_combined_analysis():
    try:
        # 1. 미국 나스닥 & 기관 수급 추정
        nq = yf.Ticker("NQ=F")
        df_nq = nq.history(period="2d", interval="5m")
        
        if df_nq.empty or len(df_nq) < 20:
            return "❌ 나스닥 데이터를 불러오지 못했습니다. 시장 점검 중일 수 있습니다."

        nq_open = df_nq['Open'].iloc[0] # 데이터셋의 첫 시초가
        nq_last = df_nq['Close'].iloc[-1]
        nq_total_change = ((nq_last - nq_open) / nq_open) * 100
        
        avg_vol = df_nq['Volume'].mean()
        last_vol = df_nq['Volume'].iloc[-12:].mean()
        
        if nq_total_change > 0.7 and last_vol > avg_vol * 1.2:
            inst_flow = "🚀 기관/프로그램 동반 강매수"
        elif nq_total_change < -0.7 and last_vol > avg_vol * 1.2:
            inst_flow = "📉 기관 주도 대량 매도"
        else:
            inst_flow = "⚖️ 개인 위주 소강상태"

        # 2. 비트코인 분석
        btc = yf.Ticker("BTC-USD")
        df_btc = btc.history(period="1d", interval="5m")
        
        if not df_btc.empty:
            btc_start = df_btc['Open'].iloc[0]
            btc_now = df_btc['Close'].iloc[-1]
            btc_total_change = ((btc_now - btc_start) / btc_start) * 100
            
            avg_btc_vol = df_btc['Volume'].mean()
            whale_act = df_btc[df_btc['Volume'] > avg_btc_vol * 3]
            btc_buy = len(whale_act[whale_act['Close'] > whale_act['Open']])
            btc_sell = len(whale_act[whale_act['Volume'] > 0]) - btc_buy # 안전한 계산
        else:
            btc_total_change, btc_buy, btc_sell = 0, 0, 0

        # 3. 코스피 상황
        ks = yf.Ticker("^KS11")
        df_ks = ks.history(period="2d")
        if len(df_ks) >= 2:
            ks_last = df_ks['Close'].iloc[-1]
            ks_prev = df_ks['Close'].iloc[-2]
            ks_change = ((ks_last - ks_prev) / ks_prev) * 100
        else:
            ks_last, ks_change = 0, 0

        # 4. 종합 판단
        if nq_total_change > 1.0:
            summary = f"🔥 [강력 매수] 나스닥 폭등({nq_total_change:.1f}%). 기관 수급 확인."
        elif nq_total_change < -1.0:
            summary = f"🚨 [전량 관망] 나스닥 붕괴({nq_total_change:.1f}%). 리스크 관리 필수."
        else:
            summary = "🧐 [선별 대응] 지수 박스권. 종급 수급주 중심 대응."

        return (
            f"📊 **실전 수급 통합 리포트**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🇺🇸 **나스닥 (Price & Inst.)**\n"
            f" - 최종 수익률: {nq_total_change:+.2f}%\n"
            f" - 기관 흐름: {inst_flow}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🐳 **BTC (실시간 변동률)**\n"
            f" - 현재 수익률: {btc_total_change:+.2f}%\n"
            f" - 고래 매수: {btc_buy}회 / 매도: {btc_sell}회\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🇰🇷 **코스피 (현 위치)**\n"
            f" - 지수: {ks_last:,.2f} ({ks_change:+.2f}%)\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 **종합 판단:**\n {summary}"
        )
    except Exception as e:
        return f"❌ 코드 실행 중 에러 발생: {str(e)}"

def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_msg(get_combined_analysis())
