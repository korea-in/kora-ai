# get_dividend.py
# 배당에 관한 사항 조회

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(env_path)

# DART API KEY
API_KEY = os.getenv("DART_API_KEY")

# 배당에 관한 사항 API URL
URL = "https://opendart.fss.or.kr/api/alotMatter.json"


def get_dividend_info(corp_code, bsns_year, reprt_code):
    """
    배당에 관한 사항 조회
    
    Parameters:
        corp_code: 고유번호 (8자리)
        bsns_year: 사업연도 (예: "2024")
        reprt_code: 보고서 코드
            - 11013: 1분기보고서
            - 11012: 반기보고서
            - 11014: 3분기보고서
            - 11011: 사업보고서
    
    Returns:
        배당 관련 정보 (주당배당금, 배당수익률, 배당성향 등)
    """
    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code,
        "bsns_year": bsns_year,
        "reprt_code": reprt_code
    }

    res = requests.get(URL, params=params)
    data = res.json()

    if data.get("status") == "000":
        return data.get("list", [])
    else:
        print("DART 오류:", data.get("message"))
        return None


def get_latest_dividend_info(corp_code, year="2024"):
    """
    최신 배당 정보 조회 (사업보고서 기준)
    """
    return get_dividend_info(corp_code, year, "11011")


def get_dividend_history(corp_code, years=None):
    """
    여러 연도의 배당 정보 조회
    
    Parameters:
        corp_code: 고유번호
        years: 조회할 연도 리스트 (기본값: 최근 3년)
    
    Returns:
        연도별 배당 정보 딕셔너리
    """
    if years is None:
        from datetime import datetime
        current_year = datetime.now().year
        years = [str(current_year - i) for i in range(1, 4)]
    
    history = {}
    for year in years:
        info = get_dividend_info(corp_code, year, "11011")
        if info:
            history[year] = info
    
    return history


if __name__ == "__main__":
    # 삼성전자 고유번호
    corp_code = "00126380"
    year = "2023"
    
    print(f"삼성전자 {year}년 배당 정보 조회")
    print("-" * 50)
    
    dividends = get_latest_dividend_info(corp_code, year)
    
    if dividends:
        print(f"총 {len(dividends)}개 항목 조회됨\n")
        for div in dividends:
            print(f"구분: {div.get('se')}")
            print(f"당기: {div.get('thstrm')}")
            print(f"전기: {div.get('frmtrm')}")
            print(f"전전기: {div.get('lwfr')}")
            print("-" * 30)
    else:
        print("배당 정보 조회 실패")
    
    # 연도별 배당 이력 조회
    print("\n" + "=" * 60)
    print("연도별 배당 이력")
    print("=" * 60)
    
    history = get_dividend_history(corp_code, ["2023", "2022", "2021"])
    for year, data in history.items():
        print(f"\n[{year}년]")
        if data:
            for item in data[:3]:  # 주요 항목만
                print(f"  {item.get('se')}: {item.get('thstrm')}")

