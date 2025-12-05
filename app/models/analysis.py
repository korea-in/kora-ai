"""
AnalysisHistory 모델
Firestore analysis_history 컬렉션 데이터 구조 정의
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class AnalysisHistory:
    """
    분석 기록 모델
    
    Firestore Collection: analysis_history
    Document ID: 자동 생성
    """
    
    # 필수 필드
    user_id: str                          # 사용자 UID
    company_code: str                     # 기업 코드
    company_name: str                     # 기업명
    market: str                           # 시장 (kospi/kosdaq)
    
    # 분석 정보
    request_type: str                     # 요청 유형 (재무분석, 리스크분석 등)
    request_text: str = ""                # 실제 요청 텍스트
    
    # 결과
    result_summary: str = ""              # 분석 결과 요약
    result_full: Optional[Dict] = None    # 전체 분석 결과 (JSON)
    
    # 메타데이터
    analysis_duration_ms: int = 0         # 분석 소요 시간 (밀리초)
    tokens_used: int = 0                  # 사용된 토큰 수 (AI 분석 시)
    data_sources: List[str] = field(default_factory=list)  # 사용된 데이터 소스
    
    # 상태
    status: str = "completed"             # pending, processing, completed, failed
    error_message: Optional[str] = None   # 오류 발생 시 메시지
    
    # 타임스탬프
    created_at: Optional[datetime] = None
    
    # 문서 ID (Firestore에서 조회 후 설정)
    doc_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Firestore 저장용 딕셔너리 변환"""
        return {
            'user_id': self.user_id,
            'company_code': self.company_code,
            'company_name': self.company_name,
            'market': self.market,
            'request_type': self.request_type,
            'request_text': self.request_text,
            'result_summary': self.result_summary,
            'result_full': self.result_full,
            'analysis_duration_ms': self.analysis_duration_ms,
            'tokens_used': self.tokens_used,
            'data_sources': self.data_sources,
            'status': self.status,
            'error_message': self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], doc_id: Optional[str] = None) -> 'AnalysisHistory':
        """Firestore 문서에서 AnalysisHistory 객체 생성"""
        return cls(
            user_id=data.get('user_id', ''),
            company_code=data.get('company_code', ''),
            company_name=data.get('company_name', ''),
            market=data.get('market', 'kospi'),
            request_type=data.get('request_type', ''),
            request_text=data.get('request_text', ''),
            result_summary=data.get('result_summary', ''),
            result_full=data.get('result_full'),
            analysis_duration_ms=data.get('analysis_duration_ms', 0),
            tokens_used=data.get('tokens_used', 0),
            data_sources=data.get('data_sources', []),
            status=data.get('status', 'completed'),
            error_message=data.get('error_message'),
            created_at=data.get('created_at'),
            doc_id=doc_id,
        )
    
    @classmethod
    def create_new(
        cls,
        user_id: str,
        company_code: str,
        company_name: str,
        market: str,
        request_type: str,
        request_text: str = ""
    ) -> 'AnalysisHistory':
        """새 분석 기록 생성용 팩토리 메서드"""
        return cls(
            user_id=user_id,
            company_code=company_code,
            company_name=company_name,
            market=market,
            request_type=request_type,
            request_text=request_text,
            status="pending"
        )
    
    def __repr__(self) -> str:
        return f"AnalysisHistory(company={self.company_name}, type={self.request_type}, status={self.status})"

