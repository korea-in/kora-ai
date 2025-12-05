"""
종합 보고서 생성 서비스

모든 데이터 소스(DART, News, KRX)를 통합하여
GPT-4o에 전송하고 구조화된 분석 보고서를 생성
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# 환경 변수 로드
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

# KRX 서비스
from app.services.krx.stock_service import (
    get_current_price,
    get_stock_summary,
    get_yearly_trend,
    get_moving_averages,
    get_volume_trend,
    get_valuation,
    calculate_rsi,
    calculate_mfi,
    get_price_history
)

# Naver 뉴스 서비스
from app.services.naver.news_service import search_company_news

# DART 서비스
from app.services.dart.get_company import get_company_info
from app.services.dart.get_financial_index import fetch_all_financial_index
from app.services.dart.get_financials import fetch_financials_auto
from app.services.dart.get_dividend import get_dividend_info as fetch_dividend
from app.services.dart.get_disclosure_list import get_regular_reports as fetch_disclosure_list

# OpenAI 서비스
from app.services.openai.analysis_service import chat_completion_json


def collect_all_data(
    company_name: str,
    ticker: str,
    corp_code: str,
    year: str = None
) -> Dict[str, Any]:
    """
    기업의 모든 데이터 수집
    
    Args:
        company_name: 기업명
        ticker: 종목코드 (6자리)
        corp_code: DART 고유번호 (8자리)
        year: 사업연도 (기본: 전년도)
        
    Returns:
        통합 데이터 딕셔너리
    """
    if year is None:
        year = str(datetime.now().year - 1)
    
    result = {
        "company_name": company_name,
        "ticker": ticker,
        "corp_code": corp_code,
        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "krx": {},
        "dart": {},
        "news": {},
        "errors": []
    }
    
    # ============================================
    # 1. KRX 주가 데이터 수집
    # ============================================
    try:
        # 현재가
        current = get_current_price(ticker)
        if current:
            result["krx"]["current_price"] = current.to_dict()
        
        # 종합 요약
        summary = get_stock_summary(ticker)
        if summary:
            result["krx"]["summary"] = summary.to_dict()
        
        # 1년 추이
        yearly = get_yearly_trend(ticker)
        if yearly:
            result["krx"]["yearly_trend"] = yearly
        
        # 이동평균
        ma = get_moving_averages(ticker)
        if ma:
            result["krx"]["moving_averages"] = ma
        
        # 거래량
        volume = get_volume_trend(ticker, days=60)
        if volume:
            result["krx"]["volume_trend"] = {
                "avg_volume": volume.get("avg_volume"),
                "latest_volume": volume.get("latest_volume"),
                "volume_surge": volume.get("volume_surge")
            }
        
        # 밸류에이션
        valuation = get_valuation(ticker)
        if valuation:
            result["krx"]["valuation"] = valuation
        
        # RSI
        rsi = calculate_rsi(ticker)
        if rsi:
            result["krx"]["rsi"] = rsi
        
        # MFI
        mfi = calculate_mfi(ticker)
        if mfi:
            result["krx"]["mfi"] = mfi
        
        # 1년 가격 히스토리 (차트용)
        history = get_price_history(ticker, days=365)
        if history:
            result["krx"]["price_history"] = [
                {"date": h.date, "close": h.close, "volume": h.volume}
                for h in history
            ]
            
    except Exception as e:
        result["errors"].append(f"KRX 데이터 수집 오류: {str(e)}")
    
    # ============================================
    # 2. DART 공시/재무 데이터 수집
    # ============================================
    if corp_code:  # corp_code가 있는 경우에만 DART 데이터 수집
        try:
            # 기업 개황
            company_info = get_company_info(corp_code)
            if company_info:
                result["dart"]["company_info"] = company_info
            
            # 주요 재무지표 (수익성, 안정성, 성장성, 활동성)
            financial_index = fetch_all_financial_index(corp_code, year, "11011")
            if financial_index:
                result["dart"]["financial_index"] = financial_index
            
            # 전체 재무제표
            financials, fs_type = fetch_financials_auto(corp_code, year, "11011")
            if financials:
                # 주요 계정만 추출
                key_accounts = extract_key_accounts(financials)
                result["dart"]["financials"] = {
                    "type": fs_type,
                    "year": year,
                    "key_accounts": key_accounts
                }
            
            # 배당 정보
            dividend = fetch_dividend(corp_code, year, "11011")
            if dividend:
                result["dart"]["dividend"] = dividend
            
            # 최근 공시 목록
            disclosures = fetch_disclosure_list(corp_code)
            if disclosures:
                result["dart"]["disclosures"] = disclosures[:10]  # 최근 10개
                
        except Exception as e:
            result["errors"].append(f"DART 데이터 수집 오류: {str(e)}")
    else:
        result["errors"].append("DART corp_code가 없어 공시/재무 데이터를 수집하지 못했습니다.")
    
    # ============================================
    # 3. 뉴스 데이터 수집 (LLM용 15개, 표시용 5개)
    # ============================================
    try:
        news_result = search_company_news(company_name, display=15)  # LLM 분석용 15개
        if news_result and news_result.success:
            all_news = [
                {
                    "title": item.clean_title,
                    "description": item.clean_description,
                    "link": item.link,
                    "pub_date": item.pub_date,
                    "source": item.source
                }
                for item in news_result.items
            ]
            result["news"]["total"] = news_result.total
            result["news"]["items"] = all_news[:5]  # 표시용 5개
            result["news"]["items_for_analysis"] = all_news  # LLM 분석용 전체 15개
    except Exception as e:
        result["errors"].append(f"뉴스 데이터 수집 오류: {str(e)}")
    
    return result


def extract_key_accounts(financials: List[Dict]) -> Dict[str, Any]:
    """재무제표에서 주요 계정 추출"""
    key_items = [
        "자산총계", "부채총계", "자본총계",
        "매출액", "영업이익", "당기순이익",
        "영업활동현금흐름", "투자활동현금흐름", "재무활동현금흐름",
        "유동자산", "유동부채", "비유동부채"
    ]
    
    result = {}
    for item in financials:
        account_name = item.get("account_nm", "")
        if any(key in account_name for key in key_items):
            result[account_name] = {
                "current": item.get("thstrm_amount"),
                "previous": item.get("frmtrm_amount"),
                "before_previous": item.get("bfefrmtrm_amount")
            }
    
    return result


def generate_full_report(
    company_name: str,
    ticker: str,
    corp_code: str
) -> Optional[Dict[str, Any]]:
    """
    종합 보고서 생성 (데이터 수집 + AI 분석)
    
    Returns:
        완전한 보고서 데이터 딕셔너리
    """
    # 1. 모든 데이터 수집
    all_data = collect_all_data(company_name, ticker, corp_code)
    
    # 2. GPT-4o 분석 요청
    analysis = request_ai_analysis(all_data)
    
    # 3. 결과 통합
    report = {
        "meta": {
            "company_name": company_name,
            "ticker": ticker,
            "corp_code": corp_code,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data_errors": all_data.get("errors", [])
        },
        "raw_data": all_data,
        "ai_analysis": analysis
    }
    
    return report


def request_ai_analysis(all_data: Dict[str, Any]) -> Optional[Dict]:
    """GPT-4o에 전체 데이터 기반 분석 요청"""
    
    system_prompt = """당신은 KORA AI의 수석 증권 애널리스트입니다.
