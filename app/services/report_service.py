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
from app.services.dart.get_stock_info import get_stock_total_qty

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
                # 업종코드를 업종명으로 변환
                induty_code = company_info.get('induty_code', '')
                if induty_code:
                    from app.utils.industry_mapper import get_industry_fast
                    company_info['induty_name'] = get_industry_fast(induty_code)
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
            
            # 주식의 총수 현황 (BPS 계산용)
            stock_info = get_stock_total_qty(corp_code, year, "11011")
            if stock_info:
                result["dart"]["stock_info"] = stock_info
                print(f"[DART] 주식수 조회 완료: {stock_info.get('total_shares')}")
            else:
                print(f"[DART] 주식수 조회 실패")
            
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
    
    # ============================================
    # 4. 재무 데이터 보완 (ROA, ROE 등 계산)
    # ============================================
    try:
        result = enrich_financial_data(result)
    except Exception as e:
        result["errors"].append(f"재무 지표 계산 오류: {str(e)}")
    
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


def calculate_financial_ratios(key_accounts: Dict[str, Any]) -> Dict[str, Any]:
    """
    재무제표 데이터에서 주요 재무 비율 계산
    ROA, ROE, 부채비율, 유동비율, 당좌비율, 이자보상배율 등
    """
    ratios = {}
    
    def parse_amount(value):
        """금액 문자열을 숫자로 변환"""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return value
        try:
            # 쉼표 제거 후 변환
            return float(str(value).replace(',', ''))
        except:
            return None
    
    # 주요 계정 추출
    total_assets = None
    total_liabilities = None
    total_equity = None
    net_income = None
    operating_income = None
    revenue = None
    current_assets = None
    current_liabilities = None
    inventory = None
    interest_expense = None
    receivables = None
    
    for account_name, values in key_accounts.items():
        current_val = parse_amount(values.get('current'))
        
        if '자산총계' in account_name:
            total_assets = current_val
        elif '부채총계' in account_name:
            total_liabilities = current_val
        elif '자본총계' in account_name:
            total_equity = current_val
        elif '당기순이익' in account_name:
            net_income = current_val
        elif '영업이익' in account_name:
            operating_income = current_val
        elif '매출액' in account_name or '영업수익' in account_name:
            if revenue is None:  # 첫 번째 매출 관련 계정 사용
                revenue = current_val
        elif '유동자산' in account_name:
            current_assets = current_val
        elif '유동부채' in account_name:
            current_liabilities = current_val
        elif '재고자산' in account_name:
            inventory = current_val
        elif '이자비용' in account_name or '금융비용' in account_name or '금융원가' in account_name:
            if interest_expense is None:  # 첫 번째 이자 관련 계정 사용
                interest_expense = current_val
        elif '매출채권' in account_name or '매출채권및기타채권' in account_name or '수취채권' in account_name:
            if receivables is None:  # 첫 번째 매출채권 관련 계정 사용
                receivables = current_val
    
    # ROA (총자산순이익률) = 당기순이익 / 총자산 × 100
    if total_assets and net_income and total_assets != 0:
        ratios['ROA'] = round((net_income / total_assets) * 100, 2)
    
    # ROE (자기자본순이익률) = 당기순이익 / 자기자본 × 100
    if total_equity and net_income and total_equity != 0:
        ratios['ROE'] = round((net_income / total_equity) * 100, 2)
    
    # 부채비율 = 부채총계 / 자본총계 × 100
    if total_equity and total_liabilities and total_equity != 0:
        ratios['debt_ratio'] = round((total_liabilities / total_equity) * 100, 2)
    
    # 자기자본비율 = 자본총계 / 자산총계 × 100
    if total_assets and total_equity and total_assets != 0:
        ratios['equity_ratio'] = round((total_equity / total_assets) * 100, 2)
    
    # 유동비율 = 유동자산 / 유동부채 × 100
    if current_assets and current_liabilities and current_liabilities != 0:
        ratios['current_ratio'] = round((current_assets / current_liabilities) * 100, 2)
    
    # 당좌비율 = (유동자산 - 재고자산) / 유동부채 × 100
    if current_assets and current_liabilities and current_liabilities != 0:
        inv = inventory or 0
        ratios['quick_ratio'] = round(((current_assets - inv) / current_liabilities) * 100, 2)
    
    # 이자보상배율 = 영업이익 / 이자비용
    if operating_income and interest_expense and interest_expense != 0:
        ratios['interest_coverage'] = round(operating_income / interest_expense, 2)
    
    # 영업이익률 = 영업이익 / 매출액 × 100
    if revenue and operating_income and revenue != 0:
        ratios['operating_margin'] = round((operating_income / revenue) * 100, 2)
    
    # 순이익률 = 당기순이익 / 매출액 × 100
    if revenue and net_income and revenue != 0:
        ratios['net_profit_margin'] = round((net_income / revenue) * 100, 2)
    
    # 총자산회전율 = 매출액 / 총자산
    if revenue and total_assets and total_assets != 0:
        ratios['asset_turnover'] = round(revenue / total_assets, 2)
    
    # 매출채권회전율 = 매출액 / 매출채권
    if revenue and receivables and receivables != 0:
        ratios['receivable_turnover'] = round(revenue / receivables, 2)
    
    # 순이익률 = 당기순이익 / 매출액 × 100
    if revenue and net_income and revenue != 0:
        ratios['net_margin'] = round((net_income / revenue) * 100, 2)
    
    # 자기자본비율 = 자본총계 / 자산총계 × 100
    if total_assets and total_equity and total_assets != 0:
        ratios['equity_ratio'] = round((total_equity / total_assets) * 100, 2)
    
    return ratios


