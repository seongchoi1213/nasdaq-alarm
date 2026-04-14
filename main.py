import yfinance as yf
import requests
import os
from datetime import datetime, time
import pytz
import google.generativeai as genai

# Gemini AI 설정
def get_ai_analysis(market_data):
    try:
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        당신은 전문 금융 분석 비서입니다. 아래 제공된 실시간 시장 데이터를 바탕으로 투자자가 오늘 주목해야 할 핵심 포인트 3가지를 분석해주세요.
        전문적이면서도 명확한 말투(~입니다, ~하세요)를 사용하고, 데이터 간의 상관관계(예: 환율과 외인 수급의 관계)를 짚어주세요.
        
        [시장 데이터]
        {market_data}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 분석을 가져오지 못했습니다: {str(e)}"

def get_combined_analysis():
    try:
        seoul_tz = pytz.timezone('Asia/Seoul')
        now_seoul = datetime.now(seoul_tz)
        
        # 1. 환율
        usdkrw = yf.Ticker("USDKRW=X")
        df_fx = usdkrw.history(period="2d")
        fx_now = df_fx['Close'].iloc[-1]
        fx_diff = fx_now - df_fx['Close'].iloc[-2]
        fx_report = f"현재 {fx_now:,.2f}원 ({fx_diff:+.2f}원)"

        # 2. 나스닥 & VIX
        nq = yf.Ticker("NQ=F")
        df_nq = nq.history(period="2d", interval="5m")
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        nq_change = ((df_nq['Close'].iloc[-1] - df_nq['Open'].iloc[0]) / df_nq['Open'].iloc[0]) * 100 if len(df_nq) > 0 else 0
        nq_report = f"변동률 {nq_change:+.2f}%, VIX {vix:.2f}"

        # 3. 비트코인
        btc = yf.Ticker("BTC-USD")
        df_btc = btc.history(period="1d", interval="5m")
        btc_change = ((df_btc['Close'].iloc[-1] - df_btc['Open'].iloc[0]) / df_btc['Open'].iloc[0]) * 100 if not df_btc.empty else 0
        btc_report = f"수익률 {btc_change:+.2f}%"

        # 4. 코스피 (09-11시 수급)
        ks = yf.Ticker("^KS11")
        df_ks = ks.history(period="1d", interval="5m")
        ks_report = "데이터 수집 중"
        if not df_ks.empty:
            df_ks.index = df_ks.index.tz_convert('Asia/Seoul')
            morning_df = df_ks[df_ks.index.time <= time(11, 5)]
            if not morning_df.empty:
                ks_change = ((morning_df['Close'].iloc[-1] - morning_df['Open'].iloc[0]) / morning_df['Open'].iloc[0]) * 100
                ks_report = f"시초가 대비 {ks_change:+.2f}%"

        # 데이터 취합 (AI 전달용)
        raw_data = f"환율: {fx_report}, 나스닥: {nq_report}, 비트코인: {btc_report}, 코스피: {ks_report}"
        
        # AI 비서의 심층 분석 호출
        ai_briefing = get_ai_analysis(raw_data)

        return (
            f"📊 **{now_seoul.strftime('%m/%d')} AI 통합 마켓 리포트**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💵 **환율:** {fx_report}\n"
            f"🇺🇸 **나스닥:** {nq_report}\n"
            f"🐳 **BTC:** {btc_report}\n"
            f"🇰🇷 **국장:** {ks_report}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🤖 **AI 비서의 심층 브리핑**\n"
            f"{ai_briefing}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 *이 데이터는 AI가 분석한 참고용 지표입니다.*"
        )
    except Exception as e:
        return f"❌ 오류 발생: {str(e)}"

def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_msg(get_combined_analysis())
    
