# get_company.py
# 기업 개황 정보 조회

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(env_path)

# DART API KEY
API_KEY = os.getenv("DART_API_KEY")

# 기업 개황 API URL
URL = "https://opendart.fss.or.kr/api/company.json"


def get_company_info(corp_code):
    """
    기업 개황 정보 조회
    - 정식명칭, 영문명칭, 대표자명, 법인구분, 법인등록번호
    - 사업자등록번호, 주소, 홈페이지, IR홈페이지
    - 전화번호, 팩스번호, 업종코드, 설립일, 결산월 등
    """
    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code
    }

    res = requests.get(URL, params=params)
    data = res.json()

    if data.get("status") == "000":
        return data
    else:
        print("DART 오류:", data.get("message"))
        return None


if __name__ == "__main__":
    # 삼성전자 고유번호
    corp_code = "00126380"
    
    print("삼성전자 기업 개황 조회")
    print("-" * 50)
    
    info = get_company_info(corp_code)
    
    if info:
        print(f"회사명: {info.get('corp_name')}")
        print(f"영문명: {info.get('corp_name_eng')}")
        print(f"대표자: {info.get('ceo_nm')}")
        print(f"법인구분: {info.get('corp_cls')}")
        print(f"주소: {info.get('adres')}")
        print(f"홈페이지: {info.get('hm_url')}")
        print(f"설립일: {info.get('est_dt')}")
        print(f"결산월: {info.get('acc_mt')}")
    else:
        print("기업 정보 조회 실패")

