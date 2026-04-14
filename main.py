import yfinance as yf
import requests
import os
from datetime import datetime, time
import pytz
import google.generativeai as genai
from google.generativeai.types import RequestOptions

# ==========================================
# 1. AI 비서 분석 로직 (V1 정식 버전 강제 고정)
# ==========================================
def get_ai_analysis(market_data):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return "⚠️ [설정 오류] GEMINI_API_KEY를 찾을 수 없습니다."
    
    try:
        genai.configure(api_key=api_key)
        
        # 404 에러 방지를 위한 1순위 모델 설정
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        당신은 금융 분석 비서입니다. 아래 데이터를 바탕으로 오늘 투자자가 주목해야 할 핵심 전략 3가지를 브리핑하세요.
        문장은 간결하고 전문적으로 작성하세요.

        [시장 데이터 집계]
        {market_data}
        """
        
        # [핵심 수정] api_version을 'v1'으로 강제 지정하여 404(v1beta 오류)를 방지합니다.
        response = model.generate_content(
            prompt,
            request_options=RequestOptions(api_version='v1')
        )
        
        if response and response.text:
            return response.text
        else:
            return "🔍 데이터 해석에는 성공했으나 코멘트를 생성하지 못했습니다."

    except Exception as e:
        # [우회 로직] 만약 그래도 에러가 나면 구형 안정 모델(gemini-pro)로 재시도
        try:
            model_alt = genai.GenerativeModel('gemini-pro')
            response_alt = model_alt.generate_content(prompt)
            return f"(우회 분석 적용) {response_alt.text}"
        except:
            return f"🔍 AI 엔진 최종 연결 오류: {str(e)}"

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
            fx_report = "데이터 수신 지연"

        # --- (2) 나스닥 선물 및 VIX ---
        nq = yf.Ticker("NQ=F")
        df_nq = nq.history(period="2d", interval="5m")
        vix_data = yf.Ticker("^VIX").history(period="1d")
        vix = vix_data['Close'].iloc[-1] if not vix_data.empty else 0
        
        if not df_nq.empty:
            nq_change = ((df_nq['Close'].iloc[-1] - df_nq['Open'].iloc[0]) / df_nq['Open'].iloc[0]) * 100
            nq_report = f"{nq_change:+.2f}% (VIX: {vix:.2f})"
        else:
            nq_report = "데이터 수신 지연"

        # --- (3) 비트코인 ---
        btc = yf.Ticker("BTC-USD")
        df_btc = btc.history(period="1d", interval="5m")
        if not df_btc.empty:
            btc_change = ((df_btc['Close'].iloc[-1] - df_btc['Open'].iloc[0]) / df_btc['Open'].iloc[0]) * 100
            btc_report = f"{btc_change:+.2f}%"
        else:
            btc_report = "데이터 수신 지연"

        # --- (4) 코스피 (수강 수급) ---
        ks = yf.Ticker("^KS11")
        df_ks = ks.history(period="1d", interval="5m")
        ks_report = "장 개시 전"
        if not df_ks.empty:
            df_ks.index = df_ks.index.tz_convert('Asia/Seoul')
            morning_df = df_ks[df_ks.index.time <= time(11, 5)]
            if not morning_df.empty:
                ks_change = ((morning_df['Close'].iloc[-1] - morning_df['Open'].iloc[0]) / morning_df['Open'].iloc[0]) * 100
                ks_report = f"시초 대비 {ks_change:+.2f}%"

        market_summary = f"환율:{fx_report}, 나스닥:{nq_report}, BTC:{btc_report}, 코스피:{ks_report}"
        ai_briefing = get_ai_analysis(market_summary)

        return (
            f"📊 **{now_seoul.strftime('%m/%d')} AI 실전 수급 리포트**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💵 **환율:** {fx_report}\n"
            f"🇺🇸 **나스닥:** {nq_report}\n"
            f"🐳 **BTC:** {btc_report}\n"
            f"🇰🇷 **국장:** {ks_report}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🤖 **AI 비서의 심층 분석**\n\n"
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
    
