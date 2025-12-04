# get_dart_regular_reports.py
# 정기공시(A) 최신 보고서 조회 최종버전

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("../.env")
API_KEY = os.getenv("DART_API_KEY")

URL = "https://opendart.fss.or.kr/api/list.json"


def get_regular_reports(corp_code, start="20200101", end=None):
    if not end:
        end = datetime.today().strftime("%Y%m%d")

    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code,
        "bgn_de": start,
        "end_de": end,
        "pblntf_ty": "A",        # 정기공시
        "last_reprt_at": "Y",    # 최종정정본만
        "page_no": 1,
        "page_count": 100
    }

    r = requests.get(URL, params=params)
    data = r.json()

    if data.get("status") != "000":
        print("DART 오류:", data.get("message"))
        return []

    return data.get("list", [])


def get_latest_regular_report(corp_code):
    reports = get_regular_reports(corp_code)
    if not reports:
        return None

    reports.sort(key=lambda x: x["rcept_dt"], reverse=True)
    return reports[0]


if __name__ == "__main__":
    corp_code = "00126380"  # 삼성전자
    latest = get_latest_regular_report(corp_code)

    if latest:
        print(latest)
    else:
        print("정기보고서 없음")
