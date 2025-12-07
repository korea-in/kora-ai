# get_stock_info.py
# 주식의 총수 현황 조회

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드
env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(env_path)

# DART API KEY
API_KEY = os.getenv("DART_API_KEY")

# 주식의 총수 현황 API URL
URL = "https://opendart.fss.or.kr/api/stockTotqySttus.json"


def get_stock_total_qty(corp_code: str, bsns_year: str = None, reprt_code: str = "11011") -> dict:
    """
    주식의 총수 현황 조회
    
    Args:
        corp_code: 고유번호 (8자리)
        bsns_year: 사업연도 (기본값: 현재년도-1)
        reprt_code: 보고서 코드 (11011: 사업보고서, 11012: 반기, 11013: 1분기, 11014: 3분기)
    
    Returns:
        주식 총수 정보 딕셔너리
        {
            'total_shares': 발행주식총수,
            'common_shares': 보통주,
            'preferred_shares': 우선주,
            'raw_data': 원본 데이터
        }
    """
    from datetime import datetime
    
    if not bsns_year:
        bsns_year = str(datetime.now().year - 1)
    
    params = {
        "crtfc_key": API_KEY,
        "corp_code": corp_code,
        "bsns_year": bsns_year,
        "reprt_code": reprt_code
    }
    
    print(f"[DART] 주식총수 조회: corp_code={corp_code}, year={bsns_year}, reprt_code={reprt_code}")
    
    try:
        res = requests.get(URL, params=params, timeout=10)
        data = res.json()
        
        if data.get("status") == "000":
            items = data.get("list", [])
            print(f"[DART] 주식총수 조회 성공: {len(items)}개 항목")
            
            result = {
                'total_shares': None,
                'common_shares': None,
                'preferred_shares': None,
                'raw_data': items
            }
            
            for item in items:
                se = item.get("se", "")  # 구분
                istc_totqy = item.get("istc_totqy", "")  # 발행주식의 총수
                
                # 숫자로 변환
                def parse_number(val):
                    if not val or val == '-':
                        return None
                    try:
                        return int(str(val).replace(',', ''))
                    except:
                        return None
                
                shares = parse_number(istc_totqy)
                
                print(f"[DART] 주식항목: {se} = {istc_totqy} → {shares}")
                
                # 발행주식총수 찾기
                if '합계' in se or '발행주식총수' in se:
                    if shares:
                        result['total_shares'] = shares
                elif '보통주' in se:
                    if shares:
                        result['common_shares'] = shares
                elif '우선주' in se:
                    if shares:
                        result['preferred_shares'] = shares
            
            # 합계가 없으면 보통주 + 우선주로 계산
            if result['total_shares'] is None:
                common = result['common_shares'] or 0
                preferred = result['preferred_shares'] or 0
                if common > 0:
                    result['total_shares'] = common + preferred
                    print(f"[DART] 주식총수 계산: {common} + {preferred} = {result['total_shares']}")
            
            print(f"[DART] 최종 발행주식총수: {result['total_shares']}")
            return result
            
        else:
            print(f"[DART] 주식총수 조회 실패: {data.get('message')}")
            
            # 이전 연도로 재시도
            if bsns_year == str(datetime.now().year - 1):
                print(f"[DART] 이전 연도({int(bsns_year) - 1})로 재시도...")
                return get_stock_total_qty(corp_code, str(int(bsns_year) - 1), reprt_code)
            
            return None
            
    except Exception as e:
        print(f"[DART] 주식총수 조회 오류: {e}")
        return None


if __name__ == "__main__":
    # 삼성전자 테스트
    corp_code = "00126380"
    
    print("삼성전자 주식총수 조회")
    print("-" * 50)
    
    result = get_stock_total_qty(corp_code)
    
    if result:
        print(f"\n발행주식총수: {result['total_shares']:,}주")
        print(f"보통주: {result['common_shares']:,}주" if result['common_shares'] else "보통주: -")
        print(f"우선주: {result['preferred_shares']:,}주" if result['preferred_shares'] else "우선주: -")
    else:
        print("주식총수 조회 실패")
