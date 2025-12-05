"""
OpenAI GPT-4o 기업 분석 서비스

기능:
- 기업 종합 분석 (JSON 구조화 응답)
- 재무제표 분석
- 뉴스 감성 분석
- 공시 요약
- 투자 보고서 생성
"""

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from dotenv import load_dotenv

from openai import OpenAI

# 환경 변수 로드
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(env_path)

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 기본 모델 설정
DEFAULT_MODEL = "gpt-4o"


# ============================================
# 응답 데이터 구조 정의
# ============================================

@dataclass
class NewsSentiment:
    """뉴스 감성 평가"""
    title: str              # 뉴스 제목
    score: int              # 감성 점수 (0~100)
    sentiment: str          # 긍정/부정/중립
    summary: str            # 요약 (3문장 이내)


@dataclass
class AnalysisReport:
    """기업 분석 보고서 구조"""
    company_name: str                       # 기업명
    ticker: str                             # 종목코드
    
    # 핵심 지표
    fair_price: int                         # 적정주가
    fair_price_reason: str                  # 적정주가 산출 근거
    investment_score: int                   # 투자 점수 (0~100)
    
    # 뉴스 감성 평가 (3개)
    news_sentiments: List[Dict]             # NewsSentiment 리스트
    
    # 평가 요약
    evaluation_summary: str                 # 평가 요약 (5문장 이내)
    
    # 상세 평가
    detail_key_list: List[str]              # 상세 평가 키 리스트
    detail_evaluations: Dict[str, str]      # 키별 상세 내용
    
    # 메타
    generated_at: str = ""                  # 생성 시각
    model: str = DEFAULT_MODEL              # 사용 모델
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


# ============================================
# 기본 채팅 완성 함수
# ============================================

def chat_completion(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    response_format: str = None
) -> Optional[str]:
    """
    GPT-4o 채팅 완성 API 호출
    
    Args:
        messages: 대화 메시지 리스트
        model: 사용할 모델
        temperature: 창의성 (0~1)
        max_tokens: 최대 응답 토큰
        response_format: 응답 형식 ("json_object" 또는 None)
        
    Returns:
        응답 텍스트
    """
    try:
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # JSON 모드 설정
        if response_format == "json_object":
            kwargs["response_format"] = {"type": "json_object"}
        
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return None


def chat_completion_json(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.5,
    max_tokens: int = 3000
) -> Optional[Dict]:
    """
    GPT-4o JSON 응답 API 호출
    
    Returns:
        파싱된 JSON 딕셔너리
    """
    response = chat_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format="json_object"
    )
    
    if response:
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            return None
    return None


# ============================================
# 구조화된 기업 분석 함수
# ============================================