제공된 모든 데이터(주가, 재무제표, 공시, 뉴스)를 종합 분석하여 
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트 없이 JSON만 출력하세요.

{
    "fair_price": 적정주가(숫자, 원 단위),
    "fair_price_reason": "적정주가 산출 근거 (PER, PBR, 성장성 등 기반, 3문장)",
    "current_vs_fair": "저평가/적정/고평가",
    
    "investment_score": 투자점수(0~100),
    "investment_grade": "A+/A/B+/B/C/D/F 중 하나",
    "investment_opinion": "적극매수/매수/중립/매도/적극매도 중 하나",
    
    "news_analysis": {
        "overall_score": 전체감성점수(0~100),
        "overall_sentiment": "긍정/중립/부정",
        "top_news": [
            {
                "title": "뉴스 제목",
                "sentiment": "긍정/중립/부정",
                "score": 점수(0~100),
                "summary": "핵심 요약 (1문장)"
            }
        ]
    },
    
    "financial_health": {
        "score": 재무건전성점수(0~100),
        "grade": "A/B/C/D/F",
        "summary": "재무 건전성 요약 (2문장)"
    },
    
    "growth_potential": {
        "score": 성장성점수(0~100),
        "grade": "A/B/C/D/F",
        "summary": "성장 가능성 요약 (2문장)"
    },
    
    "profitability": {
        "score": 수익성점수(0~100),
        "grade": "A/B/C/D/F",
        "summary": "수익성 요약 (2문장)"
    },
    
    "evaluation_summary": "종합 평가 요약 (5문장 이내, 투자자 관점)",
    
    "detail_key_list": ["재무건전성", "성장성", "수익성", "시장평가", "기술적분석", "뉴스동향", "리스크"],
    "detail_evaluations": {
        "재무건전성": "상세 분석 (부채비율, 유동비율, 현금흐름 등)",
        "성장성": "상세 분석 (매출/이익 성장률, 투자 계획 등)",
        "수익성": "상세 분석 (ROE, ROA, 영업이익률 등)",
        "시장평가": "상세 분석 (PER, PBR 업종 대비 등)",
        "기술적분석": "상세 분석 (RSI, MFI, 이동평균 등)",
        "뉴스동향": "상세 분석 (주요 이슈, 시장 반응 등)",
        "리스크": "주요 리스크 요인 (3가지 이상)"
    },
    
    "price_forecast": {
        "3month": 3개월후예상가(숫자),
        "6month": 6개월후예상가(숫자),
        "12month": 12개월후예상가(숫자),
        "confidence": "높음/중간/낮음",
        "disclaimer": "본 예측은 참고용이며 투자 결정의 책임은 투자자에게 있습니다."
    }
}

