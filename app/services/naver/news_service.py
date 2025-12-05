"""
네이버 뉴스 검색 API 서비스
https://developers.naver.com/docs/serviceapi/search/news/news.md

사용법:
1. 네이버 개발자 센터에서 애플리케이션 등록
2. 클라이언트 ID, 시크릿 발급
3. .env 파일에 설정:
   NAVER_CLIENT_ID=your_client_id
   NAVER_CLIENT_SECRET=your_client_secret
"""

import os
import requests
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import quote
import re


# ============================================
# 데이터 클래스
# ============================================

@dataclass
class NaverNewsItem:
    """
    네이버 뉴스 검색 결과 아이템
    """
    title: str                          # 뉴스 제목 (HTML 태그 포함 가능)
    original_link: str                  # 뉴스 기사 원문 URL
    link: str                           # 네이버 뉴스 URL
    description: str                    # 뉴스 내용 요약
    pub_date: Optional[datetime] = None # 기사 발행일
    
    # 추가 정보 (파싱 후 설정)
    clean_title: str = ""               # HTML 태그 제거된 제목
    clean_description: str = ""         # HTML 태그 제거된 요약
    source: str = ""                    # 언론사 (URL에서 추출)
    
    def __post_init__(self):
        """HTML 태그 제거 및 추가 정보 설정"""
        self.clean_title = self._remove_html_tags(self.title)
        self.clean_description = self._remove_html_tags(self.description)
        self.source = self._extract_source(self.original_link)
    
    @staticmethod
    def _remove_html_tags(text: str) -> str:
        """HTML 태그 제거"""
        clean = re.sub(r'<[^>]+>', '', text)
        clean = clean.replace('&quot;', '"')
        clean = clean.replace('&amp;', '&')
        clean = clean.replace('&lt;', '<')
        clean = clean.replace('&gt;', '>')
        clean = clean.replace('&apos;', "'")
        return clean.strip()
    
    @staticmethod
    def _extract_source(url: str) -> str:
        """URL에서 언론사 추출"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            # 주요 언론사 매핑
            sources = {
                'news.naver.com': '네이버뉴스',
                'www.hankyung.com': '한국경제',
                'www.mk.co.kr': '매일경제',
                'www.edaily.co.kr': '이데일리',
                'www.sedaily.com': '서울경제',
                'www.etnews.com': '전자신문',
                'www.dt.co.kr': '디지털타임스',
                'www.fnnews.com': '파이낸셜뉴스',
                'www.mt.co.kr': '머니투데이',
                'biz.chosun.com': '조선비즈',
                'www.hani.co.kr': '한겨레',
                'www.donga.com': '동아일보',
                'www.yonhapnews.co.kr': '연합뉴스',
            }
            return sources.get(domain, domain)
        except Exception:
            return ""
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'title': self.clean_title,
            'original_title': self.title,
            'original_link': self.original_link,
            'link': self.link,
            'description': self.clean_description,
            'original_description': self.description,
            'pub_date': self.pub_date.isoformat() if self.pub_date else None,
            'source': self.source
        }
    
    @classmethod
    def from_api_response(cls, item: Dict) -> 'NaverNewsItem':
        """API 응답에서 객체 생성"""
        pub_date = None
        if 'pubDate' in item:
            try:
                # 네이버 API 날짜 형식: "Mon, 26 Sep 2016 07:50:00 +0900"
                pub_date = datetime.strptime(
                    item['pubDate'], 
                    "%a, %d %b %Y %H:%M:%S %z"
                )
            except Exception:
                pass
        
        return cls(
            title=item.get('title', ''),
            original_link=item.get('originallink', ''),
            link=item.get('link', ''),
            description=item.get('description', ''),
            pub_date=pub_date
        )


@dataclass
class NaverNewsResponse:
    """
    네이버 뉴스 검색 API 응답
    """
    total: int = 0                      # 총 검색 결과 수
    start: int = 1                      # 검색 시작 위치
    display: int = 10                   # 표시된 결과 수
    items: List[NaverNewsItem] = field(default_factory=list)
    
    # 메타 정보
    query: str = ""                     # 검색어
    success: bool = True                # 성공 여부
    error_message: str = ""             # 에러 메시지
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'total': self.total,
            'start': self.start,
            'display': self.display,
            'query': self.query,
            'success': self.success,
            'error_message': self.error_message,
            'items': [item.to_dict() for item in self.items]
        }


# ============================================
# API 설정
# ============================================

NAVER_API_URL = "https://openapi.naver.com/v1/search/news.json"


def _get_credentials() -> tuple:
    """네이버 API 인증 정보 조회"""
    client_id = os.environ.get('NAVER_CLIENT_ID', '')
    client_secret = os.environ.get('NAVER_CLIENT_SECRET', '')
    return client_id, client_secret


def _is_configured() -> bool:
    """API 설정 여부 확인"""
    client_id, client_secret = _get_credentials()
    return bool(client_id and client_secret)


# ============================================
# API 호출 함수
# ============================================

def search_news(
    query: str,
    display: int = 10,
    start: int = 1,
    sort: str = "sim"
) -> NaverNewsResponse:
    """
    네이버 뉴스 검색
    
    Args:
        query: 검색어 (UTF-8 인코딩)
        display: 한 번에 표시할 검색 결과 개수 (기본: 10, 최대: 100)
        start: 검색 시작 위치 (기본: 1, 최대: 1000)
        sort: 정렬 방법 - "sim"(정확도순), "date"(날짜순)
        
    Returns:
        NaverNewsResponse 객체
    """
    # API 설정 확인
    if not _is_configured():
        return NaverNewsResponse(
            success=False,
            error_message="Naver API not configured. Set NAVER_CLIENT_ID and NAVER_CLIENT_SECRET.",
            query=query
        )
    
    client_id, client_secret = _get_credentials()
    
    # 파라미터 검증
    display = max(1, min(100, display))
    start = max(1, min(1000, start))
    sort = sort if sort in ["sim", "date"] else "sim"
    
    # 요청 헤더
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    
    # 요청 파라미터
    params = {
        "query": query,
        "display": display,
        "start": start,
        "sort": sort
    }
    
    try:
        response = requests.get(
            NAVER_API_URL,
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            items = [
                NaverNewsItem.from_api_response(item) 
                for item in data.get('items', [])
            ]
            
            return NaverNewsResponse(
                total=data.get('total', 0),
                start=data.get('start', 1),
                display=data.get('display', len(items)),
                items=items,
                query=query,
                success=True
            )
        else:
            # 에러 응답 처리
            error_data = response.json() if response.content else {}
            error_msg = error_data.get('errorMessage', f"HTTP {response.status_code}")
            
            return NaverNewsResponse(
                success=False,
                error_message=error_msg,
                query=query
            )
            
    except requests.exceptions.Timeout:
        return NaverNewsResponse(
            success=False,
            error_message="Request timeout",
            query=query
        )
    except requests.exceptions.RequestException as e:
        return NaverNewsResponse(
            success=False,
            error_message=str(e),
            query=query
        )
    except Exception as e:
        return NaverNewsResponse(
            success=False,
            error_message=f"Unexpected error: {str(e)}",
            query=query
        )


def search_company_news(
    company_name: str,
    keywords: Optional[List[str]] = None,
    display: int = 10,
    sort: str = "date"
) -> NaverNewsResponse:
    """
    기업 관련 뉴스 검색
    
    Args:
        company_name: 기업명
        keywords: 추가 검색 키워드 (예: ["주가", "실적"])
        display: 표시 개수
        sort: 정렬 방법 (기업 뉴스는 최신순 기본)
        
    Returns:
        NaverNewsResponse 객체
    """
    # 검색어 구성
    query_parts = [company_name]
    
    if keywords:
        # 키워드 OR 검색
        keyword_query = " OR ".join(keywords)
        query_parts.append(f"({keyword_query})")
    
    query = " ".join(query_parts)
    
    return search_news(
        query=query,
        display=display,
        sort=sort
    )


# ============================================
# 유틸리티 함수
# ============================================

def get_stock_related_keywords() -> List[str]:
    """주식 관련 기본 키워드"""
    return [
        "주가", "주식", "실적", "매출", "영업이익",
        "배당", "공시", "투자", "증권", "애널리스트"
    ]


def get_financial_keywords() -> List[str]:
    """재무 관련 키워드"""
    return [
        "재무", "부채", "자산", "현금흐름", "자본",
        "흑자", "적자", "성장률", "수익성"
    ]


def check_api_status() -> Dict[str, Any]:
    """API 상태 확인"""
    configured = _is_configured()
    
    result = {
        "configured": configured,
        "client_id_set": bool(os.environ.get('NAVER_CLIENT_ID')),
        "client_secret_set": bool(os.environ.get('NAVER_CLIENT_SECRET'))
    }
    
    if configured:
        # 테스트 검색 수행
        test_response = search_news("테스트", display=1)
        result["api_working"] = test_response.success
        if not test_response.success:
            result["error"] = test_response.error_message
    
    return result