def generate_analysis_report(
    company_name: str,
    ticker: str,
    current_price: int,
    stock_data: Dict[str, Any],
    valuation_data: Dict[str, Any] = None,
    technical_data: Dict[str, Any] = None,
    financial_data: Dict[str, Any] = None,
    news_list: List[Dict] = None,
    disclosure_list: List[Dict] = None
) -> Optional[Dict]:
    """
    기업 종합 분석 보고서 생성 (JSON 구조화)
    
    Args:
        company_name: 기업명
        ticker: 종목코드
        current_price: 현재 주가
        stock_data: 주가 데이터
        valuation_data: 밸류에이션 (PER, PBR 등)
        technical_data: 기술적 지표 (RSI, MFI)
        financial_data: 재무 데이터
        news_list: 뉴스 리스트
        disclosure_list: 공시 리스트
        
    Returns:
        구조화된 분석 보고서 딕셔너리
    """
    
    system_prompt = """당신은 KORA AI의 전문 증권 애널리스트입니다.
주어진 데이터를 분석하여 반드시 아래 JSON 형식으로만 응답해주세요.
다른 텍스트 없이 JSON만 출력하세요.

응답 JSON 구조:
{
    "fair_price": 적정주가(숫자),
    "fair_price_reason": "적정주가 산출 근거 (2문장)",
    "investment_score": 투자점수(0~100 사이 정수),
    "news_sentiments": [
        {
            "title": "뉴스 제목 또는 주제",
            "score": 감성점수(0~100),
            "sentiment": "긍정/부정/중립",
            "summary": "요약 (3문장 이내)"
        }
    ],
    "evaluation_summary": "종합 평가 요약 (5문장 이내)",
    "detail_key_list": ["재무건전성", "성장성", "수익성", "시장평가", "기술적분석"],
    "detail_evaluations": {
        "재무건전성": "상세 분석 내용",
        "성장성": "상세 분석 내용",
        "수익성": "상세 분석 내용",
        "시장평가": "상세 분석 내용",
        "기술적분석": "상세 분석 내용"
    }
}

점수 기준:
- 투자점수: 80+ 매수추천, 60~79 관망, 40~59 주의, 40미만 매도고려
- 뉴스감성: 70+ 긍정, 40~69 중립, 40미만 부정
- 적정주가: PER, PBR, 성장성 등을 종합하여 산출"""

    # 뉴스 데이터 포맷
    news_text = "뉴스 없음"
    if news_list and len(news_list) > 0:
        news_items = []
        for n in news_list[:5]:
            title = n.get('title', n.get('clean_title', ''))
            desc = n.get('description', n.get('clean_description', ''))
            news_items.append(f"- {title}: {desc[:100]}")
        news_text = "\n".join(news_items)

    user_content = f"""## {company_name} ({ticker}) 분석 요청

### 현재 주가
{current_price:,}원

### 주가 데이터
{_format_dict(stock_data)}

### 밸류에이션 지표
{_format_dict(valuation_data) if valuation_data else "데이터 없음"}

### 기술적 지표
{_format_dict(technical_data) if technical_data else "데이터 없음"}

### 재무 데이터
{_format_dict(financial_data) if financial_data else "데이터 없음"}

### 최근 뉴스
{news_text}

### 최근 공시
{_format_disclosures(disclosure_list) if disclosure_list else "공시 없음"}

위 데이터를 분석하여 JSON 형식으로 응답해주세요."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    result = chat_completion_json(messages, temperature=0.4, max_tokens=2500)
    
    if result:
        # 메타 정보 추가
        from datetime import datetime
        result['company_name'] = company_name
        result['ticker'] = ticker
        result['current_price'] = current_price
        result['generated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result['model'] = DEFAULT_MODEL
    
    return result


def analyze_news_sentiment_json(
    company_name: str,
    news_list: List[Dict]
) -> Optional[Dict]:
    """
    뉴스 감성 분석 (JSON 구조화)
    
    Returns:
        {
            "overall_score": 전체 감성 점수,
            "overall_sentiment": "긍정/부정/중립",
            "news_sentiments": [...],
            "key_topics": ["토픽1", "토픽2", ...],
            "investment_implications": "투자 시사점"
        }
    """
    if not news_list:
        return {"error": "분석할 뉴스가 없습니다."}
    
    system_prompt = """뉴스 감성 분석 전문가입니다.
주어진 뉴스들을 분석하여 반드시 아래 JSON 형식으로만 응답하세요.

{
    "overall_score": 전체감성점수(0~100),
    "overall_sentiment": "긍정/부정/중립",
    "news_sentiments": [
        {
            "title": "뉴스 제목",
            "score": 점수(0~100),
            "sentiment": "긍정/부정/중립",
            "summary": "핵심 요약 (1문장)"
        }
    ],
    "key_topics": ["주요토픽1", "주요토픽2", "주요토픽3"],
    "investment_implications": "투자 시사점 (2문장)"
}"""

    news_text = "\n".join([
        f"- {n.get('title', n.get('clean_title', ''))}: {n.get('description', '')[:100]}"
        for n in news_list[:10]
    ])

    user_content = f"""## {company_name} 뉴스 감성 분석