점수 기준:
- 80점 이상: 매우 우수 (A)
- 60~79점: 우수 (B) 
- 40~59점: 보통 (C)
- 20~39점: 주의 (D)
- 20점 미만: 위험 (F)"""

    # 데이터 요약 (토큰 절약)
    user_content = format_data_for_gpt(all_data)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    result = chat_completion_json(messages, temperature=0.4, max_tokens=3500)
    
    return result


def format_data_for_gpt(all_data: Dict[str, Any]) -> str:
    """GPT 전송용 데이터 포맷팅"""
    
    company_name = all_data.get("company_name", "")
    ticker = all_data.get("ticker", "")
    
    # KRX 데이터
    krx = all_data.get("krx", {})
    current = krx.get("current_price", {})
    summary = krx.get("summary", {})
    valuation = krx.get("valuation", {})
    rsi = krx.get("rsi", {})
    mfi = krx.get("mfi", {})
    ma = krx.get("moving_averages", {})
    yearly = krx.get("yearly_trend", {})
    
    # DART 데이터
    dart = all_data.get("dart", {})
    company_info = dart.get("company_info", {})
    financial_index = dart.get("financial_index", {})
    financials = dart.get("financials", {})
    dividend = dart.get("dividend", [])
    disclosures = dart.get("disclosures", [])
    
    # 뉴스 데이터
    news = all_data.get("news", {})
    news_items = news.get("items", [])
    
    content = f"""## {company_name} ({ticker}) 종합 분석 요청

### 📊 주가 현황
- 현재가: {current.get('close', 'N/A'):,}원
- 등락률: {current.get('change_rate', 'N/A')}%
- 52주 최고: {yearly.get('high_price', 'N/A'):,}원
- 52주 최저: {yearly.get('low_price', 'N/A'):,}원
- 52주 수익률: {yearly.get('total_return', 'N/A')}%

