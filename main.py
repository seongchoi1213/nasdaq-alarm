import yfinance as yf
import requests
import os
from datetime import datetime, time
import pytz
import google.generativeai as genai

# Gemini AI 심층 분석 함수
def get_ai_analysis(market_data):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return "⚠️ AI API 키가 설정되지 않았습니다. 수치 데이터만 제공합니다."
    
    try:
        genai.configure(api_key=api_key)
        # 안정적인 1.5 Flash 모델 사용
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        당신은 실력 있는 전업 투자자의 개인 비서입니다. 
        아래의 시장 데이터를 분석하여 투자자가 오늘 취해야 할 전략을 '핵심 브리핑' 형태로 작성하세요.
        환율과 코스피 수급의 관계, 나스닥과 비트코인의 심리를 연결해서 설명하고 전문적이되 명쾌하게 작성하세요.
        
        [오늘의 시장 데이터]
        {market_data}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"🔍 AI 분석 중 일시적 오류: {str(e)}"

def get_combined_analysis():
    try:
        seoul_tz = pytz.timezone('Asia/Seoul')
        now_seoul = datetime.now(seoul_tz)
        
        # 1. 환율 (USDKRW)
        usdkrw = yf.Ticker("USDKRW=X")
        df_fx = usdkrw.history(period="2d")
        fx_now = df_fx['Close'].iloc[-1]
        fx_diff = fx_now - df_fx['Close'].iloc[-2]
        fx_report = f"{fx_now:,.2f}원 ({fx_diff:+.2f}원)"

        # 2. 나스닥 및 변동성 지수
        nq = yf.Ticker("NQ=F")
        df_nq = nq.history(period="2d", interval="5m")
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        nq_change = ((df_nq['Close'].iloc[-1] - df_nq['Open'].iloc[0]) / df_nq['Open'].iloc[0]) * 100 if len(df_nq) > 0 else 0
        nq_report = f"{nq_change:+.2f}% (공포지수 VIX: {vix:.2f})"

        # 3. 비트코인
        btc = yf.Ticker("BTC-USD")
        df_btc = btc.history(period="1d", interval="5m")
        btc_change = ((df_btc['Close'].iloc[-1] - df_btc['Open'].iloc[0]) / df_btc['Open'].iloc[0]) * 100 if not df_btc.empty else 0
        btc_report = f"{btc_change:+.2f}%"

        # 4. 코스피 (09-11시 수급)
        ks = yf.Ticker("^KS11")
        df_ks = ks.history(period="1d", interval="5m")
        ks_report = "장 개시 전 또는 데이터 수집 불가"
        if not df_ks.empty:
            df_ks.index = df_ks.index.tz_convert('Asia/Seoul')
            morning_df = df_ks[df_ks.index.time <= time(11, 5)]
            if not morning_df.empty:
                ks_change = ((morning_df['Close'].iloc[-1] - morning_df['Open'].iloc[0]) / morning_df['Open'].iloc[0]) * 100
                ks_report = f"시초가 대비 {ks_change:+.2f}% (오전 수급 반영)"

        # AI 전달용 데이터 문자열
        market_summary = f"환율: {fx_report} / 나스닥: {nq_report} / 비트코인: {btc_report} / 코스피: {ks_report}"
        
        # AI 비서 분석 결과
        ai_briefing = get_ai_analysis(market_summary)

        # 텔레그램 메시지 구성
        return (
            f"📊 **{now_seoul.strftime('%m/%d')} AI 통합 리포트**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💵 **원/달러 환율:** {fx_report}\n"
            f"🇺🇸 **나스닥 선물:** {nq_report}\n"
            f"🐳 **비트코인:** {btc_report}\n"
            f"🇰🇷 **코스피 수급:** {ks_report}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🤖 **AI 비서의 심층 브리핑**\n\n"
            f"{ai_briefing}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 *성공적인 투자를 응원합니다.*"
        )
    except Exception as e:
        return f"❌ 리포트 생성 오류: {str(e)}"

def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_msg(get_combined_analysis())