### 뉴스 목록 ({len(news_list)}건)
{news_text}

위 뉴스들의 감성을 분석하여 JSON으로 응답해주세요."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    return chat_completion_json(messages, temperature=0.3, max_tokens=1500)


def calculate_fair_price_json(
    company_name: str,
    current_price: int,
    valuation: Dict[str, Any],
    financials: Dict[str, Any] = None
) -> Optional[Dict]:
    """
    적정주가 산출 (JSON 구조화)
    
    Returns:
        {
            "fair_price": 적정주가,
            "upside_potential": 상승여력(%),
            "valuation_method": "산출 방식",
            "calculation_detail": "계산 상세",
            "confidence": "높음/중간/낮음"
        }
    """
    system_prompt = """증권 밸류에이션 전문가입니다.
주어진 재무 데이터로 적정주가를 산출하여 JSON으로 응답하세요.

{
    "fair_price": 적정주가(숫자),
    "upside_potential": 상승여력(숫자, %),
    "valuation_method": "사용한 밸류에이션 방식",
    "calculation_detail": "계산 근거 설명 (3문장)",
    "confidence": "높음/중간/낮음",
    "price_range": {
        "low": 하단가,
        "mid": 중간가,
        "high": 상단가
    }
}"""

    user_content = f"""## {company_name} 적정주가 산출

### 현재 주가
{current_price:,}원

### 밸류에이션 지표
{_format_dict(valuation)}

### 재무 데이터
{_format_dict(financials) if financials else "데이터 없음"}

적정주가를 산출하여 JSON으로 응답해주세요."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    return chat_completion_json(messages, temperature=0.3, max_tokens=800)


# ============================================
# 기존 텍스트 기반 함수들 (하위 호환)
# ============================================

def analyze_company(
    company_name: str,
    stock_data: Dict[str, Any],
    financial_data: Dict[str, Any] = None,
    news_data: List[Dict] = None
) -> Optional[str]:
    """기업 종합 분석 (텍스트 응답) - 하위 호환용"""
    system_prompt = """당신은 전문 증권 애널리스트입니다. 
주어진 데이터를 바탕으로 객관적이고 전문적인 기업 분석을 작성해주세요."""

    user_content = f"""## {company_name} 분석 요청
### 주가 데이터
{_format_dict(stock_data)}
### 재무 데이터
{_format_dict(financial_data) if financial_data else "없음"}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    return chat_completion(messages, temperature=0.5, max_tokens=2000)


def analyze_financials(
    company_name: str,
    financial_statements: Dict[str, Any],
    valuation: Dict[str, Any] = None
) -> Optional[str]:
    """재무제표 분석 (텍스트 응답)"""
    system_prompt = """재무 분석 전문가입니다. 재무제표를 분석해주세요."""

    user_content = f"""## {company_name} 재무 분석
{_format_dict(financial_statements)}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    return chat_completion(messages, temperature=0.3, max_tokens=1500)


def analyze_news_sentiment(
    company_name: str,
    news_list: List[Dict[str, str]]
) -> Optional[str]:
    """뉴스 감성 분석 (텍스트 응답)"""
    return str(analyze_news_sentiment_json(company_name, news_list))


def summarize_disclosure(
    company_name: str,
    disclosure_title: str,
    disclosure_content: str
) -> Optional[str]:
    """공시 요약 (텍스트 응답)"""
    system_prompt = """공시 분석 전문가입니다. 공시 내용을 요약해주세요."""

    user_content = f"""## {company_name} - {disclosure_title}
{disclosure_content[:2000]}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    return chat_completion(messages, temperature=0.3, max_tokens=800)


