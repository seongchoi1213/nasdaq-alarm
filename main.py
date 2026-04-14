import yfinance as yf
import requests
import os
from datetime import datetime, time
import pytz
import google.generativeai as genai

# Gemini AI 심층 분석 함수 (수정 버전)
def get_ai_analysis(market_data):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return "⚠️ AI API 키가 설정되지 않았습니다."
    
    try:
        genai.configure(api_key=api_key)
        
        # 모델 설정 (가장 표준적인 'gemini-1.5-flash' 사용)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        당신은 금융 분석 비서입니다. 아래 데이터를 바탕으로 투자 전략 핵심 3가지를 브리핑하세요.
        문장은 간결하고 명확하게 작성하세요.
        
        [데이터]
        {market_data}
        """
        
        # 콘텐츠 생성
        response = model.generate_content(prompt)
        
        # 응답 텍스트 반환
        if response and response.text:
            return response.text
        else:
            return "🔍 AI가 데이터를 해석했지만 답변을 생성하지 못했습니다."

    except Exception as e:
        # 에러 발생 시 상세 메시지 출력 (디버깅용)
        return f"🔍 AI 분석 엔진 연결 오류: {str(e)}"

def get_combined_analysis():
    try:
        seoul_tz = pytz.timezone('Asia/Seoul')
        now_seoul = datetime.now(seoul_tz)
        
        # 1. 환율
        usdkrw = yf.Ticker("USDKRW=X")
        df_fx = usdkrw.history(period="2d")
        fx_now = df_fx['Close'].iloc[-1]
        fx_diff = fx_now - df_fx['Close'].iloc[-2]
        fx_report = f"{fx_now:,.2f}원 ({fx_diff:+.2f}원)"

        # 2. 나스닥 및 VIX
        nq = yf.Ticker("NQ=F")
        df_nq = nq.history(period="2d", interval="5m")
        vix_data = yf.Ticker("^VIX").history(period="1d")
        vix = vix_data['Close'].iloc[-1] if not vix_data.empty else 0
        nq_change = ((df_nq['Close'].iloc[-1] - df_nq['Open'].iloc[0]) / df_nq['Open'].iloc[0]) * 100 if len(df_nq) > 0 else 0
        nq_report = f"{nq_change:+.2f}% (VIX: {vix:.2f})"

        # 3. 비트코인
        btc = yf.Ticker("BTC-USD")
        df_btc = btc.history(period="1d", interval="5m")
        btc_change = ((df_btc['Close'].iloc[-1] - df_btc['Open'].iloc[0]) / df_btc['Open'].iloc[0]) * 100 if not df_btc.empty else 0
        btc_report = f"{btc_change:+.2f}%"

        # 4. 코스피
        ks = yf.Ticker("^KS11")
        df_ks = ks.history(period="1d", interval="5m")
        ks_report = "데이터 수집 전"
        if not df_ks.empty:
            df_ks.index = df_ks.index.tz_convert('Asia/Seoul')
            morning_df = df_ks[df_ks.index.time <= time(11, 5)]
            if not morning_df.empty:
                ks_change = ((morning_df['Close'].iloc[-1] - morning_df['Open'].iloc[0]) / morning_df['Open'].iloc[0]) * 100
                ks_report = f"시초 대비 {ks_change:+.2f}%"

        market_summary = f"환율:{fx_report}, 나스닥:{nq_report}, BTC:{btc_report}, 코스피:{ks_report}"
        ai_briefing = get_ai_analysis(market_summary)

        return (
            f"📊 **{now_seoul.strftime('%m/%d')} AI 통합 리포트**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💵 **환율:** {fx_report}\n"
            f"🇺🇸 **나스닥:** {nq_report}\n"
            f"🐳 **BTC:** {btc_report}\n"
            f"🇰🇷 **코스피:** {ks_report}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🤖 **AI 비서 브리핑**\n\n"
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
    
