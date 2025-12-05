"""
DART 전자공시 API 서비스
https://opendart.fss.or.kr/

TODO: 구현 예정
- 기업 공시 조회
- 재무제표 조회
- 사업보고서 조회

사용법:
1. DART OpenAPI에서 API 키 발급
2. .env 파일에 설정:
   DART_API_KEY=your_api_key
"""

import os
from typing import Dict, Any


# API 설정
DART_API_URL = "https://opendart.fss.or.kr/api"


def _get_api_key() -> str:
    """DART API 키 조회"""
    return os.environ.get('DART_API_KEY', '')


def _is_configured() -> bool:
    """API 설정 여부 확인"""
    return bool(_get_api_key())


def check_api_status() -> Dict[str, Any]:
    """API 상태 확인"""
    return {
        "configured": _is_configured(),
        "api_key_set": bool(_get_api_key())
    }


# TODO: 아래 함수들 구현 예정

def get_company_disclosure(corp_code: str):
    """기업 공시 조회"""
    pass


def get_financial_statements(corp_code: str, year: str):
    """재무제표 조회"""
    pass


def get_business_report(corp_code: str, year: str):
    """사업보고서 조회"""
    pass