def generate_investment_report(
    company_name: str,
    ticker: str,
    all_data: Dict[str, Any]
) -> Optional[str]:
    """종합 투자 보고서 (텍스트 응답) - 하위 호환용"""
    # JSON 버전 호출 후 텍스트 변환
    result = generate_analysis_report(
        company_name=company_name,
        ticker=ticker,
        current_price=all_data.get('stock', {}).get('current_price', 0),
        stock_data=all_data.get('stock', {}),
        valuation_data=all_data.get('valuation', {}),
        technical_data=all_data.get('technical', {}),
        news_list=all_data.get('news', [])
    )
    
    if result:
        return json.dumps(result, ensure_ascii=False, indent=2)
    return None


# ============================================
# 유틸리티 함수
# ============================================

def _format_dict(data: Dict) -> str:
    """딕셔너리를 보기 좋게 포맷"""
    if not data:
        return "데이터 없음"
    
    lines = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"- {key}:")
            for k, v in value.items():
                lines.append(f"  - {k}: {v}")
        elif isinstance(value, list):
            lines.append(f"- {key}: {len(value)}개 항목")
        else:
            lines.append(f"- {key}: {value}")
    
    return "\n".join(lines)


def _format_disclosures(disclosures: List[Dict]) -> str:
    """공시 리스트 포맷"""
    if not disclosures:
        return "공시 없음"
    
    lines = []
    for i, disc in enumerate(disclosures[:5], 1):
        title = disc.get('report_nm', disc.get('title', ''))
        date = disc.get('rcept_dt', disc.get('date', ''))
        lines.append(f"{i}. [{date}] {title}")
    
    return "\n".join(lines)


# ============================================
# 테스트
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("GPT-4o 분석 서비스 테스트 (JSON 구조화)")
    print("=" * 60)
    
    # 테스트 데이터
    test_stock = {
        "current_price": 80050,
        "change_rate": 1.72,
        "high_52w": 83900,
        "low_52w": 42500,
        "ma5": 79950,
        "ma20": 78617,
        "ma60": 73929
    }
    
    test_valuation = {
        "per": 9.48,
        "pbr": 0.71,
        "div_yield": 2.7,
        "eps": 8441,
        "bps": 112364
    }
    
    test_technical = {
        "rsi": {"value": 56.49, "signal": "강세"},
        "mfi": {"value": 58.9, "signal": "자금 유입"}
    }
    
    test_news = [
        {"title": "신한금융, 3분기 순이익 1조원 돌파", "description": "신한금융지주가 3분기 순이익 1조원을 달성했다."},
        {"title": "신한은행, 디지털 혁신 가속화", "description": "신한은행이 AI 기반 서비스를 확대한다."},
        {"title": "금융지주 배당 확대 기대", "description": "금융지주사들의 배당 확대가 예상된다."}
    ]
    
    print("\n[1] API 연결 테스트")
    simple_test = chat_completion([
        {"role": "user", "content": "안녕하세요. 테스트입니다. '연결 성공'이라고만 답해주세요."}
    ], max_tokens=50)
    
    if simple_test:
        print(f"✅ API 연결 성공: {simple_test}")
    else:
        print("❌ API 연결 실패")
        exit()
    
    print("\n[2] 종합 분석 보고서 테스트 (JSON)")
    print("신한금융지주 분석 중...")
    
    report = generate_analysis_report(
        company_name="신한금융지주",
        ticker="055550",
        current_price=80050,
        stock_data=test_stock,
        valuation_data=test_valuation,
        technical_data=test_technical,
        news_list=test_news
    )
    
    if report:
        print("\n✅ 분석 완료!")
        print("-" * 60)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print("-" * 60)
        
        # 주요 필드 출력
        print(f"\n📊 적정주가: {report.get('fair_price', 'N/A'):,}원")
        print(f"📈 투자점수: {report.get('investment_score', 'N/A')}점")
        print(f"📝 평가요약: {report.get('evaluation_summary', 'N/A')[:100]}...")
        
        print(f"\n🔑 상세평가 항목: {report.get('detail_key_list', [])}")
    else:
        print("❌ 분석 실패")
