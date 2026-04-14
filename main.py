import yfinance as yf
import requests
import os
from datetime import datetime
import pytz
import google.generativeai as genai

# 1. 텔레그램 전송 함수 (안정성 최우선)
def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat_id: return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    
    try:
        res = requests.post(url, json=payload)
        print(f"📡 전송 결과: {res.status_code}")
    except Exception as e:
        print(f"❌ 전송 오류: {e}")

# 2. AI 분석 함수 (문문제를 일으킨 RequestOptions 삭제)
def get_ai_analysis(market_data):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key: return "API 키 미설정"
    
    try:
        genai.configure(api_key=api_key)
        # 모델 선언 방식을 가장 기본으로 변경
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"투자 분석가로서 다음 지표를 바탕으로 오늘의 전략을 기호 없이 짧게 분석해줘: {market_data}"
        
        # 복잡한 옵션 없이 기본 호출
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text
        return "AI 코멘트 생성 불가"
    except Exception as e:
        # 에러 발생 시 구형 모델로 한 번 더 시도하는 보험 추가
        try:
            model_alt = genai.GenerativeModel('gemini-pro')
            return model_alt.generate_content(prompt).text
        except:
            return f"AI 분석 실패: {str(e)}"

# 3. 메인 실행 로직
def run():
    seoul_tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(seoul_tz).strftime('%Y-%m-%d %H:%M')
    
    report = f"📊 [마켓 리포트 {now}]\n\n"
    market_summary = ""
    
    # 데이터 수집 (안전하게 처리)
    try:
        fx_ticker = yf.Ticker("USDKRW=X")
        fx = fx_ticker.history(period="1d")['Close'].iloc[-1]
        report += f"💵 환율: {fx:,.2f}원\n"
        market_summary += f"환율 {fx}원, "
    except: report += "💵 환율: 수집지연\n"

    try:
        nq_ticker = yf.Ticker("NQ=F")
        nq = nq_ticker.history(period="1d")['Close'].iloc[-1]
        report += f"🇺🇸 나스닥: {nq:,.2f}\n"
        market_summary += f"나스닥 {nq}, "
    except: report += "🇺🇸 나스닥: 수집지연\n"

    # AI 브리핑 추가
    report += "\n🤖 [AI 비서 브리핑]\n"
    report += get_ai_analysis(market_summary)

    # 최종 전송
    send_msg(report)

if __name__ == "__main__":
    run()
