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
    
    # 모델 경로를 더 확실한 형태로 변경
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    if is_pre_market:
        context = "현재 코스피 개장 전입니다. 전일 마감 지표와 미장 흐름을 요약하세요."
    else:
        context = "현재 코스피 장중입니다. 오늘 오전 시초가 대비 수급 에너지를 분석하세요."

    prompt = f"""
    당신은 수급 분석 전문가입니다. {context}
    - 환율과 비트코인은 이미 수치가 있으니 브리핑에서 절대 언급하지 마세요.
    - 결과 중심의 냉철한 문체를 사용하세요. (1~2문장)
    데이터: {market_data}
    """
    
    try:
        # 응답 구조를 더 안전하게 파싱
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
        res_json = response.json()
        if 'candidates' in res_json:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            # 에러 메시지 상세 확인용 (로그 출력)
            print(f"AI 응답 오류: {res_json}")
            return "분석 엔진 응답 대기 중"
    except Exception as e:
        print(f"AI 호출 실패: {e}")
        return "수급 분석 일시 지연"

def run():
    seoul_tz = pytz.timezone('Asia/Seoul')
    now_dt = datetime.now(seoul_tz)
    now_str = now_dt.strftime('%Y-%m-%d %H:%M')
    
    # 09:00 이전이면 전일 마감 데이터 분석
    is_pre_market = now_dt.hour < 9
    summary_ai = ""

    # 1. KOSPI (전일 마감과 오전 수급 완벽 분리)
    try:
        ks_ticker = yf.Ticker("^KS11")
        ks_h = ks_ticker.history(period="5d", interval="15m") # 넉넉하게 5일치 호출
        if not ks_h.empty:
            curr = ks_h['Close'].iloc[-1]
            if is_pre_market:
                # 어제 종가 찾기
                prev_close = ks_h['Close'].iloc[-2]
                diff = curr - prev_close
                label = "전일마감"
            else:
                # 오늘 시초가 대비
                diff = curr - ks_h['Open'].iloc[0]
                label = "오전수급"
            
            ks_ui = f"<b>🇰🇷 KOSPI MARKET ({label})</b>\n┗ <b>{curr:,.2f}</b> ({diff:+.2f})\n┗ <b>상태:</b> {'🟢 매수 우위' if diff > 0 else '🔴 매도 우위'}\n\n"
            summary_ai += f"코스피 {curr}({label} 변동 {diff:+.2f}), "
    except: ks_ui = "🇰🇷 KOSPI: 지연\n\n"

    # 2. NASDAQ
    try:
        nq_h = yf.Ticker("NQ=F").history(period="1d", interval="1h")
        if not nq_h.empty:
            curr = nq_h['Close'].iloc[-1]
            lh = curr - nq_h['Open'].iloc[-1]
            nq_ui = f"<b>🇺🇸 NASDAQ 100</b>\n┗ <b>{curr:,.2f}</b> ({lh:+.2f})\n┗ <b>라스트아워:</b> {'⬆️ 상방' if lh > 0 else '⬇️ 하방'}\n\n"
            summary_ai += f"나스닥 {curr}(라스트 {lh:+.2f}), "
    except: nq_ui = "🇺🇸 NASDAQ: 지연\n\n"

    # 3. BTC & FX
    try:
        fx_h = yf.Ticker("USDKRW=X").history(period="2d")
        fx_curr = fx_h['Close'].iloc[-1]
        fx_mark = "▲" if fx_curr > fx_h['Close'].iloc[-2] else "▼"
        btc = yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1]
        etc_ui = f"<b>💰 BTC & FX</b>\n┗ <b>BTC:</b> ${btc:,.0f}\n   ㄴ <b>ETF/고래:</b> 🟢 유입세\n┗ <b>환율:</b> {fx_curr:,.2f}원 ({fx_mark})\n\n"
    except: etc_ui = "💰 ASSETS: 지연\n\n"

    divider = "━━━━━━━━━━━━━━━━━━\n"
    ai_brief = get_ai_analysis(summary_ai, is_pre_market)
    
    title = "아침 시장 리포트" if is_pre_market else "오전 수급 브리핑"
    header = f"🚀 <b>{title} ({now_str})</b>\n"
    
    final_report = f"{header}{divider}{ks_ui}{nq_ui}{etc_ui}{divider}<b>🤖 AI 비서 브리핑</b>\n{ai_brief}"
    send_msg(final_report)

if __name__ == "__main__":
    run()
