"""
Company 관련 모델
Firestore popular 컬렉션 데이터 구조 정의
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class PopularCompany:
    """
    인기 기업 모델
    
    Firestore Collection: popular
    Document ID: {market}_{company_code}
    """
    
    # 필수 필드
    market: str                           # 시장 (kospi/kosdaq)
    company_code: str                     # 기업 코드
    company_name: str                     # 기업명
    
    # 통계
    view_count: int = 0                   # 조회수
    search_count: int = 0                 # 검색 횟수
    analysis_count: int = 0               # 분석 요청 횟수
    
    # 타임스탬프
    created_at: Optional[datetime] = None
    last_viewed: Optional[datetime] = None
    
    # 문서 ID
    doc_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Firestore 저장용 딕셔너리 변환"""
        return {
            'market': self.market,
            'company_code': self.company_code,
            'company_name': self.company_name,
            'view_count': self.view_count,
            'search_count': self.search_count,
            'analysis_count': self.analysis_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], doc_id: Optional[str] = None) -> 'PopularCompany':
        """Firestore 문서에서 PopularCompany 객체 생성"""
        return cls(
            market=data.get('market', 'kospi'),
            company_code=data.get('company_code', ''),
            company_name=data.get('company_name', ''),
            view_count=data.get('view_count', 0),
            search_count=data.get('search_count', 0),
            analysis_count=data.get('analysis_count', 0),
            created_at=data.get('created_at'),
            last_viewed=data.get('last_viewed'),
            doc_id=doc_id,
        )
    
    @classmethod
    def create_new(cls, market: str, company_code: str, company_name: str) -> 'PopularCompany':
        """새 인기 기업 생성용 팩토리 메서드"""
        return cls(
            market=market,
            company_code=company_code,
            company_name=company_name,
            view_count=1,
        )
    
    @staticmethod
    def generate_doc_id(market: str, company_code: str) -> str:
        """문서 ID 생성"""
        return f"{market}_{company_code}"
    
    def format_view_count(self) -> str:
        """조회수 포맷팅 (1000 이상은 K로 표시)"""
        if self.view_count >= 1000:
            return f"{self.view_count / 1000:.1f}K"
        return str(self.view_count)
    
    def __repr__(self) -> str:
        return f"PopularCompany(market={self.market}, code={self.company_code}, views={self.view_count})"

