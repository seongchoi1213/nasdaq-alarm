import yfinance as yf
import requests
import os
from datetime import datetime, time
import pytz
import google.generativeai as genai

# ==========================================
# 1. AI 비서 분석 로직 (404 오류 방지 최적화)
# ==========================================
def get_ai_analysis(market_data):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return "⚠️ [설정 오류] GEMINI_API_KEY를 찾을 수 없습니다."
    
    try:
        # API 설정
        genai.configure(api_key=api_key)
        
        # 404 에러를 방지하기 위해 모델명만 정확히 입력
        # 라이브러리 버전에 따라 'models/gemini-1.5-flash' 혹은 'gemini-1.5-flash' 사용
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        당신은 금융 분석 비서입니다. 아래 제공된 시장 데이터를 바탕으로 
        투자자가 오늘 주목해야 할 핵심 전략 3가지를 브리핑하세요.
        문장은 간결하고 전문적인 톤으로 작성하세요.

        [시장 데이터 집계]
        {market_data}
        """
        
        # 콘텐츠 생성
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text
        else:
            return "🔍 데이터 해석에는 성공했으나 코멘트를 생성하지 못했습니다."

    except Exception as e:
        return f"🔍 AI 엔진 연결 오류: {str(e)}"

# ==========================================
# 2. 시장 데이터 수집 로직
# ==========================================
def get_combined_analysis():
    try:
        seoul_tz = pytz.timezone('Asia/Seoul')
        now_seoul = datetime.now(seoul_tz)
        
        # --- (1) 원/달러 환율 ---
        usdkrw = yf.Ticker("USDKRW=X")
        df_fx = usdkrw.history(period="2d")
        if len(df_fx) >= 2:
            fx_now = df_fx['Close'].iloc[-1]
            fx_diff = fx_now - df_fx['Close'].iloc[-2]
            fx_report = f"{fx_now:,.2f}원 ({fx_diff:+.2f}원)"
        else:
            fx_report = "환율 데이터 수신 지연"

        # --- (2) 나스닥 선물 및 VIX(공포지수) ---
        nq = yf.Ticker("NQ=F")
        df_nq = nq.history(period="2d", interval="5m")
        vix_data = yf.Ticker("^VIX").history(period="1d")
        vix = vix_data['Close'].iloc[-1] if not vix_data.empty else 0
        
        if not df_nq.empty:
            nq_change = ((df_nq['Close'].iloc[-1] - df_nq['Open'].iloc[0]) / df_nq['Open'].iloc[0]) * 100
            nq_report = f"{nq_change:+.2f}% (VIX: {vix:.2f})"
        else:
            nq_report = "나스닥 데이터 수신 지연"

        # --- (3) 비트코인 ---
        btc = yf.Ticker("BTC-USD")
        df_btc = btc.history(period="1d", interval="5m")
        if not df_btc.empty:
            btc_change = ((df_btc['Close'].iloc[-1] - df_btc['Open'].iloc[0]) / df_btc['Open'].iloc[0]) * 100
            btc_report = f"{btc_change:+.2f}%"
        else:
            btc_report = "비트코인 데이터 수신 지연"

        # --- (4) 코스피 (09-11시 수급) ---
        ks = yf.Ticker("^KS11")
        df_ks = ks.history(period="1d", interval="5m")
        ks_report = "오전 수급 집계 전"
        if not df_ks.empty:
            df_ks.index = df_ks.index.tz_convert('Asia/Seoul')
            morning_df = df_ks[df_ks.index.time <= time(11, 5)]
            if not morning_df.empty:
                ks_change = ((morning_df['Close'].iloc[-1] - morning_df['Open'].iloc[0]) / morning_df['Open'].iloc[0]) * 100
                ks_report = f"시초 대비 {ks_change:+.2f}%"

        # AI 분석을 위한 데이터 요약
        market_summary = f"환율:{fx_report}, 나스닥:{nq_report}, BTC:{btc_report}, 코스피:{ks_report}"
        
        # AI 브리핑 생성
        ai_briefing = get_ai_analysis(market_summary)

        # 리포트 조립
        return (
            f"📊 **{now_seoul.strftime('%m/%d')} AI 통합 마켓 리포트**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💵 **원/달러 환율:** {fx_report}\n"
            f"🇺🇸 **나스닥 선물:** {nq_report}\n"
            f"🐳 **비트코인:** {btc_report}\n"
            f"🇰🇷 **코스피 수급:** {ks_report}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🤖 **AI 비서 브리핑**\n\n"
            f"{ai_briefing}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 *이 리포트는 실시간 데이터를 기반으로 자동 생성되었습니다.*"
        )
    except Exception as e:
        return f"❌ 리포트 생성 중 치명적 오류: {str(e)}"

# ==========================================
# 3. 텔레그램 전송 로직
# ==========================================
def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"메시지 전송 실패: {e}")

if __name__ == "__main__":
    send_msg(get_combined_analysis())
    
