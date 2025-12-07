"""
업종 코드 → 업종명 매핑 유틸리티
"""
import os
import csv
from typing import Optional, Dict

# 업종 코드 캐시
_industry_cache: Dict[str, str] = {}
_cache_loaded = False

def load_industry_codes():
    """CSV 파일에서 업종 코드를 로드"""
    global _industry_cache, _cache_loaded
    
    if _cache_loaded:
        return
    
    try:
        csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'Industry', 'Industry_code.csv')
        csv_path = os.path.abspath(csv_path)
        
        if not os.path.exists(csv_path):
            print(f"[IndustryMapper] CSV 파일 없음: {csv_path}")
            _cache_loaded = True
            return
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            
            # 헤더 스킵 (처음 6줄)
            for _ in range(6):
                next(reader, None)
            
            for row in reader:
                if len(row) >= 11:
                    code = row[1].strip()  # 업종코드 (2번째 컬럼)
                    name = row[10].strip()  # 세세분류명 (11번째 컬럼)
                    
                    if code and name and code not in _industry_cache:
                        _industry_cache[code] = name
        
        print(f"[IndustryMapper] {len(_industry_cache)}개 업종 코드 로드 완료")
        _cache_loaded = True
        
    except Exception as e:
        print(f"[IndustryMapper] 로드 오류: {e}")
        _cache_loaded = True


def get_industry_name(code: str) -> Optional[str]:
    """
    업종 코드로 업종명 조회
    
    Args:
        code: 업종 코드 (예: "659906", "641100")
        
    Returns:
        업종명 또는 None
    """
    if not code:
        return None
    
    load_industry_codes()
    
    # 정확히 일치하는 코드 찾기
    code = str(code).strip()
    
    if code in _industry_cache:
        return _industry_cache[code]
    
    # 6자리 코드로 패딩 후 검색
    if len(code) < 6:
        padded = code.ljust(6, '0')
        if padded in _industry_cache:
            return _industry_cache[padded]
    
    # 앞부분 일치로 검색 (더 넓은 카테고리)
    for cached_code, name in _industry_cache.items():
        if cached_code.startswith(code):
            return name
    
    return None


def get_industry_with_code(code: str) -> str:
    """
    업종 코드와 업종명을 함께 반환
    
    Args:
        code: 업종 코드
        
    Returns:
        "업종명 (코드)" 형식 또는 코드만
    """
    if not code:
        return "-"
    
    name = get_industry_name(code)
    
    if name:
        return name
    
    return str(code)


# 주요 업종 코드 빠른 매핑 (자주 사용되는 업종)
COMMON_INDUSTRIES = {
    "641100": "중앙은행",
    "659201": "국내은행",
    "659906": "지주회사",
    "660100": "생명보험업",
    "660201": "손해보험업",
    "661101": "증권 중개업",
    "321104": "반도체 제조업",
    "322001": "전자부품 제조업",
    "311101": "자동차 제조업",
    "241100": "의약품 제조업",
    "721001": "컴퓨터 프로그래밍 서비스업",
    "642001": "무선 및 위성 통신업",
    "642005": "유선 통신업",
}


def get_industry_fast(code: str) -> str:
    """빠른 업종명 조회 (공통 업종 우선)"""
    if not code:
        return "-"
    
    code = str(code).strip()
    
    # 공통 업종에서 먼저 검색
    if code in COMMON_INDUSTRIES:
        return COMMON_INDUSTRIES[code]
    
    # CSV에서 검색
    name = get_industry_name(code)
    return name if name else code
