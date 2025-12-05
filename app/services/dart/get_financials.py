# get_financials.py
# 단일회사 전체 재무제표 조회

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(env_path)

# DART API KEY
API_KEY = os.getenv("DART_API_KEY")

# 단일회사 전체 재무제표 API URL
URL = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"

# DART 조회 함수 정의
def fetch_financials(corp_code, year, report_code, fs_div):
    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code,
        "bsns_year": year,
        "reprt_code": report_code,
        "fs_div": fs_div
    }

    res = requests.get(URL, params=params)
    data = res.json()

    # status 값이 000이면 정상
    if data.get("status") == "000":
        return data.get("list", [])
    return None

# 자동 CFS 우선 조회 함수
def fetch_financials_auto(corp_code, year, report_code):
    # 연결 CFS 우선 조회
    rows = fetch_financials(corp_code, year, report_code, "CFS")
    if rows:
        return rows, "CFS"

    # 없으면 개별 OFS 조회
    rows = fetch_financials(corp_code, year, report_code, "OFS")
    if rows:
        return rows, "OFS"

    return None, None

if __name__ == "__main__":
    # 신한금융지주 고유번호
    corp_code = "00382199"
    year = "2023"
    report_code = "11011"  # 사업보고서

    print("신한금융지주 2023년 사업보고서 재무제표 조회 시작")

    rows, used_type = fetch_financials_auto(corp_code, year, report_code)

    if rows is None:
        print("조회 실패 또는 데이터 없음")
    else:
        print("조회 성공")
        print("사용된 재무 기준", used_type)
        print("총 라인 수", len(rows))
        print("일부 데이터 출력")

        for row in rows[:10]:
            print(row)