### 📈 이동평균선
- 5일: {ma.get('current', {}).get('ma5', 'N/A'):,}원
- 20일: {ma.get('current', {}).get('ma20', 'N/A'):,}원
- 60일: {ma.get('current', {}).get('ma60', 'N/A'):,}원
- 120일: {ma.get('current', {}).get('ma120', 'N/A'):,}원
- 추세: {ma.get('trend', 'N/A')}

### 🔬 기술적 지표
- RSI(14): {rsi.get('value', 'N/A')} ({rsi.get('signal', 'N/A')})
- MFI(14): {mfi.get('value', 'N/A')} ({mfi.get('signal', 'N/A')})

### 💰 밸류에이션
- PER: {valuation.get('per', 'N/A')}배
- PBR: {valuation.get('pbr', 'N/A')}배
- EPS: {valuation.get('eps', 'N/A'):,}원
- BPS: {valuation.get('bps', 'N/A'):,}원
- 배당수익률: {valuation.get('div_yield', 'N/A')}%

### 🏢 기업 개요
- 회사명: {company_info.get('corp_name', company_name)}
- 대표자: {company_info.get('ceo_nm', 'N/A')}
- 업종: {company_info.get('induty_code', 'N/A')}
- 설립일: {company_info.get('est_dt', 'N/A')}
- 상장일: {company_info.get('stock_lst_dt', 'N/A')}
- 홈페이지: {company_info.get('hm_url', 'N/A')}

### 📋 재무지표
"""
    
    # 재무지표 추가
    for category, items in financial_index.items():
        if items:
            content += f"\n[{category}]\n"
            for item in items[:5]:  # 각 카테고리 최대 5개
                idx_name = item.get('idx_nm', '')
                idx_val = item.get('idx_val', '')
                content += f"- {idx_name}: {idx_val}\n"
    
    # 주요 재무제표 계정
    key_accounts = financials.get("key_accounts", {})
    if key_accounts:
        content += "\n### 📊 주요 재무제표 계정\n"
        for account, values in list(key_accounts.items())[:10]:
            current_val = values.get("current", "N/A")
            content += f"- {account}: {current_val}\n"
    
    # 배당 정보
    if dividend:
        content += "\n### 💵 배당 정보\n"
        for div in dividend[:3]:
            content += f"- {div.get('se', '')}: {div.get('thstrm', '')}원\n"
    
    # 최근 공시
    if disclosures:
        content += "\n### 📢 최근 공시\n"
        for disc in disclosures[:5]:
            content += f"- [{disc.get('rcept_dt', '')}] {disc.get('report_nm', '')}\n"
    
    # 뉴스
    if news_items:
        content += f"\n### 📰 최근 뉴스 ({len(news_items)}건)\n"
        for news_item in news_items[:7]:
            content += f"- {news_item.get('title', '')}\n"
            content += f"  요약: {news_item.get('description', '')[:100]}...\n"
    
    content += "\n\n위 데이터를 종합 분석하여 JSON 형식으로 응답해주세요."
    
    return content


# ============================================
# 테스트
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("종합 보고서 생성 테스트")
    print("=" * 60)
    
    # 신한금융지주 테스트
    company_name = "신한금융지주"
    ticker = "055550"
    corp_code = "00382199"
    
    print(f"\n[1] 데이터 수집: {company_name}")
    all_data = collect_all_data(company_name, ticker, corp_code)
    
    print(f"\n수집 완료!")
    print(f"- KRX 데이터: {len(all_data.get('krx', {}))}개 항목")
    print(f"- DART 데이터: {len(all_data.get('dart', {}))}개 항목")
    print(f"- 뉴스: {len(all_data.get('news', {}).get('items', []))}건")
    print(f"- 오류: {all_data.get('errors', [])}")
    
    print("\n[2] AI 분석 요청 중...")
    # analysis = request_ai_analysis(all_data)
    # print(json.dumps(analysis, ensure_ascii=False, indent=2))

