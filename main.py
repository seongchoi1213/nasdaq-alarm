import yfinance as yf
import requests
import os
from datetime import datetime
import pytz

def send_msg(text):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except: pass

def get_ai_analysis(market_data, is_pre_market):
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key: return "API 키 설정 확인 필요"
    
    # [시뮬레이션 반영] 가장 범용적인 정식 v1 경로와 표준 모델명 사용
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
    당신은 전문 주식 분석가입니다. 아래 데이터를 기반으로 시장 수급을 1~2문장으로 요약하세요.
    1. 환율, 비트코인 수치는 이미 리포트에 있으니 절대 언급하지 마세요.
    2. 나스닥 라스트아워와 코스피 수급(전일 또는 오전)의 연결 고리만 냉철하게 분석하세요.
    데이터: {market_data}
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, json=payload, timeout=15)
        res_json = response.json()
        
        # 정상적인 텍스트 추출 시도
        if 'candidates' in res_json and res_json['candidates']:
            return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            # 상세 에러 메시지가 있을 경우 출력하여 디버깅 지원
            error_info = res_json.get('error', {}).get('message', '알 수 없는 응답 구조')
            return f"수급 분석 일시 지연 (사유: {error_info})"
    except Exception as e:
        return f"연결 오류 발생 ({str(e)})"

def run():
    # 1. 시간대 설정
    seoul_tz = pytz.timezone('Asia/Seoul')
    now_dt = datetime.now(seoul_tz)
    now_str = now_dt.strftime('%Y-%m-%d %H:%M')
    
    # 오전 9시 개장 여부 판단
    is_pre_market = now_dt.hour < 9
    summary_ai = ""

    # 2. KOSPI 데이터 수집 (지능형 분기)
    try:
        ks_ticker = yf.Ticker("^KS11")
        ks_h = ks_ticker.history(period="5d", interval="15m")
        if not ks_h.empty:
            curr = ks_h['Close'].iloc[-1]
            if is_pre_market:
                # 개장 전: 전일 종가와 비교
                prev_close = ks_h['Close'].iloc[-2]
                diff = curr - prev_close
                label = "전일마감"
            else:
                # 개장 후: 오늘 시초가와 비교
                diff = curr - ks_h['Open'].iloc[0]
                label = "오전수급"
            
            ks_ui = f"<b>🇰🇷 KOSPI MARKET ({label})</b>\n┗ <b>{curr:,.2f}</b> ({diff:+.2f})\n┗ <b>상태:</b> {'🟢 매수 우위' if diff > 0 else '🔴 매도 우위'}\n\n"
            summary_ai += f"코스피 {curr}({label} {diff:+.2f}), "
    except: ks_ui = "🇰🇷 KOSPI: 데이터 지연\n\n"

    # 3. NASDAQ 데이터 수집 (최신 미장)
    try:
        nq_h = yf.Ticker("NQ=F").history(period="1d", interval="1h")
        if not nq_h.empty:
            nq_curr = nq_h['Close'].iloc[-1]
            nq_lh = nq_curr - nq_h['Open'].iloc[-1]
            nq_ui = f"<b>🇺🇸 NASDAQ 100</b>\n┗ <b>{nq_curr:,.2f}</b> ({nq_lh:+.2f})\n┗ <b>라스트아워:</b> {'⬆️ 상방' if nq_lh > 0 else '⬇️ 하방'}\n\n"
            summary_ai += f"나스닥 {nq_curr}(라스트 {nq_lh:+.2f}), "
    except: nq_ui = "🇺🇸 NASDAQ: 데이터 지연\n\n"

    # 4. 기타 자산 (BTC & 환율)
    try:
        fx_h = yf.Ticker("USDKRW=X").history(period="2d")
        fx_curr = fx_h['Close'].iloc[-1]
        fx_mark = "▲" if fx_curr > fx_h['Close'].iloc[-2] else "▼"
        btc = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        etc_ui = f"<b>💰 BTC & FX</b>\n┗ <b>BTC:</b> ${btc:,.0f}\n   ㄴ <b>ETF/고래:</b> 🟢 유입세\n┗ <b>환율:</b> {fx_curr:,.2f}원 ({fx_mark})\n\n"
    except: etc_ui = "💰 ASSETS: 데이터 지연\n\n"

    # 5. 리포트 조립 및 전송
    ai_brief = get_ai_analysis(summary_ai, is_pre_market)
    
    title = "아침 시장 리포트" if is_pre_market else "오전 수급 브리핑"
    header = f"🚀 <b>{title} ({now_str})</b>\n"
    divider = "━━━━━━━━━━━━━━━━━━\n"
    
    final_report = f"{header}{divider}{ks_ui}{nq_ui}{etc_ui}{divider}<b>🤖 AI 비서 브리핑</b>\n{ai_brief}"
    send_msg(final_report)

if __name__ == "__main__":
    run()
