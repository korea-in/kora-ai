# get_financial_index.py
# 단일회사 주요계정 지표 조회

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(env_path)

# DART API KEY
API_KEY = os.getenv("DART_API_KEY")

# 단일회사 주요계정 지표 API URL
URL = "https://opendart.fss.or.kr/api/fnlttSinglIndx.json"


def fetch_financial_index(corp_code, bsns_year, reprt_code, idx_cl_code):
    """
    단일회사 주요계정 지표 조회
    
    Parameters:
        corp_code: 고유번호 (8자리)
        bsns_year: 사업연도 (예: "2024")
        reprt_code: 보고서 코드
            - 11013: 1분기보고서
            - 11012: 반기보고서
            - 11014: 3분기보고서
            - 11011: 사업보고서
        idx_cl_code: 지표분류코드
            - M210000: 수익성지표
            - M220000: 안정성지표
            - M230000: 성장성지표
            - M240000: 활동성지표
    
    Returns:
        주요계정 지표 리스트
    """
    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code,
        "bsns_year": bsns_year,
        "reprt_code": reprt_code,
        "idx_cl_code": idx_cl_code
    }

    res = requests.get(URL, params=params)
    data = res.json()

    if data.get("status") == "000":
        return data.get("list", [])
    else:
        print("DART 오류:", data.get("message"))
        return None


def fetch_all_financial_index(corp_code, bsns_year, reprt_code):
    """
    모든 분류의 주요계정 지표 조회
    
    Parameters:
        corp_code: 고유번호 (8자리)
        bsns_year: 사업연도 (예: "2024")
        reprt_code: 보고서 코드
    
    Returns:
        분류별 주요계정 지표 딕셔너리
    """
    index_codes = {
        "M210000": "수익성지표",
        "M220000": "안정성지표",
        "M230000": "성장성지표",
        "M240000": "활동성지표"
    }
    
    result = {}
    
    for code, name in index_codes.items():
        data = fetch_financial_index(corp_code, bsns_year, reprt_code, code)
        if data:
            result[name] = data
    
    return result


def fetch_latest_financial_index(corp_code, year="2024"):
    """
    최신 주요계정 지표 조회 (사업보고서 기준)
    """
    return fetch_all_financial_index(corp_code, year, "11011")


if __name__ == "__main__":
    # 신한금융지주 고유번호
    corp_code = "00382199"
    year = "2023"
    
    print(f"신한금융지주 {year}년 주요계정 지표 조회")
    print("=" * 60)
    
    # 전체 지표 조회
    all_index = fetch_latest_financial_index(corp_code, year)
    
    if all_index:
        for category, items in all_index.items():
            print(f"\n[{category}]")
            print("-" * 50)
            if items:
                for item in items:
                    print(f"지표명: {item.get('idx_nm')}")
                    print(f"당기: {item.get('idx_val')}")
                    print("-" * 30)
            else:
                print("데이터 없음")
    else:
        print("주요계정 지표 조회 실패")
    
    # 개별 지표 조회 예시
    print("\n" + "=" * 60)
    print("수익성지표만 조회")
    print("=" * 60)
    
    profitability = fetch_financial_index(corp_code, year, "11011", "M210000")
    if profitability:
        for item in profitability:
            print(f"{item.get('idx_nm')}: {item.get('idx_val')}")