def enrich_financial_data(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    재무 데이터가 없거나 불완전한 경우 계산으로 보완
    """
    dart_data = result.get("dart", {})
    krx_data = result.get("krx", {})
    
    # 재무제표 기반 지표 계산
    if dart_data.get("financials", {}).get("key_accounts"):
        calculated_ratios = calculate_financial_ratios(
            dart_data["financials"]["key_accounts"]
        )
        
        # 기존 financial_index에 계산된 지표 추가/보완
        if "financial_index" not in dart_data:
            dart_data["financial_index"] = {}
        
        if "calculated_ratios" not in dart_data:
            dart_data["calculated_ratios"] = calculated_ratios
        
        # ROA가 없으면 계산된 값 사용
        if calculated_ratios.get("ROA") is not None:
            if not dart_data.get("financial_index", {}).get("profitability", {}).get("ROA"):
                if "profitability" not in dart_data.get("financial_index", {}):
                    dart_data["financial_index"]["profitability"] = {}
                dart_data["financial_index"]["profitability"]["ROA (계산)"] = f"{calculated_ratios['ROA']}%"
        
        # ROE가 없으면 계산된 값 사용
        if calculated_ratios.get("ROE") is not None:
            if not dart_data.get("financial_index", {}).get("profitability", {}).get("ROE"):
                if "profitability" not in dart_data.get("financial_index", {}):
                    dart_data["financial_index"]["profitability"] = {}
                dart_data["financial_index"]["profitability"]["ROE (계산)"] = f"{calculated_ratios['ROE']}%"
        
        # 부채비율이 없으면 계산된 값 사용
        if calculated_ratios.get("debt_ratio") is not None:
            if not dart_data.get("financial_index", {}).get("stability", {}).get("부채비율"):
                if "stability" not in dart_data.get("financial_index", {}):
                    dart_data["financial_index"]["stability"] = {}
                dart_data["financial_index"]["stability"]["부채비율 (계산)"] = f"{calculated_ratios['debt_ratio']}%"
    
    # KRX 밸류에이션이 없거나 불완전한 경우 DART 데이터로 계산
    valuation = krx_data.get("valuation", {})
    current_price_data = krx_data.get("current_price", {})
    current_price = current_price_data.get("close") if current_price_data else None
    
    # PER, PBR이 없으면 DART 데이터로 계산 시도
    if (not valuation or valuation.get("per") is None or valuation.get("pbr") is None) and current_price:
        if not valuation:
            valuation = {}
        
        dividend_data = dart_data.get("dividend", [])
        key_accounts = dart_data.get("financials", {}).get("key_accounts", {})
        
        # 방법 1: 배당 데이터에서 EPS 직접 가져오기
        eps_from_dividend = None
        for item in dividend_data:
            se = item.get("se", "")
            thstrm = item.get("thstrm", "")
            if "(연결)주당순이익(원)" in se or "주당순이익(원)" in se:
                if thstrm and thstrm != "-":
                    try:
                        eps_from_dividend = int(thstrm.replace(",", ""))
                        break
                    except:
                        pass
        
        # EPS가 있으면 PER 계산
        if eps_from_dividend and eps_from_dividend > 0:
            valuation["eps"] = eps_from_dividend
            valuation["per"] = round(current_price / eps_from_dividend, 2)
        
        # 방법 2: 재무제표에서 BPS 계산
        # BPS = 순자산(자본총계) / 발행주식수
        # key_accounts의 값은 {'current': ..., 'previous': ...} 형태
        print(f"[BPS 계산] 시작 - 현재가: {current_price}")
        
        total_equity_data = None
        total_assets_data = None
        total_liabilities_data = None
        
        for key, val in key_accounts.items():
            if '자본총계' in key:
                if isinstance(val, dict):
                    total_equity_data = val.get('current')
                else:
                    total_equity_data = val
                print(f"[BPS 계산] 자본총계 발견: {key} = {total_equity_data}")
            elif '자산총계' in key:
                if isinstance(val, dict):
                    total_assets_data = val.get('current')
                else:
                    total_assets_data = val
                print(f"[BPS 계산] 자산총계 발견: {key} = {total_assets_data}")
            elif '부채총계' in key:
                if isinstance(val, dict):
                    total_liabilities_data = val.get('current')
                else:
                    total_liabilities_data = val
                print(f"[BPS 계산] 부채총계 발견: {key} = {total_liabilities_data}")
        
        # 문자열인 경우 숫자로 변환
        def parse_value(v):
            if v is None:
                return None
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str):
                try:
                    return float(v.replace(',', ''))
                except:
                    return None
            return None
        
        total_equity_data = parse_value(total_equity_data)
        total_assets_data = parse_value(total_assets_data)
        total_liabilities_data = parse_value(total_liabilities_data)
        
        print(f"[BPS 계산] 파싱 후 - 자본총계: {total_equity_data}, 자산총계: {total_assets_data}, 부채총계: {total_liabilities_data}")
        
        # 자본총계가 없으면 자산총계 - 부채총계로 계산
        if total_equity_data is None and total_assets_data and total_liabilities_data:
            total_equity_data = total_assets_data - total_liabilities_data
            print(f"[BPS 계산] 자본총계 계산: {total_assets_data} - {total_liabilities_data} = {total_equity_data}")
        
        summary = krx_data.get("summary", {})
        market_cap = summary.get("market_cap") if summary else None
        print(f"[BPS 계산] 시가총액: {market_cap}")
        
        # 발행주식수 계산 방법 1: 시가총액 / 현재가
        shares = None
        if market_cap and current_price > 0:
            shares = market_cap / current_price
            print(f"[BPS 계산] 주식수 (시가총액/현재가): {shares:,.0f}")
        
        # 발행주식수 계산 방법 2: DART stock_info에서 조회
        dart_stock_info = dart_data.get("stock_info", {})
        if dart_stock_info and dart_stock_info.get('total_shares'):
            dart_shares = dart_stock_info['total_shares']
            print(f"[BPS 계산] DART 주식수 (캐시): {dart_shares:,.0f}")
            # 시가총액 계산이 안되면 DART 주식수 사용
            if not shares:
                shares = dart_shares
                print(f"[BPS 계산] 시가총액 없음 → DART 주식수 사용: {shares:,.0f}")
        
        # 발행주식수 계산 방법 3: 아직도 없으면 DART API 실시간 조회
        corp_code = result.get("meta", {}).get("corp_code") or dart_data.get("company_info", {}).get("corp_code")
        
        if not shares and corp_code:
            print(f"[BPS 계산] 주식수 없음, DART API 실시간 조회 시도...")
            stock_info = get_stock_total_qty(corp_code)
            if stock_info and stock_info.get('total_shares'):
                shares = stock_info['total_shares']
                print(f"[BPS 계산] DART 주식수 조회 성공: {shares:,.0f}")
            else:
                print(f"[BPS 계산] DART 주식수 조회 실패")
        
        # BPS 및 PBR 계산
        if total_equity_data and total_equity_data > 0:
            if shares and shares > 0:
                bps = total_equity_data / shares
                print(f"[BPS 계산] BPS = {total_equity_data:,.0f} / {shares:,.0f} = {bps:,.0f}")
                if bps > 0:
                    valuation["bps"] = int(bps)
                    valuation["pbr"] = round(current_price / bps, 2)
                    print(f"[BPS 계산] 성공 - BPS: {valuation['bps']}, PBR: {valuation['pbr']}")
            else:
                print(f"[BPS 계산] 실패 - 주식수를 구할 수 없음 (shares={shares})")
        else:
            print(f"[BPS 계산] 실패 - 자본총계를 구할 수 없음 (total_equity={total_equity_data})")
        
        if valuation.get("per") or valuation.get("pbr"):
            valuation["source"] = "DART 데이터 기반 계산"
        
        krx_data["valuation"] = valuation
    
    # 여전히 밸류에이션이 없는 경우 메시지 추가
    if not krx_data.get("valuation") or (krx_data["valuation"].get("per") is None and krx_data["valuation"].get("pbr") is None):
        if not krx_data.get("valuation"):
            krx_data["valuation"] = {}
        krx_data["valuation"]["message"] = "밸류에이션 데이터를 계산할 수 없습니다."
    
    result["dart"] = dart_data
    result["krx"] = krx_data
    
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

## 분석 원칙
1. 기본적 분석(재무제표, 밸류에이션)을 중심으로 분석
2. 뉴스/시장 심리는 참고 자료로 활용
3. 상세 평가는 최소 5문장 이상으로 충분히 설명
4. 모든 판단에는 구체적인 근거 수치를 명시

## ⚠️ 적정주가 산정 규칙 (필수 준수)
적정주가는 반드시 아래 공식으로 계산한 "원" 단위 금액을 반환하세요:
- 일반기업: 적정주가 = EPS × 업종평균PER (예: EPS 5,000원 × PER 12배 = 60,000원)
- 금융업: 적정주가 = BPS × 업종평균PBR (예: BPS 100,000원 × PBR 0.8배 = 80,000원)

❌ 잘못된 예: 0.8, 5, 12 (이것은 배수이지 주가가 아닙니다)
✅ 올바른 예: 80000, 95000, 120000 (이것이 원 단위 적정주가입니다)

{
    "fair_price": 적정주가(정수, 원 단위. 예시: 현재가 80000원이면 → 85000 또는 75000처럼 수만원 단위로 반환),
    "fair_price_reason": "적정주가 산출 근거: EPS/BPS 값과 적용 배수, 계산 과정을 명시 (예: BPS 100,000원 × PBR 0.85배 = 85,000원)",
    "current_vs_fair": "저평가/적정/고평가",
    
    "investment_score": 투자점수(0~100, 기본적분석 70점 + 뉴스분석 30점 배분),
    "investment_grade": "A+/A/B+/B/C/D/F 중 하나",
    "investment_opinion": "적극매수/매수/중립/매도/적극매도 중 하나",
    
    "news_analysis": {
        "overall_score": 전체감성점수(0~100),
        "overall_sentiment": "긍정/중립/부정",
        "summary": "뉴스 분석 요약 (최근 뉴스에서 파악되는 시장 분위기, 주요 이슈, 투자 심리를 3~4문장으로 설명)",
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
        "summary": "재무 건전성 상세 분석. 부채비율, 유동비율, 이자보상배율 등 핵심 지표를 수치와 함께 분석하고, 업종 평균 대비 수준을 평가. 최소 4문장 이상 작성."
    },
    
    "growth_potential": {
        "score": 성장성점수(0~100),
        "grade": "A/B/C/D/F",
        "summary": "성장 가능성 상세 분석. 매출액/영업이익/순이익의 전년 대비 성장률, 향후 성장 동력, 업종 전망을 종합하여 최소 4문장 이상 작성."
    },
    
    "profitability": {
        "score": 수익성점수(0~100),
        "grade": "A/B/C/D/F",
        "summary": "수익성 상세 분석. ROE, ROA, 영업이익률, 순이익률을 수치와 함께 분석하고, 업종 평균 대비 수준과 개선/악화 추세를 평가. 최소 4문장 이상 작성."
    },
    
    "evaluation_summary": "종합 평가 요약. 1) 현재 투자 매력도 평가, 2) 핵심 강점 2가지, 3) 주요 리스크 2가지, 4) 적합한 투자자 유형, 5) 투자 시 유의사항을 포함하여 최소 7문장 이상으로 상세하게 작성. 구체적인 수치와 근거를 반드시 포함.",
    
    "detail_key_list": ["재무건전성", "성장성", "수익성", "시장평가", "기술적분석", "뉴스동향", "리스크"],
    "detail_evaluations": {
        "재무건전성": "상세 분석 (최소 5문장). 부채비율, 유동비율, 당좌비율, 자기자본비율, 이자보상배율 등 각 지표의 수치와 적정 기준 대비 평가를 구체적으로 서술. 현금흐름 상태와 재무구조의 안정성 판단.",
        "성장성": "상세 분석 (최소 5문장). 최근 3년간 매출/영업이익/순이익 성장률 추이, CAGR, 업종 대비 성장 속도, 향후 성장 전망, 성장 드라이버 분석.",
        "수익성": "상세 분석 (최소 5문장). ROE, ROA, 영업이익률, 순이익률의 수치와 업종 평균 대비 수준, 수익성 추세 분석, 원가 구조와 마진 분석.",
        "시장평가": "상세 분석 (최소 5문장). PER, PBR, EV/EBITDA 등 밸류에이션 지표를 업종 평균/경쟁사 대비 비교, 과거 밸류에이션 밴드 대비 현재 위치, 적정 밸류에이션 수준 제시.",
        "기술적분석": "상세 분석 (최소 5문장). RSI, MFI의 현재값과 신호 해석, 이동평균선(5/20/60/120일) 배열과 추세 판단, 52주 고저 대비 현재 위치, 거래량 추이 분석.",
        "뉴스동향": "상세 분석 (최소 5문장). 최근 주요 뉴스의 핵심 내용 요약, 시장 반응 분석, 단기 주가에 미칠 영향 예측, 긍정적/부정적 이슈 구분.",
        "리스크": "주요 리스크 요인 상세 분석 (최소 5문장). 기업 고유 리스크(재무/사업/경영), 산업 리스크, 거시경제 리스크를 구분하여 최소 5가지 이상의 리스크 요인을 구체적으로 설명."
    },
    
    "price_forecast": {
        "3month": 3개월후예상가(숫자, 현재가 대비 ±15% 이내로 보수적 예측),
        "6month": 6개월후예상가(숫자, 현재가 대비 ±20% 이내로 보수적 예측),
        "12month": 12개월후예상가(숫자, 현재가 대비 ±30% 이내로 보수적 예측),
        "confidence": "높음/중간/낮음",
        "basis": "예측 근거 상세 설명. 1) 적용한 밸류에이션 방법, 2) 가정한 성장률, 3) 할인율/프리미엄 적용 이유를 3문장 이상으로 설명",
        "disclaimer": "본 예측은 기본적 분석에 기반한 참고 자료이며, 시장 변동성, 예상치 못한 이벤트 등으로 실제 주가와 크게 다를 수 있습니다. 투자 결정의 책임은 투자자에게 있습니다."
    },
    
    "business_summary": {
        "industry": "업종 분류 (예: 반도체, 금융, 바이오 등 구체적인 업종명과 하위 세그먼트)",
        "main_products": "주력 상품/서비스 (주요 매출원 2~3가지를 구체적으로 설명)",
        "competitors": "주요 경쟁사 (국내외 경쟁사 3~5개 기업명)",
        "market_trend": "시장 동향 (해당 업종의 최근 시장 상황, 성장성, 주요 트렌드를 2~3문장으로 설명)"
    }
}

## 점수 기준
- 80점 이상: 매우 우수 (A)
- 60~79점: 우수 (B) 
- 40~59점: 보통 (C)
- 20~39점: 주의 (D)
- 20점 미만: 위험 (F)

## 주가 예측 가이드라인
- 뉴스의 단기적 영향보다 기본적 분석(재무, 밸류에이션)에 더 큰 가중치 부여
- 과도하게 낙관적이거나 비관적인 예측 지양
- 업종 평균 PER/PBR을 기준으로 산정
- 현재가 대비 ±30%를 초과하는 예측은 특별한 사유가 있는 경우에만

## 주의사항
- fair_price는 반드시 "원" 단위의 실제 주가여야 합니다
- 배수(0.85, 8.5 등)가 아닌 실제 금액(85000, 95000 등)으로 반환"""

    # 데이터 요약 (토큰 절약)
    try:
        user_content = format_data_for_gpt(all_data)
        print(f"[request_ai_analysis] Formatted content length: {len(user_content)} chars")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        print("[request_ai_analysis] Calling OpenAI API...")
        result = chat_completion_json(messages, temperature=0.4, max_tokens=3500)
        
        if result:
            print(f"[request_ai_analysis] Success, got keys: {list(result.keys())[:5]}...")
            
            # 적정주가 유효성 검증 및 보정
            result = validate_fair_price(result, all_data)
        else:
            print("[request_ai_analysis] OpenAI returned None")
        
        return result
        
    except Exception as e:
        print(f"[request_ai_analysis] Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def validate_fair_price(result: Dict, all_data: Dict) -> Dict:
    """적정주가 유효성 검증 및 보정 - 비정상 값만 보정"""
    try:
        fair_price = result.get('fair_price', 0)
        
        # 현재가 가져오기
        krx = all_data.get('krx', {})
        current_price = krx.get('current_price', {}).get('close', 0)
        valuation = krx.get('valuation', {})
        
        if not current_price or current_price <= 0:
            print(f"[validate_fair_price] 현재가 없음, 검증 스킵")
            return result
        
        print(f"[validate_fair_price] 현재가: {current_price:,}원, AI 적정주가: {fair_price}")
        
        bps = valuation.get('bps', 0)
        eps = valuation.get('eps', 0)
        pbr = valuation.get('pbr', 0)
        per = valuation.get('per', 0)
        
        # 적정주가가 현재가의 1% 미만이면 AI가 배수를 주가로 잘못 반환한 것으로 판단
        if fair_price < current_price * 0.01:
            print(f"[validate_fair_price] ⚠️ 적정주가가 비정상적으로 낮음 ({fair_price}). 재계산...")
            
            recalculated = 0
            
            # BPS 기반 계산 (금융업 등)
            if bps and bps > 0:
                # AI가 반환한 값이 PBR 배수일 가능성 (예: 0.85)
                if fair_price > 0 and fair_price < 10:
                    target_pbr = fair_price
                else:
                    target_pbr = 0.8 if pbr and pbr < 1 else 1.0
                recalculated = bps * target_pbr
                print(f"[validate_fair_price] BPS 기반: {bps:,.0f} × {target_pbr:.2f} = {recalculated:,.0f}원")
            
            # EPS 기반 계산
            elif eps and eps > 0:
                target_per = per if per and per > 5 else 10
                recalculated = eps * target_per
                print(f"[validate_fair_price] EPS 기반: {eps:,.0f} × {target_per:.1f} = {recalculated:,.0f}원")
            
            # 재계산 결과 적용
            if recalculated > current_price * 0.3 and recalculated < current_price * 3:
                result['fair_price'] = int(recalculated)
                result['fair_price_reason'] = result.get('fair_price_reason', '') + f" [BPS/EPS 기반 보정]"
                print(f"[validate_fair_price] ✅ 보정 완료: {result['fair_price']:,}원")
            else:
                # 현재가 기준으로 설정
                result['fair_price'] = int(current_price)
                result['fair_price_reason'] = result.get('fair_price_reason', '') + f" [현재가 기준 보정]"
                print(f"[validate_fair_price] ⚠️ 현재가 기준: {result['fair_price']:,}원")
        
        return result
        
    except Exception as e:
        print(f"[validate_fair_price] Error: {e}")
        return result


def format_number(value, suffix=""):
    """숫자를 안전하게 포맷팅 (천단위 구분자 포함)"""
    if value is None or value == 'N/A' or value == '':
        return 'N/A'
    try:
        if isinstance(value, (int, float)):
            return f"{value:,.0f}{suffix}" if isinstance(value, float) and value == int(value) else f"{value:,}{suffix}"
        return str(value)
    except (ValueError, TypeError):
        return str(value) if value else 'N/A'


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
    news_items = news.get("items_for_analysis", news.get("items", []))
    
    # 안전하게 값 추출
    current_price = format_number(current.get('close'), "원")
    change_rate = current.get('change_rate', 'N/A')
    high_52w = format_number(yearly.get('high_price'), "원")
    low_52w = format_number(yearly.get('low_price'), "원")
    total_return = yearly.get('total_return', 'N/A')
    
    ma_current = ma.get('current', {})
    ma5 = format_number(ma_current.get('ma5'), "원")
    ma20 = format_number(ma_current.get('ma20'), "원")
    ma60 = format_number(ma_current.get('ma60'), "원")
    ma120 = format_number(ma_current.get('ma120'), "원")
    
    eps_val = format_number(valuation.get('eps'), "원")
    bps_val = format_number(valuation.get('bps'), "원")
    
    content = f"""## {company_name} ({ticker}) 종합 분석 요청

### 📊 주가 현황
- 현재가: {current_price}
- 등락률: {change_rate}%
- 52주 최고: {high_52w}
- 52주 최저: {low_52w}
- 52주 수익률: {total_return}%

### 📈 이동평균선
- 5일: {ma5}
- 20일: {ma20}
- 60일: {ma60}
- 120일: {ma120}
- 추세: {ma.get('trend', 'N/A')}

### 🔬 기술적 지표
- RSI(14): {rsi.get('value', 'N/A')} ({rsi.get('signal', 'N/A')})
- MFI(14): {mfi.get('value', 'N/A')} ({mfi.get('signal', 'N/A')})

### 💰 밸류에이션
- PER: {valuation.get('per', 'N/A')}배
- PBR: {valuation.get('pbr', 'N/A')}배
- EPS: {eps_val}
- BPS: {bps_val}
- 배당수익률: {valuation.get('div_yield', 'N/A')}%

### 🏢 기업 개요
- 회사명: {company_info.get('corp_name', company_name)}
- 대표자: {company_info.get('ceo_nm', 'N/A')}
- 업종: {company_info.get('induty_name', company_info.get('induty_code', 'N/A'))}
- 설립일: {company_info.get('est_dt', 'N/A')}
- 상장일: {company_info.get('stock_lst_dt', 'N/A')}
- 홈페이지: {company_info.get('hm_url', 'N/A')}

### 📋 재무지표
"""
    
    # 재무지표 추가
    for category, items in financial_index.items():
        if items:
            content += f"\n[{category}]\n"
            # items가 리스트인 경우와 딕셔너리인 경우 모두 처리
            if isinstance(items, list):
                for item in items[:5]:  # 각 카테고리 최대 5개
                    idx_name = item.get('idx_nm', '')
                    idx_val = item.get('idx_val', '')
                    content += f"- {idx_name}: {idx_val}\n"
            elif isinstance(items, dict):
                # 딕셔너리인 경우 key-value 형태로 출력
                for key, val in list(items.items())[:5]:
                    content += f"- {key}: {val}\n"
    
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

